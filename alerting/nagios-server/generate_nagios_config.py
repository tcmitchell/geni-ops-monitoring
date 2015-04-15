#!/usr/bin/env python
#----------------------------------------------------------------------
# Copyright (c) 2014-2015 Raytheon BBN Technologies
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and/or hardware specification (the "Work") to
# deal in the Work without restriction, including without limitation the
# rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Work, and to permit persons to whom the Work
# is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Work.
#
# THE WORK IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
# OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE WORK OR THE USE OR OTHER DEALINGS
# IN THE WORK.
#----------------------------------------------------------------------

import json
import sys
import getopt
import os
import requests


nagios_server_path = os.path.abspath(os.path.dirname(__file__))
alerting_path = os.path.dirname(nagios_server_path)
top_path = os.path.dirname(alerting_path)
common_path = os.path.join(top_path, "common")
config_path = os.path.join(top_path, "config")
sys.path.append(common_path)

import table_manager
import logger
import multiprocessing.pool


__THREAD_POOL_SIZE = 6

opslogger = logger.get_logger(config_path)


def usage():
    sys.stderr.write('generate_nagios_config.py -c </cert/path/cert.pem> [-u <opsconfig store url>] [-f <output_file>]\n')
    sys.stderr.write('   -c | --certificate= </cert/path/cert.pem> specifies the path to the certificate file\n')
    sys.stderr.write('   -u | --opsconfig_url= <opsconfig store url> specifies the URL of the opsconfig data store to get the list of aggregate from\n')
    sys.stderr.write('                         By default uses the local opsconfig.json to find the location\n')
    sys.stderr.write('   -f | --file= <output_file> specifies the path of the output nagios file\n')
    sys.stderr.write('                              By default uses nagios.cfg\n')
    sys.exit(1)

def parse_args(argv):
    if argv == []:
        usage()

    cert_path = None
    opsconfig_url = None
    output_file = None

    try:
        opts, _ = getopt.getopt(argv, "hc:u:f:", ["help", "certificate=", "opsconfig_url=", "file="])
    except getopt.GetoptError:
        usage()

    for opt, arg in opts:
        if opt in ("-h", "--help"):
            usage()
        elif opt in ("-c", "--certificate"):
            cert_path = arg
        elif opt in ("-u", "--opsconfig_url"):
            opsconfig_url = arg
        elif opt in ("-f", "--file"):
            output_file = arg
        else:
            usage()

    if opsconfig_url is None:
        # get the opsconfig URL from the local opsconfig.json
        from opsconfig_loader import OpsconfigLoader
        configLoader = OpsconfigLoader(config_path)
        opsconfig_url = configLoader.config_json['selfRef']

    if output_file is None:
        output_file = 'nagios.cfg'

    return (cert_path, opsconfig_url, output_file)

def handle_request(logger, cert_path, url):
    http_headers = {'Connection':'close'}
    resp = None
    try:
        resp = requests.get(url, verify=False, cert=cert_path, headers=http_headers)
    except Exception, e:
        opslogger.warning("No response from datastore at: " + url)
        opslogger.warning(e)
        return None

    if resp:
        try:
            json_dict = json.loads(resp.content)
        except Exception, e:
            opslogger.warning("Could not load response from " + url + " into JSON")
            opslogger.warning(e)
            return None

        return json_dict
    else:
        opslogger.warning("could not reach datastore at " + url)
        return None


CONFIG_HEADER = '''
define contactgroup{
    contactgroup_name    group_nobody
    alias    group with nobody
}

define command{
    command_name    no_command
    command_line    ""
}

define contact{
    contact_name    nobody
    host_notifications_enabled    0
    service_notifications_enabled    0
    host_notification_period    24x7
    service_notification_period    24x7
    host_notification_options    n
    service_notification_options    n
    host_notification_commands    no_command
    service_notification_commands    no_command
}

define hostgroup{
    hostgroup_name    geni_aggregates
    alias    GENI Aggregates
#    members    hosts
#    hostgroup_members    hostgroups
    notes    This group list all the nagios hosts that corresponds to GENI aggregates, Stitching Computation Services (SCS), GENI authorities and external checkers
#    notes_url    url
#    action_url    url
}


'''

HOST_SECTION = '''
define host{
    host_name    %s
    alias    %s
    #parents    host_names
    hostgroups    geni_aggregates
    initial_state    o
    max_check_attempts    1
    active_checks_enabled    0
    passive_checks_enabled    1
    check_period    24x7
    flap_detection_enabled     0
    contacts    nobody
    contact_groups    group_nobody
    notification_interval    0
    notification_period    24x7
    notes    %s
}
'''

AGGREGATE_HOST_DESCRIPTION = "This nagios host represents the Aggregate Manager known via its GENI URN: %s"

STITCHING_HOST_DESCRIPTION = "This nagios host represents a Stitching Computation Service available at the following URL(s): %s"

AUTHORITY_HOST_DESCRIPTION = "This nagios host represents the clearing house authority known via its GENI URN: %s"

EXTCK_HOST_DESCRIPTION = "This nagios host represents the %s external check data store"

SERVICE_SECTION = '''
define service{
    host_name    %s
    service_description    %s
#    display_name    display_name
#    parents    service_descriptions
#    hourly_value    #
    check_command    no_command
    initial_state    o
    max_check_attempts    1
    check_interval    15
    retry_interval    30
    active_checks_enabled    0
    passive_checks_enabled    1
    check_period    24x7
    flap_detection_enabled     0
    notification_interval    #
    notification_period    24x7
    notifications_enabled    0
    contacts    nobody
    contact_groups    group_nobody
    notes    %s
}
'''

IS_AVAILABLE_SERVICE_DESCRIPTION = "This nagios service represents whether an ops monitoring external check has been able to contact the Aggregate Manager API \
(or the SCS) and managed to successfully issue a listresources command"

IS_RESPONSIVE_SERVICE_DESCRIPTION = "This nagios service represents whether the data store has been responding to \
the collector requests"

def get_aggregate_info((cert_path, url)):
    return handle_request(opslogger, cert_path, url)


def find_aggregate_in_list(agg_urn, aggStores):
    for aggregate in aggStores:
        if agg_urn == aggregate['urn']:
            return aggregate
    return None

def get_am_urls(aggregate):
    url_list = list()
    for key in aggregate.keys():
        if key.startswith("amurl"):
            url_list.append(aggregate[key])
    return url_list

def main(argv):
    (cert_path, opsconfig_url, output_file) = parse_args(argv)
    pool = multiprocessing.pool.ThreadPool(processes=__THREAD_POOL_SIZE)
    of = open(output_file, 'w')
    aggRequest = handle_request(opslogger, cert_path, opsconfig_url)
    if aggRequest == None:
        opslogger.warning("Could not not contact opsconfigdatastore at %s" % opsconfig_url)
        return
    aggStores = aggRequest['aggregatestores']
    extckStores = aggRequest['externalcheckstores']
    authorityStores = aggRequest['authorities']
    extckStoresResponses = list()
    for extckStore in extckStores:
        url = extckStore['href']
        extckStoreResponse = handle_request(opslogger, cert_path, url)
        if extckStoreResponse == None:
            opslogger.warning("Could not not contact external check store at %s" % url)
        else:
            extckStoresResponses.append(extckStoreResponse)

    authorityStoreResponses = list()
    for authorityStore in authorityStores:
        url = authorityStore['href']
        authorityStoreResponse = handle_request(opslogger, cert_path, url)
        if authorityStoreResponse == None:
            opslogger.warning("Could not not contact external check store at %s" % url)
        else:
            authorityStoreResponses.append(authorityStoreResponse)

    argsArray = list()
    for aggregate in aggStores:
        args = (cert_path, aggregate['href'])
        argsArray.append(args)
    results = pool.map(get_aggregate_info, argsArray)

    of.write(CONFIG_HEADER)
    aggregateDict = dict()
    for res in results:
        if res is not None:
            agg_urn = res['urn']
            aggregate = find_aggregate_in_list(agg_urn, aggStores)
            if aggregate['amtype'] == "stitcher":
                url_list = get_am_urls(aggregate)
                urls = ""
                first = True
                for url in url_list:
                    if first:
                        first = False
                    else :
                        urls += ", "
                    urls += url
                hostDesc = STITCHING_HOST_DESCRIPTION % (urls,)
            else:
                hostDesc = AGGREGATE_HOST_DESCRIPTION % (agg_urn,)
            of.write(HOST_SECTION % (res['id'], res['id'], hostDesc))
            of.write('\n')
            of.write(SERVICE_SECTION % (res['id'], 'is_responsive', IS_RESPONSIVE_SERVICE_DESCRIPTION))
            of.write('\n')
            aggregateDict[res['id']] = res


    for extckStoreResponse in extckStoresResponses:
        extckHostDesc = EXTCK_HOST_DESCRIPTION % (extckStoreResponse['id'],)
        of.write(HOST_SECTION % (extckStoreResponse['id'], extckStoreResponse['id'], extckHostDesc))
        of.write('\n')
        of.write(SERVICE_SECTION % (extckStoreResponse['id'], 'is_responsive', IS_RESPONSIVE_SERVICE_DESCRIPTION))
        of.write('\n')
        mon_aggregates = extckStoreResponse['monitored_aggregates']
        extck_id = extckStoreResponse['id']
        for mon_agg in mon_aggregates:
            agg_id = mon_agg['id']
            if agg_id in aggregateDict.keys():
                of.write(SERVICE_SECTION % (agg_id, extck_id + ":is_available", IS_AVAILABLE_SERVICE_DESCRIPTION))
                of.write('\n')

    for authorityStoreResponse in authorityStoreResponses:
        authorityHostDesc = AUTHORITY_HOST_DESCRIPTION % (authorityStoreResponse['urn'],)
        of.write(HOST_SECTION % (authorityStoreResponse['id'], authorityStoreResponse['id'], authorityHostDesc))
        of.write('\n')
        of.write(SERVICE_SECTION % (authorityStoreResponse['id'], 'is_responsive', IS_RESPONSIVE_SERVICE_DESCRIPTION))
        of.write('\n')

    of.close()


if __name__ == "__main__":
    main(sys.argv[1:])
