# -*- coding: utf-8 -*-

from datetime import datetime
print_warnings = False
print_errors = True
print_status = True

def log_csv(message, err):
    """
    Log format:
    datetime, type_error, message, exception
    """
    return ""

def log_sentry(message, err):
    return ""

def logger(message, err=""):
    log_csv(message, err)
    log_sentry(message, err)

    print_message = False
    if '[Error]' in message and print_errors:
        print_message = True

    elif '[Status]' in message and print_status:
        print_message = True

    elif '[Warning]' in message and print_warnings:
        print_message = True
    else:
        print_message = False

    timestamp = datetime.today().isoformat()
    if print_message:
        if '[Status]' not in message:
            print "[%s] %s Exception: %s" %(timestamp, message, err)
        else:
            print "[%s] %s" %(timestamp, message)
    else:
        pass
