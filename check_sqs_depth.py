#!/usr/bin/python

##########################################################
#
# Written by Matthew McMillan
# matthew.mcmillan@gmail.com
# @matthewmcmillan
# https://matthewcmcmillan.blogspot.com
# https://github.com/matt448/nagios-checks
#
# Requires the boto library and a .boto file with read
# permissions to the queues.
# 

import sys
import argparse
import boto
import boto.sqs

def printUsage():
    print
    print "Example:    ", sys.argv[0], "--name myqueue --region us-east-1 --warn 10 --crit 20"
    print

#Parse command line arguments
parser = argparse.ArgumentParser(description='This script is a Nagios check that \
                                    monitors the number of messages in Amazon SQS \
                                    queues. It requires a .boto file in the user\'s \
                                    home directroy and AWS credentials that allow \
                                    read access to the queues that are to be monitored.')

parser.add_argument('--name', dest='name', type=str, required=True,
                        help='Name of SQS queue. This can be a wildcard match. \
                              For example a name of blah_ would match blah_1, \
                              blah_2, blah_foobar. To monitor a single queue, enter \
                              the exact name of the queue.')
                                                      
parser.add_argument('--region', dest='region', type=str, default='us-east-1',
                        help='AWS Region hosting the SQS queue. \
                              Default is us-east-1.')
                                                      
parser.add_argument('--warn', dest='warn', type=int, required=True, 
                        help='Warning level for queue depth.')

parser.add_argument('--crit', dest='crit', type=int, required=True, 
                        help='Critical level for queue depth.')

parser.add_argument('--debug', action='store_true', help='Enable debug output.')

args = parser.parse_args()

# Assign command line args to variable names
queueName = args.name
sqsRegion = args.region
warnDepth = args.warn
critDepth = args.crit

if critDepth <= warnDepth:
    print
    print "ERROR: Critical value must be larger than warning value."
    printUsage()
    exit(2)


qList = []
depthList = []
statusMsgList = []
statusMsg = ""
msgLine = ""
perfdataMsg = ""
warnCount = 0
critCount = 0
exitCode = 3 

# Make SQS connection
conn = boto.sqs.connect_to_region(sqsRegion)
rs = conn.get_all_queues(prefix=queueName)

# Loop through each queue and get message count
# Push the queue name and depth to lists
for qname in rs:
    namelist = str(qname.id).split("/") # Split out queue name 
    qList.append(namelist[2])
    depthList.append(int(qname.count()))

if args.debug:
    print
    print '========== Queue List ============='
    print qList
    print '=================================='
    print

# Build status message and check warn/crit values
for index in range(len(qList)):
    if depthList[index] >= warnDepth and depthList[index] < critDepth:
        warnCount += 1
    if depthList[index] >= critDepth:
        critCount += 1
    #print index, ": ", qList[index], depthList[index]
    msgLine = qList[index] + ":" + str(depthList[index]) 
    statusMsgList.append(msgLine) 

# Set exit code based on number of warnings and criticals
if warnCount == 0 and critCount == 0:
    statusMsgList.insert(0, "OK - Queue depth (")
    exitCode = 0
elif warnCount > 0 and critCount == 0:
    statusMsgList.insert(0, "WARNING - Queue depth (")
    exitCode = 1
elif critCount > 0:
    statusMsgList.insert(0, "CRITICAL - Queue depth (")
    exitCode = 2
else:
    statusMsgList.insert(0, "UNKNOWN - Queue depth (")
    exitCode = 3

# Build status message output
for msg in statusMsgList:
    statusMsg += msg + " "

# Build perfdata output
for index in range(len(qList)):
    perfdataMsg += qList[index] + "=" + str(depthList[index]) + ";" + str(warnDepth) + ";" + str(critDepth) + "; "

# Finalize status message
statusMsg += ") [W:" + str(warnDepth) + " C:" + str(critDepth) + "]"

# Print final output for Nagios
print statusMsg + "|" + perfdataMsg

# Exit with appropriate code
exit(exitCode)
