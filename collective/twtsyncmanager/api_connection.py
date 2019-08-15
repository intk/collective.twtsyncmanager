#!/usr/bin/python
# -*- coding: utf-8 -*-


#
# Ticket works sync mechanism by Andre Goncalves
#

import re
try:
    from urllib.parse import urlencode
except ImportError:
    # support python 2
    from urllib import urlencode

#from .error import RequestError, RequestSetupError
import sys



class Error(Exception):
    """Base exception."""

    def __init__(self, message):
        Exception.__init__(self, message)

        # Avoid warnings about BaseException.message being deprecated.
        self.message = message

    def __str__(self):
        """
        Customize string representation in Python 2.
        We can't have string representation containing unicode characters in Python 2.
        """
        if sys.version_info.major == 2:
            return self.message.encode('ascii', errors='ignore')
        else:
            return super(Error, self).__str__()


class RequestError(Error):
    """Errors while preparing or performing an API request."""
    pass


class RequestSetupError(RequestError):
    """Errors while preparing an API request."""
    pass


def generate_querystring(params):
    """
    Generate a querystring
    """
    if not params:
        return None
    parts = []
    for param, value in sorted(params.items()):
        parts.append(urlencode({param: value}))

    if parts:
        return '&'.join(parts)


class APIConnection(object):

    ENVIRONMENTS = ['test', 'prod']
    URL_REGEX = re.compile(
        r'^(?:http|ftp)s?://' # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|' # domain
        r'localhost|' # localhost
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})' # ...or ip
        r'(?::\d+)?' # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    API_KEY_SIZE = 5

    def __init__(self, api_settings):
        if api_settings and isinstance(api_settings, dict):
            self.api_settings = self.validate_settings(api_settings)
        else:
            self.raise_request_setup_error("Required API settings are not found or have an invalid format.")

        self.api_mode = api_settings['api_mode']

    # 
    # Validaton methods
    #
    def raise_request_setup_error(self, message):
        raise RequestSetupError(message)

    def validate_settings(self, api_settings):
        for environment in self.ENVIRONMENTS:
            if environment not in api_settings:
                self.raise_request_setup_error("Details for the environment '%s' are not available in the API settings" %(environment))
            else:
                env = self.validate_environment(environment, api_settings[environment])

        api_mode = api_settings.get('api_mode', None)
        if not api_mode:
            self.raise_request_setup_error("Required API mode cannot be found in the settings.")
        else:
            self.validate_api_mode(api_mode)

        return api_settings

    def validate_environment(self, environment_name, environment):
        if environment:
            url = environment.get('url', None)
            api_key = environment.get('api_key', None)
            
            if not url:
                self.raise_request_setup_error("Required URL for the environment '%s' cannot be found" %(environment_name))
            else:
                self.validate_url(url)
            
            if not api_key:
                self.raise_request_setup_error("Required API key for the environment '%s' cannot be found" %(environment_name))
            else:
                self.validate_api_key(api_key)

            return environment
        else:
            self.raise_request_setup_error("Required details for the environment '%s' are not available in the API settings" %(environment_name))
            
    def validate_url(self, url):
        if re.match(self.URL_REGEX, url) is not None:
            return url
        else:
            self.raise_request_setup_error("URL '%s' is not valid." %(url))

    def validate_api_key(self, api_key):
        if api_key and isinstance(api_key, basestring):
            api_key_split = api_key.split('-')
            if len(api_key_split) != self.API_KEY_SIZE:
                self.raise_request_setup_error("API key '%s' is not valid." %(api_key))
        else:
            self.raise_request_setup_error("API key '%s' is not valid." %(api_key))
        
        return api_key

    def validate_api_mode(self, api_mode):
        if api_mode and isinstance(api_mode, basestring):
            if api_mode not in self.ENVIRONMENTS:
                self.raise_request_setup_error("API mode '%s' is not valid." %(api_mode))
        else:
            self.raise_request_setup_error("API mode '%s' is not valid." %(api_mode))

        return api_mode

    # 
    # CALL METHODS
    #

    def _format_request_data(self, params):
        querystring = generate_querystring(params)
        url = self.api_settings[self.api_mode]['url']

        if querystring:
            url += '?' + querystring
            params = None

        return url

    def _perform_http_call_apikey(self, http_method, params=None)
        try:

            url = self._format_request_data(params)

            response = requests.request(
                http_method, url,
                headers={
                    'Accept': 'application/json',
                    'Content-Type': 'application/json',
                    'User-Agent': 'Mozilla/5.0',
                },
                timeout=self.timeout,
            )
        except Exception as err:
            raise RequestError('Unable to communicate with TWT API: {error}'.format(error=err))

        return response
    #
    # DATA METHODS
    #

    def set_api_mode(self, api_mode):
        api_mode = self.validate_api_mode(api_mode)
        self.api_mode = api_mode
        return self.api_mode

    def get_api_url(self):
        return self.api_settings[self.api_mode]['url']

    def get_api_key(self):
        return self.api_settings[self.api_mode]['api_key']

    def get_performance_list_by_date(date_from, date_until, season):


        pass

    def get_performance_list_by_season(season):

        pass

    def get_performance_availability(self, performance_id):


        pass


if __name__ == '__main__':
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

    api_connection = APIConnection(api_settings)


    # Test get performance availability
    test_performance_id = "1409"
    self.get_performance_availability(test_performance_id)

    ## TODO
    # Test get list of performances by date
    # Test get list of performances by season


    





