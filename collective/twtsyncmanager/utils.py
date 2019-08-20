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

def get_api_settings():
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


def get_datetime_today():
    ## TODO
    ## format = YYYY-MM-DD
    return ""

def get_datetime_future(years=20):
    ## TODO
    ## format = YYYY-MM-DD
    return ""
