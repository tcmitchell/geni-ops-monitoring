#!/usr/bin/env python
#----------------------------------------------------------------------
# Copyright (c) 2014 Raytheon BBN Technologies
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
import json
# import ConfigParser
import subprocess
# from string import digits
import os
# import requests

##################################################
# geni-lib config for FOAM/FV listresources test #
geniLibConfigPath = "/usr/local/geni-lib/samples"  #
geniLibPath = "/usr/local/geni-lib"  #
sys.path.append(geniLibConfigPath)  #
sys.path.append(geniLibPath)  #

import amcanary_config  #
context = amcanary_config.buildContext()  #
from geni.aggregate.core import AM  #
##################################################

common_path = "../common/"
# input file with short-names and Urls aggregates
# inputFile=open('/home/amcanary/src/gcf/agg_nick_cache.base')
# inputFile=open('/home/amcanary/.bssw/geni/nickcache.json')
# dic to store short name and corresponding url
# Format: shortname [fqdn]=[aggShortName,amtype, state, timestamp]
# shortName[urn]=[aggShortName, amType, selfRef, measRef, url, fqdn, schema, state, timestamp]
# where state is 0 for up and 1 for down
shortName = {}

shortNamePath = "/home/amcanary/shortName"
sys.path.append(common_path)


import table_manager


class SiteOF(AM):
    def __init__ (self, name, url=None):
        super(SiteOF, self).__init__(name, url, "amapiv2", "foam")

def getOFState(context, site=None):
    try:
        ad = site.listresources(context)  # Run listresources for a particular site
    except:
        print "Control plane connection to", site.name, "for FOAM/FV Offline"
        return str(0)  # Can't reach the site via control path

    prtFlag = 0  # Check to see if dpids have ports.
                #  No ports on all dpids for a given switch indicates possible FV issues.
    for switch in ad.datapaths:
        if len(switch.ports) == 0:
            print "NO ports found on ", switch.dpid, ". FV may be hang or connection from dpid to FV is broken."
        else:  # If any dpid has ports listed, FV is working for that switch
            prtFlag = 1
            return str(prtFlag)
    return str(0)  # All dpids on that switch had no ports. FV is down.

class InfoPopulator():
    def __init__(self, tbl_mgr, url_base):

        self.tbl_mgr = tbl_mgr
        self.url_base = url_base
        # steal config path from table_manager
        self.config_path = tbl_mgr.config_path

    def insert_agg_is_avail_datapoint(self, aggRow):
        # Insert into ops_externalcheck
        agg_id = aggRow[0]  # agg_id
        ts = aggRow[8]  # str(int(time.time()*1000000))
        v = aggRow[7]
        datapoint = [agg_id, ts, v]
        db_insert(self.tbl_mgr, "ops_aggregate_is_available", datapoint)
        db_purge(self.tbl_mgr, "ops_aggregate_is_available")


def db_purge(tbl_mgr, table_str):
    old_ts = int((time.time() - 168 * 60 * 60) * 1000000)  # Purge data older than 1 week (168 hours)
    tbl_mgr.purge_old_tsdata(table_str, old_ts)


def db_insert(tbl_mgr, table_str, row_arr):
    val_str = "('"
    for val in row_arr:
        val_str += val + "','"  # join won't do this
    val_str = val_str[:-2] + ")"  # remove last 2 of 3 chars: ',' and add )
    tbl_mgr.insert_stmt(table_str, val_str)

def getAMState(output):
    cols = output.strip().split(':')
    if cols[2] == " Timed out after 60 seconds":  # Occurs if subprocess hangs
        result = "0"
    elif cols[3] == " 0":  # check for "returned: 0" output
        result = "1"  # Good result
    else:
        result = "0"  # Bad result
    return result

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
    config_path = "../config/"
    tbl_mgr = table_manager.TableManager(db_name, config_path)
    tbl_mgr.poll_config_store()
    ip = InfoPopulator(tbl_mgr, "")

    # Grab shortName dic outputed by extck_store.py
    shortName = json.load(open(shortNamePath))
    for urn in shortName:
        siteName = shortName[urn][0]
        amtype = shortName[urn][1]
        url = shortName[urn][4]
        fqdn = shortName[urn][5]
        if amtype == "foam":
            site = SiteOF(siteName, url)
            state = getOFState(context, site)
        elif amtype == "stitcher":  # Do something special
            state = getStitcherState()
        else:
            p = subprocess.Popen(["/usr/local/bin/wrap_am_api_test", "genich", fqdn, amtype, "GetVersion"], stdout=subprocess.PIPE)
            output, _err = p.communicate()
            state = getAMState(output)
        shortName[urn].append(state)
        shortName[urn].append(str(int(time.time() * 1000000)))
        ip.insert_agg_is_avail_datapoint(shortName[urn])

if __name__ == "__main__":
    main()
