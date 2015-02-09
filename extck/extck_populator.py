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
import sys
import time
import subprocess
import shlex
import os
# import requests

extck_path = os.path.abspath(os.path.dirname(__file__))
top_path = os.path.dirname(extck_path)
common_path = os.path.join(top_path, "common")
config_path = os.path.join(top_path, "config")
sys.path.append(common_path)
sys.path.append(extck_path)
import extck_config
import logger
import table_manager
opslogger = logger.get_logger(config_path)
config = extck_config.ExtckConfigLoader(opslogger)



##################################################
# geni-lib config for FOAM/FV listresources test #
sys.path.append(config.get_geni_lib_config_path())  #
sys.path.append(config.get_geni_lib_path())  #

import amcanary_config  #
context = amcanary_config.buildContext()  #
from geni.aggregate.core import AM  #
##################################################






class SiteOF(AM):
    def __init__ (self, name, url, apiversion):
        if apiversion == 0:
            apiversionstr = "amapiv2"
        else:
            apiversionstr = "amapiv" + str(apiversion)
        super(SiteOF, self).__init__(name, url, apiversionstr, "foam")
        self.apiversion = apiversion

def getOFState(context, site=None):

    try:
        ad = site.listresources(context)  # Run listresources for a particular site
    except Exception, e:
        opslogger.warning(str(e))
        opslogger.warning("Control plane connection for FOAM/FV Aggregate Manager to %s is Offline via API version %s" % (site.name, str(site.apiversion)))
        return 0  # Can't reach the site via control pat

    # Check to see if dpids have ports.
    #  No ports on all dpids for a given switch indicates possible FV issues.
    for switch in ad.datapaths:
        if len(switch.ports) == 0:
            opslogger.warning("NO ports found on " + switch.dpid + ". FV may be hang or connection from dpid to FV is broken.")
        else:  # If any dpid has ports listed, FV is working for that switch
            return 1

    opslogger.warning("NO ports found on any switch. FV may be hang or connection from dpid to FV is broken.")
    return 0  # All dpids on that switch had no ports. FV is down.

class DataPopulator():

    __IS_AVAILABLE_TBLNAME = "ops_aggregate_is_available"

    def __init__(self, tbl_mgr):
        self.tbl_mgr = tbl_mgr

    def insert_agg_is_avail_datapoint(self, agg_id, ts, state):

        datapoint = (agg_id, ts, state)
        self.__db_insert(DataPopulator.__IS_AVAILABLE_TBLNAME, datapoint)

    def __db_purge(self, table_str):
        old_ts = int((time.time() - 168 * 60 * 60) * 1000000)  # Purge data older than 1 week (168 hours)
        self.tbl_mgr.purge_old_tsdata(table_str, old_ts)


    def __db_insert(self, table_str, row_arr):
        val_str = "('"
        first = True
        for val in row_arr:
            if first:
                first = False
            else:
                val_str += "', '"
            val_str += str(val)
        val_str += "')"
        self.tbl_mgr.insert_stmt(table_str, val_str)

    def db_purge_agg_is_available(self):
        self.__db_purge(DataPopulator.__IS_AVAILABLE_TBLNAME)


def getAMStateForURL(agg_id, am_url, amtype, config):
    cmd_str = config.get_am_full_test_command(am_url, amtype)
    args = shlex.split(cmd_str)
    opslogger.debug("About to execute: " + cmd_str)
    # Searching for the name of the test being executed
    for arg in args:
        if arg.startswith("Test.test_"):
            test = arg[10:]  # the ending of that argument.
            break
    p = subprocess.Popen(args, stdout=subprocess.PIPE)
    output, _err = p.communicate()
    state = 0
    retcode = 1  # Assuming we've got an error
    for line in output.split('\n'):
        words = line.split()
        if len(words) == 3 \
            and words[0] == 'MONITORING' \
            and words[1] == ('test_%s' % test):
            retcode = int(words[2])
            break;
    qualifier = "NOT "
    if retcode == 0:
        state = 1
        qualifier = ""

    opslogger.info("aggregate %s is %sreachable at %s" % (agg_id, qualifier, am_url))
    return state

def getStitcherState():
    cmd = "cat /home/amcanary/getversion_SCS.xml | curl -X POST -H 'Content-type: text/xml' -d \@- http://oingo.dragon.maxgigapop.net:8081/geni/xmlrpc"
    echoCmd = "echo $?"
    os.popen(cmd)
    out = os.popen(echoCmd)
    result = int(out.read())
    if result == 0:
        return "1"
    else:
        return "0"

def main():

    db_name = "local"
    tbl_mgr = table_manager.TableManager(db_name, config_path)
    tbl_mgr.poll_config_store()
    dp = DataPopulator(tbl_mgr)

    extck_id = config.get_extck_store_id()


    # get all monitored aggregates

    monitored_aggregates = tbl_mgr.query("SELECT id FROM ops_externalcheck_monitoredaggregate WHERE externalcheck_id = '%s'" % extck_id)
    if monitored_aggregates is None:
        opslogger.warning("Could not find any monitored aggregate. Has extck_store been executed?")
        return

    for monitored_aggregate_tuple in monitored_aggregates:
        monitored_aggregate_id = monitored_aggregate_tuple[0]
        opslogger.info("Checking availability of AM: %s", monitored_aggregate_id)
        amtype = tbl_mgr.query("SELECT type FROM extck_aggregate WHERE aggregate_id = '%s'" % monitored_aggregate_id)
        if amtype is None:
            opslogger.warning("Error trying to determine type of aggregate: %s" % monitored_aggregate_id)
            continue
        amtype = amtype[0][0]  # first value of first tuple...
        am_urls = tbl_mgr.query("SELECT amurl FROM extck_aggregate_amurl WHERE aggregate_id = '%s'" % monitored_aggregate_id)
        if am_urls is None:
            opslogger.warning("Did not find any registered AM URL for aggregate: %s" % monitored_aggregate_id)
            continue
        overall_state = 0  # unavailable until confirmed available.
        if amtype == "foam":
            first = True
            for url_tuple in am_urls:
                url = url_tuple[0]
                version = config.get_apiversion_from_am_url(url, amtype)
                site = SiteOF(monitored_aggregate_id, url, version)  # may be not working anymore for exogeni...
                state = getOFState(context, site)
                if first:
                    overall_state = state
                    first = False
                else:
                    if (overall_state != 0):
                        if state == 0:
                            overall_state = 0

            pass
        elif amtype == "protogeni" or \
            amtype == "instageni" or \
            amtype == "exogeni" or \
            amtype == "protogeni" or \
            amtype == "network-aggregate":
            first = True
            for url_tuple in am_urls:
                url = url_tuple[0]
                state = getAMStateForURL(monitored_aggregate_id, url, amtype, config)
                if first:
                    overall_state = state
                    first = False
                else:
                    if (overall_state != 0):
                        if state == 0:
                            overall_state = 0
        elif amtype == "stitcher":
            continue
        ts = int(time.time() * 1000000)
        dp.insert_agg_is_avail_datapoint(monitored_aggregate_id, ts, overall_state)

    dp.db_purge_agg_is_available()

if __name__ == "__main__":
    main()
