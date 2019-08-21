#!/usr/bin/env python
# -*- coding: utf-8 -*-

from plone.registry.interfaces import IRegistry
from zope.component import getUtility
from collective.twtsyncmanager.controlpanel import ITWTControlPanel
from datetime import datetime, timedelta

#
# Common definitions
#
ONE_YEAR = 365
DATE_FORMAT = "%Y-%m-%d"

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


def get_datetime_today(as_string=False):
    ## format = YYYY-MM-DD
    today = datetime.today()
    if as_string:
        return today.strftime(DATE_FORMAT)
    else:
        return today

def get_datetime_future(as_string=False, years=20):
    ## format = YYYY-MM-DD
    today = datetime.today()
    time_leap = years*ONE_YEAR
    future = today + timedelta(days=time_leap)
    if as_string:
        date_future = future.strftime(DATE_FORMAT)
        return date_future
    else:
        return future
