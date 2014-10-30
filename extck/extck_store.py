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
import ConfigParser
# import subprocess
import os
import requests
from string import digits
# from pprint import pprint as pprint

common_path = "../common/"
sys.path.append(common_path)
# import opsconfig_loader
import table_manager

config_path = "/home/amcanary/"
# input file with short-names and Urls aggregates
# Need this file for sites like EG that aren't in prod but url is not in opsconfig
# inputFileBackup=open('/home/amcanary/src/gcf/agg_nick_cache.base')

inputFile = open('/home/amcanary/.bssw/geni/nickcache.json')

# Dic to store short name and corresponding url
# Format: shortName[urn]=[aggShortName, amType, selfRef, measRef, url, fqdn, schema]

shortName = {}

# Store cache of nickNames in here
# nickCache[urn]=[shortName, url]
nickCache = {}

# Dic to store slice info for campus and core
# monitoring slices.
#
slices = {}

class InfoPopulator():
    def __init__(self, tbl_mgr, url_base):

        self.tbl_mgr = tbl_mgr
        self.url_base = url_base
        # steal config path from table_manager
        self.config_path = tbl_mgr.config_path
        config = ConfigParser.ConfigParser()
        config.read(config_path + "ips.conf")
        self.ip_campus = dict(config.items("campus"))
        self.ip_core = dict(config.items("core"))

    def populateInfoTables(self, shortName, slices, srcPing, ipList, aggStores):
        fileLoc1 = "/home/amcanary/ops_externalcheck_experiment_Registry"
        fileLoc2 = "/home/amcanary/ops_experiment_Registry"
        dataStoreBaseUrl = "https://extckdatastore.gpolab.bbn.com"
        dataStoreSite = "gpo"
        for srcSite in srcPing:
            for dstSite in ipList:
                passFlag = 0
                if srcSite != dstSite:  # A site must not ping itself
                    dstSiteFlag = dstSite.strip().split('-')

                    if len(dstSiteFlag) == 2:
                        exp_id = srcSite + "_to_" + dstSite + "_campus"
                        sliceUrn = slices["sitemon"][0]
                        sliceUuid = slices["sitemon"][1]
                    else:
                        exp_id = srcSite + "_to_" + dstSite
                        srcSiteFlag = srcSite.strip().split('-')
                        if srcSiteFlag[2] != dstSiteFlag[2]:
                            passFlag = 1
                            pass  # Can't ping between hosts in different networks
                        else:
                            if dstSiteFlag[2] == "3715_core":  # Get slice info for core VLAN 3715
                                sliceUrn = slices["gpoI15"][0]
                                sliceUuid = slices["gpoI15"][1]
                            else:
                                sliceUrn = slices["gpoI16"][0]  # Get slice info for core VLAN 3716
                                sliceUuid = slices["gpoI16"][1]

                    if passFlag == 1:
                        pass
                    else:
                        # Routine for "ops_externalcheck_experiment" Table
                    #    extck_exp = [exp_id, dataStoreSite, dataStoreBaseUrl + "/info/experiment/" + exp_id]
                    #    dataInsert(self.tbl_mgr, fileLoc1, exp_id, extck_exp, "ops_externalcheck_experiment")

                        urnHrefs = getSiteInfo(srcSite, dstSite, shortName)  # [srcUrn, srcHref, dstUrn, dstHref]
                        if urnHrefs[0] == '' or urnHrefs[1] == '' or urnHrefs[2] == '' or urnHrefs[3] == '':
                            continue
                        else:
                            extck_exp = [exp_id, dataStoreSite, dataStoreBaseUrl + "/info/experiment/" + exp_id]
                            dataInsert(self.tbl_mgr, fileLoc1, exp_id, extck_exp, "ops_externalcheck_experiment")
                            ts = str(int(time.time() * 1000000))
                            exp = ["http://www.gpolab.bbn.com/monitoring/schema/20140828/experiment#", exp_id,
                            dataStoreBaseUrl + "/info/experiment/" + exp_id, ts, sliceUrn, sliceUuid,
                                urnHrefs[0], urnHrefs[1], urnHrefs[2], urnHrefs[3]]
                            dataInsert(self.tbl_mgr, fileLoc2, exp_id, exp, "ops_experiment")

    def insert_externalcheck_monitoredaggregate(self, urn, aggRow):
        extck_id = aggRow[0]  # agg_id
        dataStoreSite = "gpo"
#         ts = str(int(time.time() * 1000000))
        dataStoreHref = aggRow[2]
        mon_agg = [extck_id, dataStoreSite, dataStoreHref]
        fileLoc = "/home/amcanary/ops_externalcheck_monitoredaggregate_Registry"
        dataInsert(self.tbl_mgr, fileLoc, mon_agg[2], mon_agg, "ops_externalcheck_monitoredaggregate")

    def insert_aggregate(self, urn, aggRow):
        schema = aggRow[6]
        agg_id = aggRow[0]  # agg_id
        selfRef = aggRow[2]
        ts = str(int(time.time() * 1000000))
        measRef = aggRow[3]
        fileLoc = "/home/amcanary/ops_aggregate_Registry"
        data = [schema, agg_id, selfRef, urn, ts, measRef]
        # urn is used below to uniquely identify a row in a "tracking" file.
        dataInsert(self.tbl_mgr, fileLoc, urn, data, "ops_aggregate")

    def insert_externalcheck(self):  # This function assumes the existence of only 1 external check datastore
        dataStoreSite = "gpo"
        dataStore_url_base = "https://extckdatastore.gpolab.bbn.com"
        ts = str(int(time.time() * 1000000))
        extck = ["http://www.gpolab.bbn.com/monitoring/schema/20140828/externalcheck#", dataStoreSite, dataStore_url_base + "/info/externalcheck/" + dataStoreSite, ts, dataStore_url_base + "/data/"]
        fileLoc = "/home/amcanary/ops_externalcheck_Registry"
        dataInsert(self.tbl_mgr, fileLoc, extck[0], extck, "ops_externalcheck")

def dataInsert (tbl_mgr, fileLoc, exp_id, data, table):
    regFile = open(fileLoc, "r+")
    if os.stat(fileLoc).st_size > 0:  # If file is not empty
        exp_aggFlag = 0  # Check if an entry is registered
        for line in regFile:
            line = line.strip().split(" ")  # Remove white spaces
            if line[0] == exp_id:
                exp_aggFlag = 1
                break  # Item registered already
        if exp_aggFlag == 0:  # Register new item
            regFile.write(exp_id)
            regFile.write('\n')
            db_insert(tbl_mgr, table, data)
    else:  # Empty file
        regFile.write(exp_id)
        regFile.write('\n')
        db_insert(tbl_mgr, table , data)

def getSiteInfo(srcSite, dstSite, shortName):
    if srcSite == "gpo-ig-3715_core" or srcSite == "gpo-ig-3716_core": srcSite = "gpo-ig"
    if dstSite == "gpo-ig-3715_core" or dstSite == "gpo-ig-3716_core": dstSite = "gpo-ig"
    if srcSite == "wisconsin-ig-3715_core": srcSite = "wisconsin-ig"
    if srcSite == "uh-eg-3716_core": srcSite = "uh-eg"
    if srcSite == "missouri-ig-3716_core": srcSite = "missouri-ig"
    if dstSite == "wisconsin-ig-3715_core": dstSite = "wisconsin-ig"
    if dstSite == "uh-eg-3716_core": dstSite = "uh-eg"
    if dstSite == "missouri-ig-3716_core": dstSite = "missouri-ig"

    srcUrn = srcHref = dstUrn = dstHref = ''
    for key in shortName:
        if shortName[key][0] == srcSite:
            srcUrn = key
            srcHref = shortName[key][2]
        elif shortName[key][0] == dstSite:
            dstUrn = key
            dstHref = shortName[key][2]

    return [srcUrn, srcHref, dstUrn, dstHref]


def db_insert(tbl_mgr, table_str, row_arr):
    val_str = "('"

    for val in row_arr:
        val_str += val + "','"  # join won't do this

    val_str = val_str[:-2] + ")"  # remove last 2 of 3 chars: ',' and add )

    tbl_mgr.insert_stmt(table_str, val_str)

def getShortName(aggStores):

    nickCache = getNickCache()
    for aggregate in aggStores:

        if aggregate['amtype'] == 'instageni' or aggregate['amtype'] == 'protogeni':  # When ExoGENI datastores come online, insert here
            aggDetails = handle_request(aggregate['href'])  # Use url for site's store to query site
            if aggDetails == None:
                continue
            selfRef = aggDetails['selfRef']
            measRef = aggDetails['measRef']
            urn = aggDetails['urn']
            schema = aggDetails['$schema']
            amType = "protogeni"
            aggShortName = aggDetails['id']
            if aggregate.has_key('amurl'):  # For non-prod aggregates
                url = aggregate['amurl']
            else:
                if nickCache.has_key(urn):
                    url = nickCache[urn][1]
                else:
                    # No point grabbing data for site without AM URL
                    print "Missing URL for ", aggShortName
                    continue

            cols = url.strip().split('/')
            cols1 = cols[2].strip().split(':')
            fqdn = cols1[0]
            shortName[urn] = [aggShortName, amType, selfRef, measRef, url, fqdn, schema]

        elif aggregate['amtype'] == "network-aggregate":  # Case for ion
            if nickCache.has_key(aggregate['urn']):
                aggDetails = handle_request(aggregate['href'])
                if aggDetails == None:
                    continue
                selfRef = aggDetails['selfRef']; measRef = aggDetails['measRef']
                urn = aggDetails['urn']; amType = 'myplc'; schema = aggDetails['$schema']
                aggShortName = aggDetails['id']; url = nickCache[urn][1]
                cols = url.strip().split('/'); cols1 = cols[2].strip().split(':'); fqdn = cols1[0]
                shortName[urn] = [aggShortName, amType, selfRef, measRef, url, fqdn, schema]
        elif aggregate['amtype'] == "stitcher":  # Special case
            selfRef = aggregate['href']; measRef = "https://extckdatastore.gpolab.bbn.com/data/"; urn = aggregate['urn']
            amType = aggregate['amtype']
            schema = "http://www.gpolab.bbn.com/monitoring/schema/20140501/aggregate#"
            url = "http://oingo.dragon.maxgigapop.net:8081/geni/xmlrpc"
            fqdn = ''; aggShortName = "scs"
            shortName[urn] = [aggShortName, amType, selfRef, measRef, url, fqdn, schema]
        elif aggregate['amtype'] == "exogeni":
            continue  # EG datastores are not reporting as yet.
        else:  # FOAM and OG
            amurlFlag = 0  # Check to see if a site has a URL
            selfRef = aggregate['href']
            measRef = "https://extckdatastore.gpolab.bbn.com/data/"
            urn = aggregate['urn']
            schema = "http://www.gpolab.bbn.com/monitoring/schema/20140501/aggregate#"
            amType = aggregate['amtype']

            if aggregate.has_key('amurl'):  # For non-prod foam aggregates
                url = aggregate['amurl']
                amurlFlag = 1
            else:
                if nickCache.has_key(urn):
                    url = nickCache[urn][1]
                    amurlFlag = 1
                else:
                    print "Missing URL for ", urn
                    continue
            if amurlFlag == 1:
                # Get aggShortName
                if amType == "foam" or amType == "opengeni":
                    cols = selfRef.strip().split('/')
                    aggShortName = cols[len(cols) - 1]  # Grab last component in cols

            # Get aggShortName
            #  if amType == "exogeni":
            #      cols=urn.strip().split(':')
            #      cols1=cols[3].strip().split('vmsite')
            #      aggShortName=cols1[0]+ "-eg"
            #      amType="orca" # Ask stephane to change this
            #  elif amType == "foam":
            #      cols=selfRef.strip().split('/')
            #      aggShortName=cols[5]

            # Get fqdn
                    cols = url.strip().split('/')
                    cols1 = cols[2].strip().split(':')
                    fqdn = cols1[0]
                    shortName[urn] = [aggShortName, amType, selfRef, measRef, url, fqdn, schema]

    return shortName

def getNickCache():
    for line in inputFile:  # Read in line
        if line[0] != '#' and line[0] != '[' and line[0] != '\n':  # Don't read comments/junk
            cols = line.strip().split('=')
            aggShortName = cols[0]
            if aggShortName == "plcv3" or aggShortName == "plc3":  # Only grab fqdn for aggShortName=plc
                continue
            # print "agg", aggShortName
            aggShortName = formatShortName(aggShortName)  # Grab shortname and convert to current format
            cols1 = cols[1].strip().split(',')
            urn = cols1[0]
            url = cols1[1]
            nickCache[urn] = [aggShortName, url]
    return nickCache

def formatShortName(shortName):
    #  if len(shortName)>3:# Aggregate with 2 chars: ignore
    shortName = shortName.translate(None, digits)  # Remove all #s froms shortName
    oldFormat = shortName.strip().split('-')
    suffix = ['ig', 'eg', 'of', 'pg', 'og']
    if len(oldFormat) == 1:  # For cases like "ion"
        return shortName
    for suffix_id in suffix:
        if oldFormat[0] == suffix_id and len(oldFormat) == 2:  # For cases like gpo-ig
            newFormat = oldFormat[1] + "-" + suffix_id
            break
        elif oldFormat[1] == suffix_id and len(oldFormat) == 2:  # For cases like ig-gpo
            newFormat = shortName
            break
        elif oldFormat[0] == suffix_id and len(oldFormat) == 3:  # For cases like ig-of-gpo
            newFormat = oldFormat[2] + '-' + suffix_id + '-' + oldFormat[1]
            break
        elif oldFormat[1] == suffix_id and len(oldFormat) == 3:  # For cases like gpo-ig-of
            newFormat = shortName
            break

    if newFormat == "i-of":  # For i2-of case
        return "i2-of"
    else:
        return newFormat

def getSlices():
    slices = {'sitemon':['urn:publicid:IDN+ch.geni.net:gpoamcanary+slice+sitemon', 'f42d1c94-506a-4247-a8af-40f5760d7750'], 'gpoI15': ['urn:publicid:IDN+ch.geni.net:gpo-infra+slice+gpoI15', '35e195e0-430a-488e-a0a7-8314326346f4'], 'gpoI16':['urn:publicid:IDN+ch.geni.net:gpo-infra+slice+gpoI16', 'e85a5108-9ea3-4e01-87b6-b3bc027aeb8f']}
    return slices


def handle_request(url=None, cert_path=None):

    if url == None:
        # Production url
        url = 'https://opsconfigdatastore.gpolab.bbn.com/info/opsconfig/geni-prod'
        # Dev url
        # url='https://tamassos.gpolab.bbn.com/info/opsconfig/geni-prod'

    cert_path = '/etc/ssl/certs/collector-gpo-withnpkey2.pem'
    resp = None
    try:
        resp = requests.get(url, verify=False, cert=cert_path)
    except Exception, e:
        print "No response from local datastore at: " + url
        print e
        return None

    if resp:
        try:
            json_dict = json.loads(resp.content)
        except Exception, e:
            print "Could not load into JSON"
            print e
            return None

        return json_dict
    else:
        print "could not reach datastore at ", url
        return None


def main():

    db_name = "local"
    config_path = "../config/"
    tbl_mgr = table_manager.TableManager(db_name, config_path)
    tbl_mgr.poll_config_store()
    ip = InfoPopulator(tbl_mgr, "")
    # Grab urns and urls for all agg stores
    # url="https://www.genirack.nyu.edu:5001/info/aggregate/nyu-ig"
    # https://www.geni.case.edu:5001/info/aggregate/cwru-ig
    # https://www.instageni.lsu.edu:5001/info/aggregate/lsu-ig
    aggRequest = handle_request()
    # print aggRequest
    # return
    if aggRequest == None:
        print "WARNING: Could not not contact opsconfigdatastore!"
        return
    aggStores = aggRequest['aggregatestores']
    # read list of urls (or short-names)
    shortName = getShortName(aggStores)
    json.dump(shortName, open("/home/amcanary/shortName", 'w'))
    slices = getSlices()
    srcPingCampus = ['gpo-ig', 'utah-ig']
    srcPingCore = ['gpo-ig-3715_core', 'gpo-ig-3716_core']
    # Populate "ops_externalcheck_experiment" and "ops_experiment" tables
    ip.populateInfoTables(shortName, slices, srcPingCampus, ip.ip_campus, aggStores)
    ip.populateInfoTables(shortName, slices, srcPingCore, ip.ip_core, aggStores)
    # Populate "ops_externalCheck" table
    ip.insert_externalcheck()
    for urn in shortName:
        # Populate "ops_externalcheck_monitoredaggregate" table
        ip.insert_externalcheck_monitoredaggregate(urn, shortName[urn])
        # Populate "ops_aggregate" table
        ip.insert_aggregate(urn, shortName[urn])

if __name__ == "__main__":
    main()
