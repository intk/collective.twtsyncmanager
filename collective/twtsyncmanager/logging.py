# -*- coding: utf-8 -*-



def log_csv(message, err):
	return ""

def log_sentry(message, err):
	return ""

def logger(message, err):
    log_csv(message, err)
    log_sentry(message, err)
    print "%s. Exception message: %s" %(message, err)