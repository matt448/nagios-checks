#!/usr/bin/python

#########################################
# Notes
#########################################
#
# Written by Matthew McMillan
# matthew.mcmillan@gmail.com
# @matthewmcmillan
# https://matthewcmcmillan.blogspot.com
# https://github.com/matt448/nagios-checks
#
# Nagios error codes
# 0 = OK
# 1 = WARNING
# 2 = CRITICAL
# 3 = UNKNOWN
#
# This check template uses a JSON test website (http://www.jsontest.com/)
# as an example webservice. Please change this to fit your needs.
#
# This is only an example/template. This check is not useful unless it 
# is customized for your environment and webservice. 
#
# Nagios dev guidelines
# http://nagiosplug.sourceforge.net/developer-guidelines.html
#
#


import sys
import json
import argparse
#from datetime import datetime, time, timedelta
import httplib, urllib, urllib2
from urllib2 import Request, urlopen, URLError, HTTPError
from pprint import pprint

#Variables
useragent = 'Nagios/3.2.3'
apipath = '/?json={"key1":"value1","key2":"value2","key3":"value3"}' 

#Parse command line arguments
parser = argparse.ArgumentParser(description='This is a template Nagios check that verifies a \
                                              webservice is functioning and parses the returned JSON data. \
                                              JSON data can be checked for values and alerted on. \
                                              Perfdata is also generated for JSON values.')

parser.add_argument('--host', dest='host', type=str, required=True, 
                    help='Hostname or IP address of api server. For this template use validate.jsontest.com')

parser.add_argument('--maxsize', dest='maxsize', type=int, default=20,
                    help='Maximum number for some JSON value. Default is is 20.')

parser.add_argument('--maxtime', dest='maxtime', type=float, default=0.7,
                    help='Maximum parse time in milliseconds. Default is is 0.7.')

parser.add_argument('--debug', action='store_true',
                    help='Enable debug output.')

parser.add_argument('--ssl', action='store_true',
                     help='Enable https/ssl communication with api server')

args = parser.parse_args()


#Assign variables from command line arguments
host = args.host
maxsize = args.maxsize
maxtime = args.maxtime


if (args.debug):
        print '########## START DEBUG OUTPUT ############'
        print 'HOST: ' + host
        print 'MAXSIZE: ' + str(maxsize)
        print 'MAXTIME: ' + str(maxtime) + ' milliseconds'
        if (args.ssl):
                print 'SSL: Encrypted communication enabled.'
        else:
                print 'SSL: Encrypted communication NOT enabled.'


#Turn on https URL if the --ssl arg is passed
if (args.ssl):
        url = 'https://' + host + apipath
	if (args.debug):
		print "URL: " + url
else:
        url = 'http://' + host + apipath
	if (args.debug):
		print "URL: " + url


#Set custom User-Agent string
headers = { 'User-Agent' : useragent }

# Build request string 
req = urllib2.Request(url, None, headers)


# Handle http error responses from server.
try:
        response = urllib2.urlopen(req)
except HTTPError as e:
        errorcode = e.code
        msg = 'Server couldn\'t fulfill the request.'
        msg += ' http_error_code=' + str(errorcode) + ' host=' + host
	perfdatamsg = ''
        exitcode = 2
except URLError as e:
        errorreason = e.reason
        msg = 'We failed to reach a server.' + str(errorreason) + ' host=' + host
	perfdatamsg = ''
        exitcode = 2
else:
        jsondata = response.read() #Read JSON data from web site
        data = json.loads(jsondata) #Load JSON data into a dict
	parse_time = float(float(data['parse_time_nanoseconds'])/1000000)
	size = data['size']
	if (args.debug):
		print 'START JSON OUTPUT:'
		print '----------------------------------'
		pprint(data)
		print '----------------------------------'
		print 'END JSON OUTPUT'
		print 'PARSE TIME: ' + str(parse_time) + ' Milliseconds'
		print 'SIZE: ' + str(size)
	#Evaluate returned data for maximums
	if (parse_time < maxtime) and (size < maxsize):
		exitcode = 0
		msg = 'Parse time and size within limits.'
	elif (parse_time >= maxtime) and (size < maxsize):
		exitcode = 1
		msg = 'Maximum parse time exceeded.'
	elif (parse_time < maxtime) and (size >= maxsize):
		exitcode = 1
		msg = 'Maximum size exceeded.'
	elif (parse_time >= maxtime) and (size >= maxsize):
		exitcode = 1
		msg = 'Both parse time and size have exceeded maximum values.'
	else:
		exitcode = 3
		msg = 'Status unknown.'

	# Additional output for status message
	msg += ' parse_time=' + str(parse_time) + 'ms'
	msg += ' size=' + str(size)
	msg += ' host=' + host

        perfdatamsg = 'size=' + str(size) + ';0;0 '
        perfdatamsg += 'parse_time=' + str(parse_time) + 'ms;0;0 '

#Generate final output for Nagios message
if (exitcode == 0):
        statusline = 'OK: ' + msg + '|' + perfdatamsg
elif (exitcode == 1):
        statusline = 'WARNING: ' + msg + '|' + perfdatamsg
elif (exitcode == 2):
        statusline = 'CRITICAL: ' + msg + '|' + perfdatamsg
else:
        statusline = 'UNKNOWN: ' + msg + '|' + perfdatamsg
        exitcode = 3


if (args.debug):
        print '########## END DEBUG OUTPUT ##############'
        print ' '
 
 
#Print Nagios status message
print statusline
exit(exitcode)



