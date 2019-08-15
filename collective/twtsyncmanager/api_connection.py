#!/usr/bin/python
# -*- coding: utf-8 -*-


#
# Ticket works sync mechanism by Andre Goncalves
#

import transaction
from datetime import datetime, timedelta
import urllib2, urllib
import requests
from plone.i18n.normalizer import idnormalizer
from lxml import etree
from plone.app.textfield.value import RichTextValue
from Products.CMFCore.utils import getToolByName
import re
import sys
import smtplib
import plone.api
from plone.app.multilingual.interfaces import ITranslationManager
from plone.app.contenttypes.behaviors.collection import ICollection
from .teylers_sync_core import CORE
from .exhibition_core import EXIBIT_CORE
from plone.event.interfaces import IEventAccessor
from collective.object.utils.views import update_exhibition_field_by_priref


class APIConnection:
    def __init__(self, portal, options):
        self.portal = portal
        self.options = options

    
