#!/usr/bin/env python
# -*- coding: utf-8 -*-

#
# Ticket works sync mechanism by Andre Goncalves
#


"""
Utils for Plone:
* update_performance(performance_id, performance_data)
* create_performance(performance_data) 
* unpublish_performance(performance_id)
* delete_performance(performance_id)
* set_availability(performance_brain, new_availability)
* get_availability(performance_brain) 
* find_performance(performance_id) 
* get_all_events(date_from)

"""

class SyncManager:

    #
    # INIT
    # 

    def __init__(self, options):
        self.options = options
        self.twt_api = self.options['api']

    #
    # UTILS
    #
    def logger(self, message):
        pass

    #
    # PARSE JSON
    #
    def match(self, field):
        # find match in the core
        if field in self.CORE.keys():
            return CORE[field]
        else:
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

    def clean_all_fields(self, performance):
        pass

    def clean_field(self, performance, fieldname):
        # types of fields
        # 
        # 
        pass

    def update_field(self, performance, fieldname, fieldvalue):
        plonefield_match = self.match(fieldname)
        if plonefield_match:
            transform_value = self.transform_special_fields(performane, fieldname, fieldvalue)
            if transform_value:
                setattr(performance, plonefield_match, transform_value)
            else:
                setattr(performance, plonefield_match, fieldvalue)
            return performance
        else:
            # raise update field error
            return False

    def update_all_fields(self, performance, performance_data):
        self.clean_all_fields(performance)
        for field in performance_data.keys():
            self.update_field(performance, field, performance_data[field])
            self.transform_special_fields(performance, field, performance_data[field])
        return performance

    def find_performance(self, performance_id):
        pass

    def update_performance(self, performance_id):
        try:
            resp = self.twt_api.get_performance_availability(performance_id)
            if 'performance' in resp:
                performance_data = resp['performance']
                performance = self.find_performance(performance_id)
                updated_performance = self.update_all_fields(performance, performance_data)
            else:
                return

            return 
        except:
            self.logger()
            pass
        

    def unpublish_performance(self, performance_id):
        pass

    def delete_performance(self, performance_id)Ç
        pass

    #
    # Transform special fields
    #
    def _transform_performance_title(self, performance, fieldname, fieldvalue):
        pass

    def _transform_event_genre(self, performance, fieldname, fieldvalue):
        pass

    def _transform_start_date(self, performance, fieldname, fieldvalue):
        pass

    def _transform_end_date(self, performance, fieldname, fieldvalue):
        pass

    def get_special_fields_handlers(self, fieldname):
        SPECIAL_FIELDS_HANDLERS = {
            "title": _transform_performance_title,
            "eventGenre": _transform_event_genre,
            "startDateTime": _transform_start_date,
            "endDateTime": _transform_end_date
        }

        if fieldname in SPECIAL_FIELDS_HANDLERS:
            return SPECIAL_FIELDS_HANDLERS[fieldname]
        else:
            return None

    # eventGenre -> subjects
    # title -> plone title
    # dates -> plone dates
    # prices -> TODO
    def transform_special_fields(self, performance, fieldname, fieldvalue):
        special_field_handler = self.get_special_fields_handlers(fieldname)
        if special_field_handler:
            special_field_value = special_field_handler(performance, fieldname, fieldvalue)
            return special_field_value
        return False


    
