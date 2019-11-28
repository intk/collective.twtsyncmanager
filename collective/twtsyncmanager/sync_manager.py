#!/usr/bin/env python
# -*- coding: utf-8 -*-

#
# Ticketworks API sync mechanism by Andre Goncalves
#
import plone.api
import transaction

# Plone dependencies
from zope.schema.interfaces import ITextLine, ITuple, IBool
from plone.app.textfield.interfaces import IRichText
from plone.app.textfield.value import RichTextValue
from zope.schema import getFieldsInOrder
from plone.event.interfaces import IEventAccessor
from datetime import datetime
from zope.component import getUtility
from plone.i18n.normalizer.interfaces import IIDNormalizer

# Product dependencies
from collective.behavior.performance.behavior import IPerformance
from .error import raise_error
from .logging import logger
from .utils import str2bool, normalize_id

from collective.twtsyncmanager.utils import get_datetime_today, get_datetime_future, DATE_FORMAT

class SyncManager(object):
    #
    # Init methods 
    # 
    DEFAULT_CONTENT_TYPE = "Event"
    DEFAULT_FOLDER = "/programma"
    AVAILABILITY_FIELDS = ['onsale', 'performanceStatus', 'statusMessage']
    PERFORMANCE_STATUSES_TEXT = {
        "ONSALE": "Bestellen",
        "SOLDOUT": "Uitverkocht",
        "CANCELLED": "Geanuleerd",
        "ONHOLD": "Tijdelijk onbeschikbaar",
        "NOSALE": "Geen tickets"
    }
    REDIRECT_URL = "https://hetpark.tst3.ticketworks.nl/mtTicket/performance"

    def __init__(self, options):
        self.options = options
        self.twt_api = self.options['api']
        self.CORE = self.options['core']
        self.fields_schema = getFieldsInOrder(IPerformance)

    #
    # Sync operations
    #
    def update_performance_by_id(self, performance_id, arrangement_list=None):
        performance = self.find_performance(performance_id)
        performance_data = self.twt_api.get_performance_availability(performance_id)

        if not arrangement_list:
            arrangement_list = self.twt_api.get_arrangement_list_by_performance_id(performance_id, date_from=get_datetime_today(as_string=True), date_until=get_datetime_future(as_string=True))

        updated_performance = self.update_performance(performance_id, performance, performance_data, arrangement_list)

        return updated_performance

    def update_performance_list_by_date(self, date_from, date_until, create_and_unpublish=False):
        performance_list = self.twt_api.get_performance_list_by_date(date_from=date_from, date_until=date_until)
        
        if create_and_unpublish:
            website_performances = self.get_all_events(date_from=date_from)
            self.sync_performance_list(performance_list, website_performances)
        else:
            self.update_performance_list(performance_list)
        
        return performance_list

    def update_availability_by_date(self, date_from, date_until):
        website_performances = self.get_all_events(date_from=date_from)
        api_performances = self.twt_api.get_performance_list_by_date(date_from=date_from, date_until=date_until)
        
        performances_data = self.build_performances_data_dict(api_performances)
        updated_availability = self.update_availability(performances_data, website_performances)

        return updated_availability

    #
    # CRUD operations
    #
    def update_performance(self, performance_id, performance, performance_data, arrangement_list=None):
        updated_performance = self.update_all_fields(performance, performance_data, arrangement_list)
        logger("[Status] Performance with ID '%s' is now updated. URL: %s" %(performance_id, performance.absolute_url()))
        return updated_performance

    def create_performance(self, performance_id):
        performance_data = self.twt_api.get_performance_availability(performance_id)
        
        try:
            title = performance_data['title']
            description = performance_data.get('subtitle', '')
            new_performance_id = normalize_id(title)
            container = self.get_container()
            new_performance = plone.api.content.create(container=container, type=self.DEFAULT_CONTENT_TYPE, id=new_performance_id, safe_id=True, title=title, description=description)
            logger("[Status] Performance with ID '%s' is now created. URL: %s" %(performance_id, new_performance.absolute_url()))
            updated_performance = self.update_performance(performance_id, new_performance, performance_data)
        except Exception as err:
            logger("[Error] Error while creating the performance ID '%s'" %(performance_id), err)
            return None

    def update_availability(self, performances_data, website_performances):
        availability_changed_list = [performance_brain for performance_brain in website_performances if self.is_availability_changed(performance_brain, self.get_performance_data_from_list_by_id(performance_brain, performances_data))]
        updated_availability = [self.update_availability_field(performance_brain, performances_data[performance_brain.performance_id]) for performance_brain in availability_changed_list]
        return updated_availability
        
    def create_new_performances(self, performances_data, website_data):
        new_performances = [api_id for api_id in performances_data.keys() if api_id not in website_data.keys()]
        created_performances = [self.create_performance(performance_id) for performance_id in new_performances]
        return new_performances

    def update_performance_list(self, performance_list):
        for performance in performance_list:
            performance_id = performance.get('id', '')
            try:
                performance_data = self.update_performance_by_id(performance_id)
            except Exception as err:
                logger("[Error] Error while requesting the sync for the performance ID: %s" %(performance_id), err)
        
        return performance_list

    def sync_performance_list(self, performance_list, website_performances):

        website_data = self.build_website_data_dict(website_performances)

        for performance in performance_list:
            performance_id = str(performance.get('id', ''))
            if performance_id in website_data.keys():
                consume_performance = website_data.pop(performance_id)
                try:
                    performance_data = self.update_performance_by_id(performance_id)
                except Exception as err:
                    logger("[Error] Error while updating the performance ID: %s" %(performance_id), err)
            else:
                try:
                    new_performance = self.create_performance(performance_id)
                except Exception as err:
                    logger("[Error] Error while creating the performance ID: %s" %(performance_id), err)
        
        if len(website_data.keys()) > 0:
            unpublished_performances = [self.unpublish_performance(performance_brain.getObject()) for performance_brain in website_data.values()]

        return performance_list

    def unpublish_performance(self, performance):
        plone.api.content.transition(obj=performance, to_state="private")
        logger("[Status] Unpublished performance with ID: '%s'" %(getattr(performance, 'performance_id', '')))
        return performance

    def publish_performance(self, performance):
        plone.api.content.transition(obj=performance, to_state="published")

    def delete_performance(self, performance):
        plone.api.content.delete(obj=performance)

    def unpublish_performance_by_id(self, performance_id):
        obj = self.find_performance(performance_id=performance_id)
        self.unpublish_performance(obj)

    def delete_performance_by_id(self, performance_id):
        obj = self.find_performance(performance_id=performance_id)
        self.delete_performance(obj)    

    def get_all_upcoming_events(self):
        today = datetime.today()
        results = self.get_all_events(date_from=today)
        return results

    def get_all_events(self, date_from=None):
        if date_from:
            if isinstance(date_from, str):
                date_from = datetime.strptime(date_from, DATE_FORMAT)
            results = plone.api.content.find(portal_type=self.DEFAULT_CONTENT_TYPE, start={'query': date_from, 'range': 'min'})
            return results
        else:
            results = plone.api.content.find(portal_type=self.DEFAULT_CONTENT_TYPE)
            return results

    #
    # CRUD utils
    # 
    def get_performance_data_from_list_by_id(self, performance_brain, performances_data):
        performance_id = getattr(performance_brain, 'performance_id', None)
        if performance_id and performance_id in performances_data:
            return performances_data[performance_id]
        else:
            logger("[Error] Performance data for '%s' cannot be found." %(performance_brain.getURL()), "requestHandlingError")
            return None

    def build_performances_data_dict(self, api_performances):
        performances_data = {}
        for api_performance in api_performances:
            if 'id' in api_performance:
                performances_data[self.safe_value(api_performance['id'])] = api_performance
            else:
                logger('[Error] Performance ID cannot be found in the API JSON: %s' %(api_performance), 'requestHandlingError')
        return performances_data

    def build_website_data_dict(self, website_performances):
        website_performances_data = {}
        for website_performance in website_performances:
            performance_id = getattr(website_performance, 'performance_id', None)
            if performance_id:
                website_performances_data[self.safe_value(performance_id)] = website_performance
            else:
                logger('[Error] Performance ID value cannot be found in the brain url: %s' %(website_performance.getURL()), 'requestHandlingError')
        return website_performances_data


    def update_availability_field(self, performance_brain, performance_data):
        performance = performance_brain.getObject()
        for field in self.AVAILABILITY_FIELDS:
            try:
                setattr(performance, field, performance_data[field])
            except Exception as err:
                logger("[Error] Availability field '%s' cannot be updated for performance ID '%s'."%(field, performance_data.get('id', 'Unknown')), err)

        try:
            performance = self.generate_performance_availability_field(performance, performance_data)
        except Exception as err:
            logger("[Error] Performance availability field value cannot be updated for performance ID '%s'." %(performance_data.get('id', 'Unknown')), err)

        performance.reindexObject()
        transaction.get().commit()
        logger("[Status] Performance availability is now updated for ID: %s" %(performance_brain.performance_id))
        return performance_brain

    def is_availability_changed(self, performance_brain, performance_data):
        ## TODO needs refactoring 
        current_onsale_value = str2bool(performance_brain.onsale)
        if performance_data and 'onsale' in performance_data:
            performance_data_onsale_value = performance_data['onsale']
            if performance_data_onsale_value != current_onsale_value:
                logger('[Status] Availability field is changed for the performance ID: %s.' %(performance_brain.performance_id))
                return True
            else:
                logger('[Status] Availability field is NOT changed for the performance ID: %s.' %(performance_brain.performance_id))
                return False
        elif not performance_data:
            return False
        else:
            if getattr(performance_brain, 'performance_id', None):
                logger("[Error] Performance 'onsale' field is not available for the ID '%s'." %(performance_brain.performance_id), 'requestHandlingError')
            else:
                return False

    def find_performance(self, performance_id):
        performance_id = self.safe_value(performance_id)
        result = plone.api.content.find(performance_id=performance_id)
        if result:
            return result[0].getObject()
        else:
            raise_error("performanceNotFoundError", "Performance with ID '%s' is not found in Plone" %(performance_id))

    def find_product_details_by_id(self, product_id, scale="mini"):
        product_id = self.safe_value(product_id)
        result = plone.api.content.find(product_id=product_id)
        if result:
            product_description = result[0].Description
            lead_image_scale_url = ""
            leadMedia = getattr(result[0], 'leadMedia', None)
            if leadMedia:
                images = plone.api.content.find(UID=leadMedia)
                if images:
                    lead_image = images[0]
                    lead_image_url = lead_image.getURL()
                    lead_image_scale_url = "%s/@@images/image/%s" %(lead_image_url, scale)
            return lead_image_scale_url, product_description

        else:
            return "", ""

    def match(self, field):
        # Find match in the core
        if field in self.CORE.keys():
            if self.CORE[field]:
                return self.CORE[field]
            else:
                logger("[Warning] API field '%s' is ignored in the fields mapping" %(field), "Field ignored in mapping.")
                return False
        else:
            # log field not match
            logger("[Error] API field '%s' does not exist in the fields mapping" %(field), "Field not found in mapping.")
            return False

    def update_field(self, performance, fieldname, fieldvalue):
        plonefield_match = self.match(fieldname)

        if plonefield_match:
            try:
                if not hasattr(performance, plonefield_match):
                    logger("[Error] Plone field '%s' does not exist" %(plonefield_match), "Plone field not found")
                    return None
                transform_value = self.transform_special_fields(performance, fieldname, fieldvalue)
                if transform_value:
                    return transform_value
                else:
                    setattr(performance, plonefield_match, self.safe_value(fieldvalue))
                    return fieldvalue
            except Exception as err:
                logger("[Error] Exception while syncing the API field '%s'" %(fieldname), err)
                return None
        else:
            return None

    def update_all_fields(self, performance, performance_data, arrangement_list=None):
        self.clean_all_fields(performance)
        updated_fields = [(self.update_field(performance, field, performance_data[field]), field) for field in performance_data.keys()]
        performance = self.generate_performance_availability_field(performance, performance_data)
        performance = self.generate_arrangement_list_field(performance, arrangement_list)

        performance = self.validate_performance_data(performance, performance_data)
        return performance

    def get_container(self):
        container = plone.api.content.get(path=self.DEFAULT_FOLDER)
        return container

    #
    # Sanitising/validation methods
    #

    def generate_performance_availability_field(self, performance, performance_data):
        fieldvalue = self.generate_availability_html(performance_data)
        setattr(performance, 'performance_availability', fieldvalue)
        return performance

    def generate_arrangement_list_field(self, performance, arrangement_list):
        fieldvalue = self.generate_arrangement_list_html(arrangement_list)
        setattr(performance, 'arrangements', fieldvalue)
        return performance

    def generate_availability_html(self, performance_data):
        performanceStatus = performance_data.get('performanceStatus', )
        onsale = performance_data.get('onsale', '')
        if performanceStatus:
            if performanceStatus != "ONSALE":
                availability_value = self.get_availability_html(performanceStatus, performance_data)
                final_value = RichTextValue(availability_value, 'text/html', 'text/html')
                return final_value
            else:
                if onsale == True:
                    availability_value = self.get_availability_html(performanceStatus, performance_data)
                    final_value = RichTextValue(availability_value, 'text/html', 'text/html')
                    return final_value
                elif onsale == False:
                    final_value = RichTextValue("", 'text/html', 'text/html')
                    return final_value
                else:
                    final_value = RichTextValue("", 'text/html', 'text/html')
                    return final_value
        else:
            logger('[Error] Performance status is not available. Cannot update the availability field.', 'requestHandingError')
            final_value = RichTextValue("", 'text/html', 'text/html')
            return final_value


    def generate_arrangement_list_html(self, arrangement_list):
        if arrangement_list:
            arrangements_html = [self.get_arrangement_html(arrangement) for arrangement in arrangement_list]
            final_arrangements_list = "<h3>Arrangementen</h3>"
            final_arrangements_list += "".join(arrangements_html)
            final_value = RichTextValue(final_arrangements_list, 'text/html', 'text/html')
            return final_value
        else:
            final_value = RichTextValue("", 'text/html', 'text/html')
            return final_value

    def get_arrangement_html(self, arrangement):
        title = arrangement.get('shortTitle', '')
        arrangement_id = arrangement.get('id', '')
        product_id = arrangement.get('product_id', '')
        image_url = ""
        if product_id:
            image_url, description = self.find_product_details_by_id(product_id)

        if image_url:
            arrangement_html = "<div class='arrangement-wrapper'><div class='arrangement-image'><a href='%s/%s'><img src='%s'/></a></div><div class='arrangement-details'><h4><a href='%s/%s'>%s</a><h4><p class='arrangement-description'>%s</p></div></div>" %(self.REDIRECT_URL, arrangement_id, image_url, self.REDIRECT_URL, arrangement_id, title, description)
        else:
            arrangement_html = "<div class='arrangement-wrapper'><div class='arrangement-details'><h4><a href='%s/%s'>%s</a></h4><p class='arrangement-description'>%s</p></div></div>" %(self.REDIRECT_URL, arrangement_id, title, description)
        
        return arrangement_html

    def get_availability_html(self, performanceStatus, performance_data):
        field_text = self.get_availability_status_text(performanceStatus)
        disabled_state = ""
        if performanceStatus != "ONSALE":
            disabled_state = "disabled"

        if field_text:
            if performanceStatus == "NOSALE":
                availability_html = "<p>%s</p>" %(field_text)
                return availability_html
            elif performanceStatus != "ONSALE":
                availability_html = "<a class='btn btn-default' %s>%s</a>" %(disabled_state, field_text)
                return availability_html
            else:
                availability_html = "<a href='%s' class='btn btn-default' %s>%s</a>" %(self.get_redirect_url(performance_data), disabled_state, field_text)
                return availability_html
        else:
            return ""

    def get_availability_status_text(self, performanceStatus):
        if performanceStatus in self.PERFORMANCE_STATUSES_TEXT:
            return self.PERFORMANCE_STATUSES_TEXT[performanceStatus]
        else:
            return None

    def get_redirect_url(self, performance_data):

        performance_id = performance_data['id']
        redirect_url = "%s/%s" %(self.REDIRECT_URL, str(performance_id))
        return redirect_url

    def safe_value(self, fieldvalue):
        if isinstance(fieldvalue, bool):
            return fieldvalue
        elif isinstance(fieldvalue, int):
            fieldvalue_safe = "%s" %(fieldvalue)
            return fieldvalue_safe
        else:
            return fieldvalue

    def clean_all_fields(self, performance):

        # get all fields from schema
        for fieldname, field in self.fields_schema:
            if fieldname not in ['performance_id', 'waiting_list']:
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
            logger("[Error] Field '%s' type is not recognised. " %(fieldname), "Field cannot be cleaned before sync.")

        return performance

    def validate_dates(self, performance, performance_data):
        startDateTime = performance_data.get('startDateTime', '')
        endDateTime = performance_data.get('endDateTime', '')

        if startDateTime and not endDateTime:
            performance_date_fields = IEventAccessor(performance)
            performance_date_fields.end = performance_date_fields.start
            return True
        
        if not startDateTime and not endDateTime:
            logger("[Error] There are no dates for the performance. ", "Performance dates cannot be found.")
            return False

        return True

    def validate_performance_data(self, performance, performance_data):
        validated = self.validate_dates(performance, performance_data)
        if validated:
            performance.reindexObject()
            transaction.get().commit()
            return performance
        else:
            raise_error("validationError", "Performance is not valid. Do not commit changes to the database.")

    #
    # Transform special fields
    # Special methods
    #
    def transform_special_fields(self, performance, fieldname, fieldvalue):
        special_field_handler = self.get_special_fields_handlers(fieldname)
        if special_field_handler:
            if fieldvalue:
                special_field_value = special_field_handler(performance, fieldname, fieldvalue)
                return special_field_value
            else:
                return fieldvalue
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
        current_subjects = performance.Subject()
        if 'frontpage-slideshow' in current_subjects:
            subjects = ['frontpage-slideshow', fieldvalue]
            performance.setSubject(subjects)
        else:
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

    def _transform_currency(self, currency):
        currencies = {
            "EUR": u'€'
        }

        if currency in currencies:
            return currencies[currency]
        else:
            return currency

    def _transform_ranks_generate_prices(self, rank, multiple_ranks=False):
        prices = rank.get('prices', '')
        final_value = ""

        if prices:
            if len(prices) > 1:
                if not multiple_ranks:
                    final_value = "<strong>Prijzen</strong>"

                default_prices = []
                available_prices = []

                for price in prices:
                    priceTypeDescription = price.get('priceTypeDescription', '')
                    price_value = price.get('price', '')
                    is_default_price = price.get('isDefault', '')
                    currency = self._transform_currency(price.get('currency', u'€'))
                    new_price = "<span><span class='price-type'>%s</span> %s%s</span>" %(priceTypeDescription, currency, price_value)

                    if is_default_price:
                        default_prices.append(new_price)
                    else:
                        available_prices.append(new_price)
                        
                generated_prices = default_prices+available_prices
                final_value += "<div class='list-prices'>"+"".join(generated_prices)+"</div>"
                return final_value
            elif len(prices) == 1:
                if not multiple_ranks:
                    final_value = "<strong>Prijs</strong>"

                price = prices[0]
                price_value = price.get('price', '')
                currency = self._transform_currency(price.get('currency', u'€'))
                final_value += "<span>%s%s</span>" %(currency, price_value)
                return final_value
            else:
                return ""
        else:
            return ""

    def _transform_ranks(self, performance, fieldname, fieldvalue):

        html_value = ""
        if len(fieldvalue) > 1:
            html_value = "<strong>Prijzen</strong>"
            for rank in fieldvalue:
                rankDescription = rank.get('rankDescription')
                prices = self._transform_ranks_generate_prices(rank, True)
                html_value += "<h6>%s</h6><div>%s</div>" %(rankDescription, prices)
            final_value = RichTextValue(html_value, 'text/html', 'text/html')
            setattr(performance, 'price', final_value)

        elif len(fieldvalue) == 1:
            rank = fieldvalue[0]
            prices = self._transform_ranks_generate_prices(rank)
            html_value += "<div>%s</div>" %(prices)
            final_value = RichTextValue(html_value, 'text/html', 'text/html')
            setattr(performance, 'price', final_value)
        else:
            return fieldvalue
            
        return fieldvalue
