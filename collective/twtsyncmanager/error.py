# -*- coding: utf-8 -*-
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

class UnkownError(Error):
    """Errors while preparing or performing an API request."""
    pass

class ValidationError(Error):
    """Errors while preparing or performing an API request."""
    pass

class RequestSetupError(RequestError):
    """Errors while preparing an API request."""
    pass

class ResponseHandlingError(Error):
    """Errors related to handling the response from the API."""
    pass


class PerformanceNotFoundError(Error):
    """Errors related to handling the response from the API."""
    pass

# 
# Error handling
#
def _raise_request_setup_error(message):
    raise RequestSetupError(message)

def _raise_request_error(message):
    raise RequestError(message)

def _raise_unknown_error(message):
    raise UnkownError(message)

def _raise_response_handling_error(message):
    raise ResponseHandlingError(message)

def _raise_performance_not_found_error(message):
    raise PerformanceNotFoundError(message)

def raise_error(error_type, message):
    switcher = {
        'requestSetupError': _raise_request_setup_error,
        'requestError': _raise_request_error,
        'requestHandlingError': _raise_response_handling_error,
        'performanceNotFoundError': _raise_performance_not_found_error
    }

    error_handler = switcher.get(error_type, None)

    if error_handler:
        error_handler(message)
    else:
        _raise_unknown_error(message)




