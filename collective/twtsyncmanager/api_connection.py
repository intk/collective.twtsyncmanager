#!/usr/bin/python
# -*- coding: utf-8 -*-


#
# Ticketworks API sync mechanism by Andre Goncalves
#

# Global dependencies
import re
import requests
import sys
from datetime import datetime

try:
    from urllib.parse import urlencode
except ImportError:
    # support python 2
    from urllib import urlencode

# Product dependencies
from .error import raise_error


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
            raise_error("requestSetupError", "Required API settings are not found or have an invalid format.")

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

    def get_performance_list_by_date(self, date_from, date_until):
        #
        # Request the performance list from the Ticketworks API
        # Requires: dateFrom and dateUntil in the format YYYY-MM-DD
        #
        date_from = self.validate_date(date_from)
        date_until = self.validate_date(date_until)
        
        params = {"dateFrom": date_from, "dateUntil": date_until}
        response = self.perform_api_call(self.HTTP_METHOD, endpoint_type='list', params=params)

        if 'performances' in response:
            return response['performances']
        else:
            raise_error("requestHandlingError", "Performance list is not available in the TWT API response.")

    def get_performance_list_by_season(self, season):
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
    # Validaton methods
    #
    def validate_settings(self, api_settings):
        for environment in self.ENVIRONMENTS:
            if environment not in api_settings:
                raise_error("requestSetupError", "Details for the environment '%s' are not available in the API settings" %(environment))
            else:
                env = self.validate_environment(environment, api_settings[environment])

        api_mode = api_settings.get('api_mode', None)
        if not api_mode:
            raise_error("requestSetupError", "Required API mode cannot be found in the settings.")
        else:
            self.validate_api_mode(api_mode)

        return api_settings

    def validate_environment(self, environment_name, environment):
        if environment:
            url = environment.get('url', None)
            api_key = environment.get('api_key', None)
            
            if not url:
                raise_error("requestSetupError", "Required URL for the environment '%s' cannot be found" %(environment_name))
            else:
                self.validate_url(url)
            
            if not api_key:
                raise_error("requestSetupError", "Required API key for the environment '%s' cannot be found" %(environment_name))
            else:
                self.validate_api_key(api_key)

            return environment
        else:
            raise_error("requestSetupError", "Required details for the environment '%s' are not available in the API settings" %(environment_name))
            
    def validate_url(self, url):
        if re.match(self.URL_REGEX, url) is not None:
            return url
        else:
            raise_error("requestSetupError", "URL '%s' is not valid." %(url))

    def validate_date(self, date):
        # Valid date: yyyy-mm-dd
        try:
            datetime_date = datetime.strptime(date, '%Y-%m-%d')
            return date
        except:
            raise_error("requestSetupError", "The date '%s' is not valid. Date format: yyyy-mm-dd" %(date))

    def validate_api_key(self, api_key):
        if api_key and isinstance(api_key, basestring):
            api_key_split = api_key.split('-')
            if len(api_key_split) != self.API_KEY_SIZE:
                raise_error("requestSetupError", "API key '%s' is not valid." %(api_key))
        else:
            raise_error("requestSetupError", "API key '%s' is not valid." %(api_key))
        
        return api_key

    def validate_api_mode(self, api_mode):
        if api_mode and isinstance(api_mode, basestring):
            if api_mode not in self.ENVIRONMENTS:
                raise_error("requestSetupError", "API mode '%s' is not valid." %(api_mode))
        else:
            raise_error("requestSetupError", "API mode '%s' is not valid." %(api_mode))

        return api_mode

    # 
    # API call methods
    #
    def _format_request_data(self, endpoint_type, params):
        params['key'] = self.get_api_key()
        querystring = generate_querystring(params)

        url = self.get_api_url()

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
            raise_error("requestError", 'Unable to communicate with TWT API: {error}'.format(error=err))

        return response

    def perform_api_call(self, http_method, endpoint_type=None, params=None):
        resp = self.perform_http_call(http_method, endpoint_type=endpoint_type, params=params)

        try:
            result = resp.json() if resp.status_code != 204 else {}
        except Exception:
            raise_error("requestHandlingError",
                "Unable to decode TWT API response (status code: {status}): '{response}'.".format(
                    status=resp.status_code, response=resp.text))

        if 'status' in result:
            status = result['status']
            if status == self.NOT_FOUND_STATUS:
                raise_error("performanceNotFoundError", 
                    "Received HTTP error from TWT API, performance was not found. (status code: {status}): '{response}'.".format(
                        status=resp.status_code, response=resp.text))

            elif status == self.ERROR_STATUS:
                error_msg = result['error']
                raise_error("responseHandlingError", 
                    "Received and ERROR status from the TWT API. Error message: '{error_message}'.".format(error_message=error_msg))
            else:
                return result
        else:
            raise_error("responseHandlingError", 
                    "Received HTTP error from TWT API, but no status in payload "
                    "(status code: {status}): '{response}'.".format(
                        status=resp.status_code, response=resp.text))
        return result
    

