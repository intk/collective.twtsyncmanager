#!/usr/bin/env python
# -*- coding: utf-8 -*-
from Products.Five import BrowserView
from collective.twtsyncmanager.api_connection import APIConnection
from collective.twtsyncmanager.sync_manager import SyncManager
from collective.twtsyncmanager.mapping_core import CORE as SYNC_CORE
from Products.statusmessages.interfaces import IStatusMessage
from zExceptions import Redirect
from plone.registry.interfaces import IRegistry
from zope.component import getUtility

#
# Product dependencies
#
from collective.twtsyncmanager.utils import get_api_settings, get_datetime_today, get_datetime_future
from collective.twtsyncmanager.error import raise_error
from collective.twtsyncmanager.logging import logger

#
# Performance List sync
#
class SyncPerformanceListView(BrowserView):

    def __call__(self):
        return self.sync()

    def sync(self):
        redirect_url = self.context.absolute_url()
        messages = IStatusMessage(self.request)

        # Get API settings from the controlpanel
        api_settings = get_api_settings()

        # Create the API connection
        api_connection = APIConnection(api_settings)

        # Create the settings for the sync
        # Initiate the sync manager
        sync_options = {"api": api_connection, 'core': SYNC_CORE}
        sync_manager = SyncManager(sync_options)

        dateFrom = get_datetime_today(as_string=True)
        dateUntil = get_datetime_future(as_string=True)

        try:
            performance_list = sync_manager.update_performance_list_by_date(date_from=dateFrom, date_until=dateUntil)
            messages.add(u"Performance list is now synced.", type=u"info")
        except Exception as err:
            logger("[Error] Error while requesting the sync for the performance list.", err)
            messages.add(u"Performance list failed to sync with the api. Please contact the website administrator.", type=u"error")

        raise Redirect(redirect_url)


#
# Performance Availability
#
class SyncPerformanceAvailabilityView(BrowserView):

    def __call__(self):
        return self.sync()

    def sync(self):

        # Get the necessary information to call the api and return a response
        context_performance_id = getattr(self.context, 'performance_id', None)
        redirect_url = self.context.absolute_url()
        messages = IStatusMessage(self.request)

        if context_performance_id:
            try:
                # Get API settings from the controlpanel
                api_settings = get_api_settings()

                # Create the API connection
                api_connection = APIConnection(api_settings)

                # Create the settings for the sync
                # Initiate the sync manager
                sync_options = {"api": api_connection, 'core': SYNC_CORE}
                sync_manager = SyncManager(sync_options)
                
                # Trigger the sync to update one performance
                performance_data = sync_manager.update_performance_by_id(performance_id=context_performance_id)
                messages.add(u"Performance ID %s is now synced." %(context_performance_id), type=u"info")
            except Exception as err:
                logger("[Error] Error while requesting the sync for the performance ID: %s" %(context_performance_id), err)
                messages.add(u"Performance ID '%s' failed to sync with the api. Please contact the website administrator." %(context_performance_id), type=u"error")
        else:
            messages.add(u"This performance cannot be synced with the API. Performance ID is missing.", type=u"error")
            logger("[Error] Error while requesting the sync for the performance. Performance ID is not available.", "Performance ID not found.")
        
        # Redirect to the original page
        raise Redirect(redirect_url)


