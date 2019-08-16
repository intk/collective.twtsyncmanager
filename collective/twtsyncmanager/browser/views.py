#!/usr/bin/env python
# -*- coding: utf-8 -*-
from Products.Five import BrowserView
from collective.twtsyncmanager.api_connection import APIConnection
from collective.twtsyncmanager.sync_manager import SyncManager
from collective.twtsyncmanager.mapping_core import CORE as SYNC_CORE
from Products.statusmessages.interfaces import IStatusMessage
from zExceptions import Redirect

class SyncSinglePerformance(BrowserView):

    def __call__(self):
        return self.sync()


    def logger(self, message, err):
        ## log into CSV
        print "%s. Exception message: %s" %(message, err)

    def sync(self):

        ## we should get the settings from the controlpanel
        api_settings = {
            'test': {
                'url': "https://hetpark.tst3.ticketworks.nl/mtTicketingAPI",
                'api_key': "d437c0cb-34ab-480f-851f-aba9a"
            },
            'prod': {
                'url': "https://hetpark.tst3.ticketworks.nl/mtTicketingAPI",
                'api_key': "d437c0cb-34ab-480f-851f-aba9a"
            },
            'api_mode': 'test'
        }

        context_performance_id = getattr(self.context, 'performance_id', None)
        redirect_url = self.context.absolute_url()

        if context_performance_id:
            try:
                api_connection = APIConnection(api_settings)
                sync_options = {"api": api_connection, 'core': SYNC_CORE}
                sync_manager = SyncManager(sync_options)
                
                performance_data = sync_manager.update_performance(performance_id=context_performance_id)
                messages = IStatusMessage(self.request)
                messages.add(u"Performance ID %s is now synced." %(context_performance_id), type=u"info")
            except Exception as err:
                self.logger("[Error] Error while requesting the sync for the performance ID: %s" %(context_performance_id), err)
                messages = IStatusMessage(self.request)
                messages.add(u"Performance ID %s failed to sync with the api. Please contact the website administrator." %(context_performance_id), type=u"error")
                raise Redirect(redirect_url)

            raise Redirect(redirect_url)
        else:
            messages = IStatusMessage(self.request)
            messages.add(u"This performance cannot be synced with the API. Performance ID is missing.", type=u"error")
            self.logger("[Error] Error while requesting the sync for the performance. Performance ID is not available.", "Performance ID not found.")
            raise Redirect(redirect_url)


