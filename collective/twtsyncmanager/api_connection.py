#!/usr/bin/python
# -*- coding: utf-8 -*-


#
# Ticketworks API sync mechanism by Andre Goncalves
#

# Global dependencies
import re
import requests
import sys

try:
    from urllib.parse import urlencode
except ImportError:
    # support python 2
    from urllib import urlencode

# Product dependencies
from .error import RequestError, RequestSetupError, ResponseHandlingError, PerformanceNotFoundError, UnkownError


# Global method
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

    #
    # Local definitions to the API connection
    #
    ENVIRONMENTS = ['test', 'prod']
    URL_REGEX = re.compile(
        r'^(?:http|ftp)s?://' # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|' # domain
        r'localhost|' # localhost
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})' # ...or ip
        r'(?::\d+)?' # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    API_KEY_SIZE = 5
    TIMEOUT = 10
    HTTP_METHOD = "get"
    FOUND_STATUS = "PERFORMANCE_FOUND"
    NOT_FOUND_STATUS = "PERFORMANCE_NOT_FOUND"
    ERROR_STATUS = "ERROR"

    ENDPOINTS = { # TODO: should get this from the settings
        "list": "performanceList",
        "availability": "performanceAvailability"
    }

    #
    # Initialisation methods
    #
    def __init__(self, api_settings):
        if api_settings and isinstance(api_settings, dict):
            self.api_settings = self.validate_settings(api_settings)
        else:
            self.raise_request_setup_error("Required API settings are not found or have an invalid format.")

        self.api_mode = api_settings['api_mode']
        # TODO: endpoints should be validated

    #
    # CRUD operations
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
        ## TODO
        return []

    def get_performance_list_by_season(season):
        ## TODO
        return []

    def get_performance_availability(self, performance_id):
        # 
        # Request the performance availability from the Ticketworks API
        # Requires: performance_id
        #
        params = {"id": performance_id}
        response = self.perform_api_call(self.HTTP_METHOD, endpoint_type='availability', params=params)
        return response

    # 
    # Error handling
    #
    def _raise_request_setup_error(self, message):
        raise RequestSetupError(message)

    def _raise_request_error(self, message):
        raise RequestError(message)

    def _raise_unknown_error(self, message):
        raise UnkownError(message)

    def _raise_response_handling_error(self, message):
        raise ResponseHandlingError(message)

    def _raise_performance_not_found_error(self, message):
        raise PerformanceNotFoundError(message)

    def raise_error(self, error_type, message):
        switcher = {
            'requestSetupError': self._raise_request_setup_error,
            'requestError': self._raise_request_error,
            'requestHandlingError': self._raise_response_handling_error,
            'performanceNotFoundError': self._raise_performance_not_found_error
        }

        error_handler = switcher.get(error_type, None)

        if error_handler:
            error_handler(message)
        else:
            self._raise_unknown_error(message)

    # 
    # Validaton methods
    #
    def validate_settings(self, api_settings):
        for environment in self.ENVIRONMENTS:
            if environment not in api_settings:
                self.raise_error("requestSetupError", "Details for the environment '%s' are not available in the API settings" %(environment))
            else:
                env = self.validate_environment(environment, api_settings[environment])

        api_mode = api_settings.get('api_mode', None)
        if not api_mode:
            self.raise_error("requestSetupError", "Required API mode cannot be found in the settings.")
        else:
            self.validate_api_mode(api_mode)

        return api_settings

    def validate_environment(self, environment_name, environment):
        if environment:
            url = environment.get('url', None)
            api_key = environment.get('api_key', None)
            
            if not url:
                self.raise_error("requestSetupError", "Required URL for the environment '%s' cannot be found" %(environment_name))
            else:
                self.validate_url(url)
            
            if not api_key:
                self.raise_error("requestSetupError", "Required API key for the environment '%s' cannot be found" %(environment_name))
            else:
                self.validate_api_key(api_key)

            return environment
        else:
            self.raise_error("requestSetupError", "Required details for the environment '%s' are not available in the API settings" %(environment_name))
            
    def validate_url(self, url):
        if re.match(self.URL_REGEX, url) is not None:
            return url
        else:
            self.raise_error("requestSetupError", "URL '%s' is not valid." %(url))

    def validate_api_key(self, api_key):
        if api_key and isinstance(api_key, basestring):
            api_key_split = api_key.split('-')
            if len(api_key_split) != self.API_KEY_SIZE:
                self.raise_error("requestSetupError", "API key '%s' is not valid." %(api_key))
        else:
            self.raise_error("requestSetupError", "API key '%s' is not valid." %(api_key))
        
        return api_key

    def validate_api_mode(self, api_mode):
        if api_mode and isinstance(api_mode, basestring):
            if api_mode not in self.ENVIRONMENTS:
                self.raise_error("requestSetupError", "API mode '%s' is not valid." %(api_mode))
        else:
            self.raise_error("requestSetupError", "API mode '%s' is not valid." %(api_mode))

        return api_mode

    def validate_parameters(self, endpoint_type, params):
        # TODO:
        # if not valid self.raise_request_setup_error("API call parameters are not valid." %(url))
        return params

    # 
    # API call methods
    #
    def _format_request_data(self, endpoint_type, params):
        params['key'] = self.api_settings[self.api_mode]['api_key']
        querystring = generate_querystring(params)

        url = self.api_settings[self.api_mode]['url']

        if endpoint_type:
            url = "%s/%s" %(url, self.ENDPOINTS[endpoint_type])

        if querystring:
            url += '?' + querystring
            params = None

        return url

    def perform_http_call(self, http_method, endpoint_type=None, params=None):
        try:
            url = self._format_request_data(endpoint_type, params)

            response = requests.request(
                http_method, url,
                headers={
                    'Accept': 'application/json',
                    'Content-Type': 'application/json',
                    'User-Agent': 'Mozilla/5.0',
                },
                timeout=self.TIMEOUT
            )
        except Exception as err:
            self.raise_error("requestError", 'Unable to communicate with TWT API: {error}'.format(error=err))

        return response

    def perform_api_call(self, http_method, endpoint_type=None, params=None):

        params = self.validate_parameters(endpoint_type, params)
        resp = self.perform_http_call(http_method, endpoint_type='availability', params=params)

        try:
            result = resp.json() if resp.status_code != 204 else {}
        except Exception:
            self.raise_error("requestHandlingError",
                "Unable to decode TWT API response (status code: {status}): '{response}'.".format(
                    status=resp.status_code, response=resp.text))

        if 'status' in result:
            status = result['status']
            if status == self.NOT_FOUND_STATUS:
                self.raise_error("performanceNotFoundError", 
                    "Received HTTP error from TWT API, performance was not found. (status code: {status}): '{response}'.".format(
                        status=resp.status_code, response=resp.text))

            elif status == self.ERROR_STATUS:
                error_msg = result['error']
                self.raise_error("responseHandlingError", 
                    "Received and ERROR status from the TWT API. Error message: '{error_message}'.".format(error_message=error_msg))
            else:
                return result
        else:
            self.raise_error("responseHandlingError", 
                    "Received HTTP error from TWT API, but no status in payload "
                    "(status code: {status}): '{response}'.".format(
                        status=resp.status_code, response=resp.text))
        return result
    

