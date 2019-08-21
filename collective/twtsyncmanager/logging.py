# -*- coding: utf-8 -*-

print_warnings = True
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

    if print_message and '[Status]' not in message:
    	print "%s Exception: %s" %(message, err)
    else:
    	print "%s" %(message)