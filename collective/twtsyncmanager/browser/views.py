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


def test_sync_performance_list():

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

    performance_list = sync_manager.update_performance_list_by_date(date_from=dateFrom, date_until=dateUntil)
    return performance_list


def test_update_availability():

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

    logger("[Status] Start hourly sync test.")
    performance_list, created_performances = sync_manager.update_availability_by_date(date_from=dateFrom, date_until=dateUntil, create_new=True)
    logger("[Status] Finished hourly sync test.")

    print "Total performances to be created: %s" %(len(created_performances))
    print "Total performances to update availability: %s" %(len(performance_list))
    return performance_list, created_performances


#
# Performance hourly sync
#
class SyncPerformancesAvailability(BrowserView):

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
            logger("[Status] Start hourly sync.")
            update_availability_list, created_performances_list = sync_manager.update_availability_by_date(date_from=dateFrom, date_until=dateUntil, create_new=True)
            logger("[Status] Finished hourly sync.")
            messages.add(u"Performances availability is now synced.", type=u"info")
        except Exception as err:
            logger("[Error] Error while requesting the sync for the performances availability.", err)
            messages.add(u"Performances availability failed to sync with the api. Please contact the website administrator.", type=u"error")

        raise Redirect(redirect_url)


#
# Performance List sync
#
class SyncPerformancesList(BrowserView):

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
            logger("[Status] Start syncing performance list.")
            performance_list = sync_manager.update_performance_list_by_date(date_from=dateFrom, date_until=dateUntil)
            logger("[Status] Syncing performance list finished.")
            messages.add(u"Performance list is now synced.", type=u"info")
        except Exception as err:
            logger("[Error] Error while requesting the sync for the performance list.", err)
            messages.add(u"Performance list failed to sync with the api. Please contact the website administrator.", type=u"error")

        raise Redirect(redirect_url)

#
# Performance Availability
#
class SyncPerformance(BrowserView):

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
                logger("[Status] Start update of single performance.")
                performance_data = sync_manager.update_performance_by_id(performance_id=context_performance_id)
                logger("[Status] Finished update of single performance.")
                messages.add(u"Performance ID %s is now synced." %(context_performance_id), type=u"info")
            except Exception as err:
                logger("[Error] Error while requesting the sync for the performance ID: %s" %(context_performance_id), err)
                messages.add(u"Performance ID '%s' failed to sync with the api. Please contact the website administrator." %(context_performance_id), type=u"error")
        else:
            messages.add(u"This performance cannot be synced with the API. Performance ID is missing.", type=u"error")
            logger("[Error] Error while requesting the sync for the performance. Performance ID is not available.", "Performance ID not found.")
        
        # Redirect to the original page
        raise Redirect(redirect_url)


