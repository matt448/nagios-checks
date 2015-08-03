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
# This Nagios check looks at the status of nodes in a RabbitMQ cluster
# and alerts if any node is not running or the minimum number of nodes
# is not present in the cluster. This check only needs to be run on one
# node in the cluster.
#
# Requires the rabbitmqadmin command to be installed. Edit rabbitmqadminCmd
# if the rabbitmqadmin command isn't in /usr/local/bin.
#

import sys
import re
import argparse
import json
from pprint import pprint
from subprocess import check_output
from subprocess import check_call

def printUsage():
    print
    print "Example:    ", sys.argv[0], "--host somehost --port 15672 --minnodes 2"
    print

#Parse command line arguments
parser = argparse.ArgumentParser(description='This script is a Nagios check that \
                                    monitors nodes in a rabbitMQ cluster.')

parser.add_argument('--host', dest='host', type=str, required=True,
                        help='Hostname of rabbitmq server.')

parser.add_argument('--port', dest='port', type=int, required=True,
                        help='Port number for rabbitmqadmin http management interface.')

parser.add_argument('--minnodes', dest='minnodes', type=int, required=True,
                        help='Minimum number of nodes required in the cluster.')

parser.add_argument('--debug', action='store_true', help='Enable debug output.')

args = parser.parse_args()

# Assign command line args to variable names
hostName = args.host
portNum = args.port
minNodes = args.minnodes


rabbitmqadminCmd = '/usr/local/bin/rabbitmqadmin'
responseData = []
depthList = []
statusMsgList = []
statusMsg = ""
msgLine = ""
perfdataMsg = ""
warnCount = 0
critCount = 0
exitCode = 3

#Run rabbitmqctl command to dump list of queues
output=check_output([rabbitmqadminCmd, "list", "nodes", "--format=raw_json", "--port="+str(portNum), "--host="+hostName ])
if args.debug:
    print '----------------OUTPUT------------------'
    print str(output)
    print '----------------------------------------'


##########################################
#Parse the JSON data and put it in a dict
responseData = json.loads(output)


###########################################
# Find number of nodes and compare against
# the minnodes value
nodeCount = len(responseData)
if args.debug:
    print 'NUMBER OF NODES: '+str(nodeCount)
if nodeCount < minNodes:
    if args.debug:
        print 'ERROR: only ' + str(nodeCount) + ' of ' + str(minNodes) + ' nodes found'
    statusMsgList.append('[CRIT: ' + str(nodeCount) + ' of ' + str(minNodes) + ' Nodes found]')
    critCount += 1 #Increment critCount to indicate error state
else:
    statusMsgList.append('[OK: ' + str(nodeCount) + ' of ' + str(minNodes) + ' Nodes found]')


##################################################
# Loop through the nodes in the responseData and
# check the running state for each.
for node in responseData:
    if args.debug:
        print node['name'] + ': ' + str(node['running']);
    if not node['running']:
        critCount += 1 #Increment critCount to indicate error state
        #Add node status to output message list
        statusMsgList.append('[NODE:' + node['name'] + ' STATUS:*NOT RUNNING*]')
    else:
        statusMsgList.append('[NODE:' + node['name'] + ' STATUS:running]')



# Set exit code based on number of warnings and criticals
if warnCount == 0 and critCount == 0:
    statusMsgList.insert(0, "OK - RabbitMQ Cluster")
    exitCode = 0
elif warnCount > 0 and critCount == 0:
    statusMsgList.insert(0, "WARNING - RabbitMQ Cluster")
    exitCode = 1
elif critCount > 0:
    statusMsgList.insert(0, "CRITICAL - RabbitMQ Cluster")
    exitCode = 2
else:
    statusMsgList.insert(0, "UNKNOWN - RabbitMQ Cluster")
    exitCode = 3

# Build status message output
for msg in statusMsgList:
    statusMsg += msg + " "


# Build perfdata output
#for index in range(len(qList)):
#    perfdataMsg += qList[index] + "=" + str(depthList[index]) + ";" + str(warnDepth) + ";" + str(critDepth) + "; "


# Print final output for Nagios
print statusMsg + "|" + perfdataMsg

# Exit with appropriate code
exit(exitCode)
