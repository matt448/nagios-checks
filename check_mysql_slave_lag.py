#!/usr/bin/python

##########################################################
#
# Written by Matthew McMillan
# matthew.mcmillan@gmail.com
# @matthewmcmillan
# https://matthewcmcmillan.blogspot.com
# https://github.com/matt448/nagios-checks
#
#

import sys
import argparse
import MySQLdb

def printUsage():
    print
    print "Example:    ", sys.argv[0], "--user myusername --pass mypassword --warn 10 --crit 20"
    print

#Parse command line arguments
parser = argparse.ArgumentParser(description='This script is a Nagios check that \
                                    monitors the number of seconds a mysql slave \
                                    is lagging behind a master.') \

parser.add_argument('--user', dest='user', type=str, required=True,
                        help='Mysql db user name that has can run the \
                              command SHOW SLAVE STATUS.')

parser.add_argument('--passwd', dest='passwd', type=str, default='',
                        help='Mysql password.')

parser.add_argument('--host', dest='host', type=str, default='localhost',
                        help='Mysql server hostname.')

parser.add_argument('--warn', dest='warn', type=int, required=True,
                        help='Warning level for lag in seconds.')

parser.add_argument('--crit', dest='crit', type=int, required=True,
                        help='Critical level for lag in seconds.')

parser.add_argument('--debug', action='store_true', help='Enable debug output.')

args = parser.parse_args()

# Assign command line args to variable names
dbuser = args.user
dbpass = args.passwd
dbhost = args.host
warn = args.warn
crit = args.crit

if crit <= warn:
    print
    print "ERROR: Critical value must be larger than warning value."
    printUsage()
    exit(2)


statusMsg = ""
msgLine = ""
perfdataMsg = ""
replicationfailed = False
exitCode = 3


#Make connection to the Mysql server
db=MySQLdb.connect(host=dbhost,db="",user=dbuser,passwd=dbpass)
c=db.cursor()


#Execute slave status command and get the data
c.execute("""SHOW SLAVE STATUS""")
row = c.fetchone()
if args.debug:
    print row

#Close the db connection
c.close()

#Extract the lag value. Should be position 32 in the list
lag_seconds = row[32]

# I didn't like the previous way of handling failed replication
# because it skewed the stats. Now if repication fails we will
# set the value to zero and flag replication as failed.
if lag_seconds is None:
    lag_seconds = 0
    replicationfailed = True
else:
    lag_seconds = int(lag_seconds)

# Set exit code based on amount of lag
if lag_seconds < warn and not replicationfailed:
    statusMsg = "OK - Replication Lag " + str(lag_seconds) + " seconds"
    exitCode = 0
elif lag_seconds >= warn and lag_seconds < crit and not replicationfailed:
    statusMsg = "WARNING - Replication Lag " + str(lag_seconds) + " seconds"
    exitCode = 1
elif lag_seconds >= crit and not replicationfailed:
    statusMsg = "CRITICAL - Replication Lag " + str(lag_seconds) + " seconds"
    exitCode = 2
elif replicationfailed:
    statusMsg = "CRITICAL - Replication Failed"
    exitCode = 2
else:
    statusMsg = "UNKNOWN - Replication Lag " + str(lag_seconds) + " seconds"
    exitCode = 3

perfdataMsg = "lag_seconds=" + str(lag_seconds) + ";" + str(warn) + ";" + str(crit) + "; "


# Print final output for Nagios
print statusMsg + "|" + perfdataMsg

# Exit with appropriate code
exit(exitCode)
