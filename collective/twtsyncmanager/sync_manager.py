#!/usr/bin/env python
# -*- coding: utf-8 -*-

#
# Ticket works sync mechanism by Andre Goncalves
#
import plone.api
import transaction

from zope.schema.interfaces import ITextLine, ITuple, IBool
from plone.app.textfield.interfaces import IRichText
from plone.app.textfield.value import RichTextValue
from zope.schema import getFieldsInOrder
from plone.event.interfaces import IEventAccessor
from datetime import datetime

from collective.behavior.performance.behavior import IPerformance

from .error import RequestError, RequestSetupError, ResponseHandlingError, PerformanceNotFoundError, UnkownError


class SyncManager(object):

    #
    # INIT
    # 

    def __init__(self, options):
        self.options = options
        self.twt_api = self.options['api']
        self.CORE = self.options['core']
        self.fields_schema = getFieldsInOrder(IPerformance)
    #
    # UTILS
    #
    def logger(self, message, err):
        ## log into CSV
        print "%s. Exception message: %s" %(message, err)

    #
    # PARSE JSON
    #
    def match(self, field):
        # find match in the core
        if field in self.CORE.keys():
            if self.CORE[field]:
                return self.CORE[field]
            else:
                self.logger("[Warning] API field '%s' is ignored in the fields mapping" %(field), "Field ignored in mapping.")
                return False
        else:
            # log field not match
            self.logger("[Error] API field '%s' does not exist in the fields mapping" %(field), "Field not found in mapping.")
            return False
    #
    # DATA
    #
    def create_performance(self, performance_data):
        pass

    def set_availability(self, performance_brain, new_availability):
        pass

    def get_all_events(self, date_from):
        pass

    #
    # Sync one performance 
    #

    def safe_value(self, fieldvalue):
        if isinstance(fieldvalue, int):
            fieldvalue_safe = "%s" %(fieldvalue)
            return fieldvalue_safe
        else:
            return fieldvalue

    def clean_all_fields(self, performance):

        # get all fields from schema
        for fieldname, field in self.fields_schema:
            if fieldname != 'performance_id':
                self.clean_field(performance, fieldname, field)
            
        # extra fields that are not in the behavior
        # location
        setattr(performance, 'location', "")

        return performance

    def clean_field(self, performance, fieldname, field):
        if ITextLine.providedBy(field):
            setattr(performance, fieldname, "")
        elif ITuple.providedBy(field):
            setattr(performance, fieldname, [])
        elif IBool.providedBy(field):
            setattr(performance, fieldname, False)
        elif IRichText.providedBy(field):
            richvalue = RichTextValue("", 'text/html', 'text/html')
            setattr(performance, fieldname, richvalue)
        else:
            self.logger("[Error] Field '%s' type is not recognised. " %(fieldname), "Field cannot be cleaned before sync.")

        return performance

    def validate_dates(self, performance, performance_data):
        startDateTime = performance_data.get('startDateTime', '')
        endDateTime = performance_data.get('endDateTime', '')

        if startDateTime and not endDateTime:
            performance_date_fields = IEventAccessor(performance)
            performance_date_fields.end = performance_date_fields.start
            return True
        if not startDateTime and not endDateTime:
            self.logger("[Error] There are no dates the performance. ", "Performance dates cannot be found.")
            return False

        return True


    def validate_performance_data(self, performance, performance_data):
        self.validate_dates(performance, performance_data)
        performance.reindexObject()
        transaction.get().commit()
        return performance

    def update_field(self, performance, fieldname, fieldvalue):
        plonefield_match = self.match(fieldname)
        if plonefield_match:
            try:
                if not hasattr(performance, plonefield_match):
                    self.logger("[Error] Plone field '%s' does not exist" %(plonefield_match), "Plone field not found")
                    return None

                if plonefield_match:
                    transform_value = self.transform_special_fields(performance, fieldname, fieldvalue)
                    if transform_value:
                        return transform_value
                    else:
                        setattr(performance, plonefield_match, self.safe_value(fieldvalue))
                        return fieldvalue
                else:
                    return False
            except Exception as err:
                self.logger("[Error] Exception while syncing the API field %s" %(fieldname), err)
                return None
        else:
            return None

    def update_all_fields(self, performance, performance_data):
        self.clean_all_fields(performance)
        supdated_fields = [(self.update_field(performance, field, performance_data[field]), field) for field in performance_data.keys()]
        performance = self.validate_performance_data(performance, performance_data)
        return performance

    def find_performance(self, performance_id):
        result = plone.api.content.find(performance_id=performance_id)
        if result:
            return result[0].getObject()
        else:
            raise PerformanceNotFoundError("Performance with ID '%s' is not found in Plone" %(performance_id))


    def update_performance(self, performance_id):
        try:
            resp = self.twt_api.get_performance_availability(performance_id)
            if 'performance' in resp:
                performance_data = resp['performance']
                performance = self.find_performance(performance_id)
                updated_performance = self.update_all_fields(performance, performance_data)
                return updated_performance
            else:
                self.logger("[Error] performance is not found in the APIs response. ID: %s" %(performance_id), "Invalid API response.")
                return None
        except Exception as err:
            self.logger("[Error] Cannot update the performance ID: %s" %(performance_id), err)
            raise
        
    def unpublish_performance(self, performance_id):
        pass

    def delete_performance(self, performance_id):
        pass

    #
    # Transform special fields
    #


    def transform_special_fields(self, performance, fieldname, fieldvalue):
        special_field_handler = self.get_special_fields_handlers(fieldname)
        if special_field_handler:
            special_field_value = special_field_handler(performance, fieldname, fieldvalue)
            return special_field_value
        return False


    def get_special_fields_handlers(self, fieldname):
        SPECIAL_FIELDS_HANDLERS = {
            "title": self._transform_performance_title,
            "eventGenre": self._transform_event_genre,
            "startDateTime": self._transform_start_date,
            "endDateTime": self._transform_end_date,
            "tags": self._transform_tags,
            "ranks": self._transform_ranks
        }

        if fieldname in SPECIAL_FIELDS_HANDLERS:
            return SPECIAL_FIELDS_HANDLERS[fieldname]
        else:
            return None

    def _transform_performance_title(self, performance, fieldname, fieldvalue):
        setattr(performance, 'performance_title', fieldvalue)
        return fieldvalue

    def _transform_event_genre(self, performance, fieldname, fieldvalue):
        performance.setSubject([fieldvalue])
        return [fieldvalue]

    def _transform_start_date(self, performance, fieldname, fieldvalue):
        performance_date_fields = IEventAccessor(performance)
        date_datetime = datetime.strptime(fieldvalue, '%Y-%m-%d %H:%M')
        performance_date_fields.start = date_datetime
        return fieldvalue

    def _transform_end_date(self, performance, fieldname, fieldvalue):
        performance_date_fields = IEventAccessor(performance)
        date_datetime = datetime.strptime(fieldvalue, '%Y-%m-%d %H:%M')
        performance_date_fields.end = date_datetime
        return fieldvalue

    def _transform_tags(self, performance, fieldname, fieldvalue):
        return fieldvalue

    def _transform_ranks_generate_prices(self, rank):
        prices = rank.get('prices', '')
        final_value = ""

        if prices:
            if len(prices) > 1:
                for price in prices:
                    priceTypeDescription = price['priceTypeDescription']
                    price_value = price['price']
                    final_value += "<li>%s %s</li>" %(priceTypeDescription, price_value)
                return final_value
            elif len(prices) == 1:
                price = prices[0]
                price_value = price['price']
                final_value += "<li>%s</li>" %(price_value)
                return final_value
            else:
                return ""
        else:
            return ""

    def _transform_ranks(self, performance, fieldname, fieldvalue):

        html_value = ""

        if len(fieldvalue) > 1:
            for rank in fieldvalue:
                rankDescription = rank['rankDescription']
                prices = self._transform_ranks_generate_prices(rank)
                html_value += "<p>%s</p><ul>%s</ul>" %(rankDescription, prices)
            setattr(performance, 'price', html_value)

        elif len(fieldvalue) == 1:
            rank = fieldvalue[0]
            prices = self._transform_ranks_generate_prices(rank)
            html_value += "<ul>%s</ul>" %(prices)
            setattr(performance, 'price', html_value)
        else:
            return fieldvalue
            
        return fieldvalue

    


    
