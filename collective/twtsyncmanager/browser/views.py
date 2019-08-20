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
from collective.twtsyncmanager.controlpanel import ITWTControlPanel


class SyncSinglePerformance(BrowserView):

    def __call__(self):
        return self.sync()

    def logger(self, message, err):
        ## TODO: log into CSV
        ## TODO: log into Sentry
        ## TODO: Create a module for logging (connect it with the api)
        ## TODO: This module should be send in the api settings
        print "%s. Exception message: %s" %(message, err)

    def get_api_settings(self):
        registry = getUtility(IRegistry)
        settings = registry.forInterface(ITWTControlPanel)
        
        api_settings = {
            'test': {
                'url': getattr(settings, 'api_url_test', None),
                'api_key': getattr(settings, 'api_key_test', None)
            },
            'prod': {
                'url': getattr(settings, 'api_url_prod', None),
                'api_key': getattr(settings, 'api_key_prod', None)
            },
            'api_mode': getattr(settings, 'api_prod_mode', None)
        }

        return api_settings

    def sync(self):

        # Get the necessary information to call the api and return a response
        context_performance_id = getattr(self.context, 'performance_id', None)
        redirect_url = self.context.absolute_url()
        messages = IStatusMessage(self.request)

        if context_performance_id:
            try:
                # Get API settings from the controlpanel
                api_settings = self.get_api_settings()

                # Create the API connection
                api_connection = APIConnection(api_settings)

                # Create the settings for the sync
                # Initiate the sync manager
                sync_options = {"api": api_connection, 'core': SYNC_CORE}
                sync_manager = SyncManager(sync_options)
                
                # Trigger the sync to update one performance
                performance_data = sync_manager.update_performance(performance_id=context_performance_id)
                messages.add(u"Performance ID %s is now synced." %(context_performance_id), type=u"info")
            except Exception as err:
                self.logger("[Error] Error while requesting the sync for the performance ID: %s" %(context_performance_id), err)
                messages.add(u"Performance ID '%s' failed to sync with the api. Please contact the website administrator." %(context_performance_id), type=u"error")
        else:
            messages.add(u"This performance cannot be synced with the API. Performance ID is missing.", type=u"error")
            self.logger("[Error] Error while requesting the sync for the performance. Performance ID is not available.", "Performance ID not found.")
        
        # Redirect to the original page
        raise Redirect(redirect_url)


