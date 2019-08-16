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

class RequestSetupError(RequestError):
    """Errors while preparing an API request."""
    pass

class ResponseHandlingError(Error):
    """Errors related to handling the response from the API."""
    pass


class PerformanceNotFoundError(Error):
    """Errors related to handling the response from the API."""
    pass
