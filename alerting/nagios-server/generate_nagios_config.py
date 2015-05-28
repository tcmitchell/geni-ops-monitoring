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
    sys.stderr.write('   -i | --input= <input_file> specifies the path of the input nagios file that was generated before\n')
    sys.exit(1)

def parse_args(argv):
    if argv == []:
        usage()

    cert_path = None
    opsconfig_url = None
    output_file = None
    input_file = None

    try:
        opts, _ = getopt.getopt(argv, "hc:u:f:i:", ["help", "certificate=", "opsconfig_url=", "file=", "input="])
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
        elif opt in ("-i", "--input"):
            input_file = arg
        else:
            usage()

    if opsconfig_url is None:
        # get the opsconfig URL from the local opsconfig.json
        from opsconfig_loader import OpsconfigLoader
        configLoader = OpsconfigLoader(config_path)
        opsconfig_url = configLoader.config_json['selfRef']

    if output_file is None:
        output_file = 'nagios.cfg'

    return (cert_path, opsconfig_url, output_file, input_file)

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

HOST_GROUP_GENI_HOSTS = 'hostgrp_geni_hosts'
HOST_GROUP_GENI_AGGREGATES = 'hostgrp_geni_aggregates'
HOST_GROUP_GENI_AUTHORITIES = 'hostgrp_geni_authorities'
HOST_GROUP_GENI_SCSS = 'hostgrp_geni_scss'
HOST_GROUP_GENI_EXTCKS = 'hostgrp_geni_extcks'

SERVICE_GROUP_AVAILABILITY = 'svcgrp_availability'
SERVICE_GROUP_STORE_RESP = 'svcgrp_datastore_resp'
SERVICE_GROUP_DATAPLANE_CONNECTIVITY_CHECK = 'svcgrp_dataplane_conn_check'
SERVICE_GROUP_SCS_PATH_CHECK = 'svcgrp_scs_path_check'

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
    hostgroup_name    %s
    alias    GENI Hosts
#    members    hosts
#    hostgroup_members    hostgroups
    notes    This group list all the nagios hosts that correspond to GENI aggregates, Stitching Computation Services (SCS), GENI authorities and external checkers
#    notes_url    url
#    action_url    url
}

define hostgroup{
    hostgroup_name    %s
    alias    GENI Aggregates
#    members    hosts
#    hostgroup_members    hostgroups
    notes    This group list all the nagios hosts that correspond to GENI aggregates
#    notes_url    url
#    action_url    url
}

define hostgroup{
    hostgroup_name    %s
    alias    GENI Authorities
#    members    hosts
#    hostgroup_members    hostgroups
    notes    This group list all the nagios hosts that correspond to GENI authorities
#    notes_url    url
#    action_url    url
}

define hostgroup{
    hostgroup_name    %s
    alias    GENI Stitching Computation Services
#    members    hosts
#    hostgroup_members    hostgroups
    notes    This group list all the nagios hosts that correspond to GENI Stitching Computation Services (SCS)
#    notes_url    url
#    action_url    url
}

define hostgroup{
    hostgroup_name    %s
    alias    GENI External Checkers
#    members    hosts
#    hostgroup_members    hostgroups
    notes    This group list all the nagios hosts that correspond to GENI external checkers
#    notes_url    url
#    action_url    url
}

define servicegroup{
    servicegroup_name    %s
    alias    GENI aggregates and services availability
#    members    services
#    servicegroup_members    servicegroups
    notes    This group list all the nagios services that checks on the availability of GENI Aggregate Manager APIs and GENI services.
#    notes_url    url
#    action_url    url
}

define servicegroup{
    servicegroup_name    %s
    alias    GENI data stores responsiveness
#    members    services
#    servicegroup_members    servicegroups
    notes    This group list all the nagios services that checks on the responsiveness of the GENI monitoring data stores.
#    notes_url    url
#    action_url    url
}

define servicegroup{
    servicegroup_name    %s
    alias    GENI data plane connectivity checks
#    members    services
#    servicegroup_members    servicegroups
    notes    This group list all the nagios services that checks on data plane connections between aggregates
#    notes_url    url
#    action_url    url
}

define servicegroup{
    servicegroup_name    %s
    alias    GENI SCS path availability
#    members    services
#    servicegroup_members    servicegroups
    notes    This group list all the nagios services that checks on the availability of a Stitching Computation Service paths between known stitching aggregates
#    notes_url    url
#    action_url    url
}

''' % (HOST_GROUP_GENI_HOSTS, HOST_GROUP_GENI_AGGREGATES, HOST_GROUP_GENI_AUTHORITIES, HOST_GROUP_GENI_SCSS, HOST_GROUP_GENI_EXTCKS,
       SERVICE_GROUP_AVAILABILITY, SERVICE_GROUP_STORE_RESP, SERVICE_GROUP_DATAPLANE_CONNECTIVITY_CHECK, SERVICE_GROUP_SCS_PATH_CHECK)



HOST_SECTION = '''
define host{
    host_name    %s
    alias    %s
    #parents    host_names
    hostgroups    %s
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

EXTCK_HOST_DESCRIPTION = "This nagios host represents the %s external check data store at the following URL: %s"

SERVICE_SECTION = '''
define service{
    host_name    %s
    service_description    %s
#    display_name    display_name
#    parents    service_descriptions
#    hourly_value    #
    servicegroups %s
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

IS_AVAILABLE_SERVICE_DESCRIPTION = "This nagios service represents whether an ops monitoring external check has been able \
to contact the Aggregate Manager API (or the SCS) and managed to successfully issue a listresources command"

IS_RESPONSIVE_SERVICE_DESCRIPTION = "This nagios service represents whether the data store has been responding to \
the collector requests"

CONNECTION_CHECK_SERVICE_DESCRIPTION = "This nagios service represents the fact that connection checks between 2 aggregates \
over the data plane have been succeeding"

STITCHING_CHECK_SERVICE_DESCRIPTION = "This nagios service represents the fact that the Stitching Computation Service is able \
to determine a stitching path between 2 aggregates"


def get_object_info((cert_path, url)):
    return handle_request(opslogger, cert_path, url)


def find_aggregate_in_list_via_key(agg_key_value, aggStores, key):
    for aggregate in aggStores:
        if aggregate is not None:
            if agg_key_value == aggregate[key]:
                return aggregate
    return None


def get_am_urls(aggregate):
    url_list = list()
    for key in aggregate.keys():
        if key.startswith("amurl"):
            url_list.append(aggregate[key])
    return url_list

def get_host_description(aggregate):
    agg_urn = aggregate['urn']
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
    return hostDesc

def get_hostgroups(host_type):
    if host_type == 'aggregate':
        return HOST_GROUP_GENI_HOSTS + "," + HOST_GROUP_GENI_AGGREGATES
    if host_type == 'scs':
        return HOST_GROUP_GENI_HOSTS + "," + HOST_GROUP_GENI_SCSS
    if host_type == 'authority':
        return HOST_GROUP_GENI_HOSTS + "," + HOST_GROUP_GENI_AUTHORITIES
    if host_type == 'extck':
        return HOST_GROUP_GENI_HOSTS + "," + HOST_GROUP_GENI_EXTCKS
    return HOST_GROUP_GENI_HOSTS


def write_generic_host_entry(of, hostId, hostDesc, host_type):
    of.write(HOST_SECTION % (hostId, hostId, get_hostgroups(host_type), hostDesc))
    of.write('\n')
    of.write(SERVICE_SECTION % (hostId, 'is_responsive', SERVICE_GROUP_STORE_RESP, IS_RESPONSIVE_SERVICE_DESCRIPTION))
    of.write('\n')

def write_aggregate_entry(of, hostId, aggregate):
    hostDesc = get_host_description(aggregate)
    host_type = 'aggregate'
    if hostId.startswith('scs'):
        host_type = 'scs'
    write_generic_host_entry(of, hostId, hostDesc, host_type)

def write_authority_entry(of, authorityId, authorityUrn):
    authorityHostDesc = AUTHORITY_HOST_DESCRIPTION % (authorityUrn,)
    write_generic_host_entry(of, authorityId, authorityHostDesc, 'authority')

def write_extck_entry(of, extck_id, extck_url):
    extckHostDesc = EXTCK_HOST_DESCRIPTION % (extck_id, extck_url)
    # for now an external check host entry pretty much looks the same as an aggregate entry
    write_generic_host_entry(of, extck_id, extckHostDesc, 'extck')



def read_existing_config_file(config_filename):
    opslogger.debug('Parsing nagios configuration file: %s', config_filename)
    of = open(config_filename, 'r')
    config_dict = dict()
    in_host_section = False
    in_service_section = False
    host_name = None
    host_type = None
    service_name = None
    agg_urn = None
    agg_urls = None
    error = False
    for line in of:
        line = line.strip()
        if in_host_section:
            if line.startswith('}'):
                in_host_section = False
                # grab all the info and add to the dictionary
                if not error:
                    if host_type is None:
                        opslogger.warning('unrecognized type')
                    else:
                        if host_name is None:
                            opslogger.warning('unrecognized host_name')
                        else:
                            host_dict = dict()
                            host_dict['services'] = list()
                            host_dict['type'] = host_type
                            if host_type == 'aggregate' or host_type == 'authority':
                                host_dict['urn'] = agg_urn
                            elif host_type == 'scs' or host_type == 'extck':
                                host_dict['urls'] = agg_urls
                            config_dict[host_name] = host_dict
                else:
                    opslogger.warning('Error during parsing of host section. Skipping section')
                host_name = None
                host_type = None
                agg_urn = None
                agg_urls = None
                error = False
            elif line.startswith('host_name'):
                host_name = line[9:].strip()
            elif line.startswith('notes'):
                notes = line[5:].strip()
                if notes.find('Aggregate Manager known via its GENI URN:') != -1:
                    host_type = 'aggregate'
                    agg_urn = notes[len(AGGREGATE_HOST_DESCRIPTION) - 2:]
                elif notes.find('Stitching Computation Service available at the following URL(s):') != -1:
                    host_type = 'scs'
                    agg_urls = notes[len(STITCHING_HOST_DESCRIPTION) - 2:]
                elif notes.find('clearing house authority known via its GENI URN:') != -1:
                    host_type = 'authority'
                    agg_urn = notes[len(AUTHORITY_HOST_DESCRIPTION) - 2:]
                elif notes.find('external check data store at the following URL: ') != -1:
                    host_type = 'extck'
                    agg_urls = notes[notes.find('external check data store at the following URL: ') + 45:]
                else:
                    opslogger.warning('unrecognized type for host %s from the notes %s' % (host_name, notes))
                    error = True
            continue
        elif in_service_section:
            if line.startswith('}'):
                in_service_section = False
                # grab all the info and add to the dictionary
                if host_name is None:
                    opslogger.warning('unrecognized host name associated with service')
                else:
                    if service_name is None:
                        opslogger.warning('unrecognized service')
                    else:
                        if not host_name in config_dict:
                            opslogger.warning("can't find host associated with service %s" % (service_name,))
                        else:
                            config_dict[host_name]['services'].append(service_name)
                # reset info
                host_name = None
                service_name = None
            elif line.startswith('host_name'):
                host_name = line[9:].strip()
            elif line.startswith('service_description'):
                service_name = line[19:].strip()
            continue
        else:
            # Looking for the beginning of a section.
            if line.startswith('define host{'):
                in_host_section = True
                continue
            elif line.startswith('define service{'):
                in_service_section = True
                continue
    of.close()
    return config_dict

def main(argv):
    (cert_path, opsconfig_url, output_file, input_file) = parse_args(argv)

    old_config_dict = None
    if input_file is not None:
        old_config_dict = read_existing_config_file(input_file)

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
    results = pool.map(get_object_info, argsArray)

    of.write(CONFIG_HEADER)
    aggregatesDict = dict()
    for res in results:
        if res is not None:
            agg_urn = res['urn']
            hostId = res['id']
            aggregatesDict[hostId] = agg_urn

    # If we parsed the old config, let's see if there were data store that we couldn't join this time, but did previously
    if old_config_dict is not None:
        for aggregate in aggStores:
            agg_urn = aggregate['urn']
            res = find_aggregate_in_list_via_key(agg_urn, results, 'urn')
            if res is None:
                # could not contact that data store this time around
                found = False
                for hostId in old_config_dict:
                    if aggregate['amtype'] == "stitcher":
                        if old_config_dict[hostId]['type'] == 'scs' and old_config_dict[hostId]['urls'].find(aggregate['am_url']) != -1 :
                            opslogger.debug('Did not get stitcher info from data store. Reusing info from previous configuration for %s' % aggregate['am_nickname'])
                            found = True
                    else:
                        if old_config_dict[hostId]['type'] == 'aggregate' and old_config_dict[hostId]['urn'] == agg_urn:
                            opslogger.debug('Did not get aggregate info from data store. Reusing info from previous configuration for %s' % agg_urn)
                            found = True
                    if found:
                        aggregatesDict[hostId] = agg_urn
                        break
                else:
                    opslogger.warning('Data store not answering and info not found in previous config: skipping aggregate %s ' % agg_urn)

    # Now writing all entries in order
    aggregatesSet = sorted(aggregatesDict.keys())
    for hostId in aggregatesSet:
        agg_urn = aggregatesDict[hostId]
        aggregate = find_aggregate_in_list_via_key(agg_urn, aggStores, 'urn')
        write_aggregate_entry(of, hostId, aggregate)


    extckStoreUrls = set()
    for extckStoreResponse in extckStoresResponses:
        extck_id = extckStoreResponse['id']
        extck_url = extckStoreResponse['selfRef']
        write_extck_entry(of, extck_id, extck_url)
        extckStoreUrls.add(extck_url)

        mon_aggregates = extckStoreResponse['monitored_aggregates']
        mon_agg_list = list()
        for mon_agg in mon_aggregates:
            agg_id = mon_agg['id']
            if agg_id in aggregatesSet:
                mon_agg_list.append(agg_id)
        # writing in order
        mon_agg_list = sorted(mon_agg_list)
        srvc_prefix = extck_id + ':'
        service_name = srvc_prefix + "is_available"
        for mon_agg in mon_agg_list:
            of.write(SERVICE_SECTION % (mon_agg, service_name, SERVICE_GROUP_AVAILABILITY, IS_AVAILABLE_SERVICE_DESCRIPTION))
            of.write('\n')

        experiments = extckStoreResponse['experiments']
        argsArray = list()
        for exp in experiments:
            args = (cert_path, exp['href'])
            argsArray.append(args)
        results = pool.map(get_object_info, argsArray)
        extck_expIds = list()
        for res in results:
            if res is not None:
                extck_expIds.append(res['id'])
        extck_expIds = sorted(extck_expIds)
        for exp_id in extck_expIds:
            if exp_id.endswith('_stitching'):
                # This is ugly - Hard coding the ID of the production SCS 'host'
                of.write(SERVICE_SECTION % ('scs-geni', srvc_prefix + exp_id, SERVICE_GROUP_SCS_PATH_CHECK,
                                            STITCHING_CHECK_SERVICE_DESCRIPTION))
                of.write('\n')
            else:
                # It's a ping check -It gets associated with the external check host itself.
                of.write(SERVICE_SECTION % (extck_id, exp_id, SERVICE_GROUP_DATAPLANE_CONNECTIVITY_CHECK,
                                            CONNECTION_CHECK_SERVICE_DESCRIPTION))
                of.write('\n')

    # if we parsed the old config, let's see if there were extck stores that we couldn't join this time around
    if old_config_dict is not None:
        for extckStore in extckStores:
            url = extckStore['href']
            extck_id = None
            if url not in extckStoreUrls:
                for hostId in old_config_dict:
                    if old_config_dict[hostId]['type'] == 'extck' and old_config_dict[hostId]['urls'] == url:
                        # we found it
                        extck_id = hostId
                        write_extck_entry(of, extck_id, url)
                        extckStoreUrls.add(url)
                        break;
                else:
                    opslogger.warning('Data store not answering and info not found in previous config: skipping external check store %s ' % url)
                if extck_id is not None:
                    # take care of monitoring aggregates
                    srvc_prefix = extck_id + ':'
                    service_name = srvc_prefix + "is_available"
                    mon_agg_list = list()
                    for hostId in old_config_dict:
                        if hostId in aggregatesSet:
                            if service_name in old_config_dict[hostId]['services']:
                                mon_agg_list.append(agg_id)
                    mon_agg_list = sorted(mon_agg_list)
                    for mon_agg in mon_agg_list:
                        of.write(SERVICE_SECTION % (hostId, service_name, SERVICE_GROUP_AVAILABILITY, IS_AVAILABLE_SERVICE_DESCRIPTION))
                        of.write('\n')
                    # deal with all the connectivity checks associated with the external checker
                    extck_services = sorted(old_config_dict[extck_id]['services'])
                    for service_name in extck_services:
                        if service_name != 'is_responsive':
                            # Assuming the only checks are ping checks for now
                            of.write(SERVICE_SECTION % (extck_id, service_name, SERVICE_GROUP_DATAPLANE_CONNECTIVITY_CHECK,
                                                        CONNECTION_CHECK_SERVICE_DESCRIPTION))
                            of.write('\n')
                    # Deal with the scs experiments
                    if 'scs-geni' in old_config_dict:
                        scs_services = sorted(old_config_dict['scs-geni']['services'])
                        for service_name in scs_services:
                            if service_name.startswith(srvc_prefix) and service_name != (srvc_prefix + 'is_available'):
                                of.write(SERVICE_SECTION % ('scs-geni', service_name, SERVICE_GROUP_SCS_PATH_CHECK,
                                                            STITCHING_CHECK_SERVICE_DESCRIPTION))
                                of.write('\n')


    authorityStoresSet = set()
    for authorityStoreResponse in authorityStoreResponses:
        authorityId = authorityStoreResponse['id']
        authorityUrn = authorityStoreResponse['urn']
        write_authority_entry(of, authorityId, authorityUrn)
        authorityStoresSet.add(authorityUrn)

    #
    if old_config_dict is not None:
        for authorityStore in authorityStores:
            urn = authorityStore['urn']
            if urn not in authorityStoresSet:
                for hostId in old_config_dict:
                    if old_config_dict[hostId]['type'] == 'authority' and old_config_dict[hostId]['urn'] == urn:
                        authorityId = hostId
                        write_authority_entry(of, authorityId, urn)
                        break
                else:
                    opslogger.warning('Data store not answering and info not found in previous config: skipping authority %s ' % urn)



    of.close()


if __name__ == "__main__":
    main(sys.argv[1:])
