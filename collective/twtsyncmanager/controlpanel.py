# -*- coding: utf-8 -*-
from datetime import date
from plone.app.registry.browser.controlpanel import ControlPanelFormWrapper
from plone.app.registry.browser.controlpanel import RegistryEditForm
from plone.z3cform import layout
from zope import schema
from zope.interface import Interface

class ITWTControlPanel(Interface):

    api_key_test = schema.TextLine(
        title=u'API key (test)',
        required=False
    )

    api_url_test =  schema.TextLine(
        title=u'API url (test)',
        required=False
    )

    api_key_prod = schema.TextLine(
        title=u'API key (production)',
        required=False
    )

    api_url_prod =  schema.TextLine(
        title=u'API url (production)',
        required=False
    )

    api_availability_endpoint = schema.TextLine(
        title=u'Performance availability endpoint',
        required=False
    )

    api_list_endpoint = schema.TextLine(
        title=u'Performance list endpoint',
        required=False
    )

    api_prod_mode = schema.TextLine(
        title=u'Select the API mode (test or prod)',
        required=False
    )


class PerformanceControlPanelForm(RegistryEditForm):
    schema = ITWTControlPanel
    label = u'TWT api control panel'

class PerformanceControlPanelView(ControlPanelFormWrapper):
    form = PerformanceControlPanelForm

