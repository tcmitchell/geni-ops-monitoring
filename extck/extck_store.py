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
import getopt
import json
import ConfigParser
# import subprocess
import requests
from string import digits
# from extck.coordinate_mesoscale_experiments import tbl_mgr
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
        config.read("./ips.conf")
        self.ip_campus = dict(config.items("campus"))
        self.ip_core = dict(config.items("core"))

    def populateInfoTables(self, shortName, slices, srcPing, ipList):
        dataStoreBaseUrl = "https://extckdatastore.gpolab.bbn.com"
        dataStoreSite = "gpo"
        exp_tablename = "ops_experiment"
        exp_schema = self.tbl_mgr.schema_dict[exp_tablename]
        ext_exp_tablename = "ops_externalcheck_experiment"
        ext_exp_schema = self.tbl_mgr.schema_dict[ext_exp_tablename]
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

                        urnHrefs = getSiteInfo(srcSite, dstSite, shortName)  # [srcUrn, srcHref, dstUrn, dstHref]
                        if urnHrefs[0] == '' or urnHrefs[1] == '' or urnHrefs[2] == '' or urnHrefs[3] == '':
                            continue
                        else:
                            ts = str(int(time.time() * 1000000))
                            exp = ["http://www.gpolab.bbn.com/monitoring/schema/20140828/experiment#",
                                   exp_id,
                                   dataStoreBaseUrl + "/info/experiment/" + exp_id,
                                   ts,
                                   sliceUrn,
                                   sliceUuid,
                                   urnHrefs[0],
                                   urnHrefs[1],
                                   urnHrefs[2],
                                   urnHrefs[3]]
                            self.tbl_mgr.upsert(exp_tablename, exp_schema, exp, self.tbl_mgr.get_column_from_schema(exp_schema, "id"))
                            extck_exp = [exp_id, dataStoreSite, dataStoreBaseUrl + "/info/experiment/" + exp_id]
                            self.tbl_mgr.upsert(ext_exp_tablename, ext_exp_schema, extck_exp,
                                                (self.tbl_mgr.get_column_from_schema(ext_exp_schema, "id"),
                                                 self.tbl_mgr.get_column_from_schema(ext_exp_schema, "externalcheck_id")))

    def insert_externalcheck_monitoredaggregate(self, urn, aggRow):
        extck_id = aggRow[1]  # agg_id
        dataStoreSite = "gpo"
#         ts = str(int(time.time() * 1000000))
        dataStoreHref = aggRow[2]
        mon_agg = [extck_id, dataStoreSite, dataStoreHref]
        ext_monagg_tablename = "ops_externalcheck_monitoredaggregate"
        ext_monagg_schema = self.tbl_mgr.schema_dict[ext_monagg_tablename]

        self.tbl_mgr.upsert(ext_monagg_tablename, ext_monagg_schema, mon_agg,
                    (self.tbl_mgr.get_column_from_schema(ext_monagg_schema, "id"),
                     self.tbl_mgr.get_column_from_schema(ext_monagg_schema, "externalcheck_id")))


    def insert_aggregate(self, urn, aggRow):
        agg_tablename = "ops_aggregate"
        agg_schema = self.tbl_mgr.schema_dict[agg_tablename]

        self.tbl_mgr.upsert(agg_tablename, agg_schema, aggRow,
                    self.tbl_mgr.get_column_from_schema(agg_schema, "id"))


    def insert_externalcheck(self):  # This function assumes the existence of only 1 external check datastore
        dataStoreSite = "gpo"
        dataStore_url_base = "https://extckdatastore.gpolab.bbn.com"
        ts = str(int(time.time() * 1000000))
        extck = ["http://www.gpolab.bbn.com/monitoring/schema/20140828/externalcheck#",
                 dataStoreSite,
                 dataStore_url_base + "/info/externalcheck/" + dataStoreSite,
                 ts,
                 dataStore_url_base + "/data/"]
        table_str = "ops_externalcheck"
        extck_schema = self.tbl_mgr.schema_dict[table_str]
        self.tbl_mgr.upsert(table_str, extck_schema, extck, self.tbl_mgr.get_column_from_schema(extck_schema, "id"))


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

def get_default_attribute_for_type(vartype):
    val = "";
    if vartype.startswith("int"):
        val = 0
    return val


def extract_row_from_json_dict(logger, db_table_schema, object_dict, object_desc, db_to_json_map=None):
    """
    Method to extract values from a json dictionary corresponding to database columns.
    :param logger: logger object
    :param db_table_schema: a database table schema in the usual format (list of tuples whose first value is
    column name, second is column type, third is whether the value is optional or not)
    :param object_dict: the json dictionary for an object
    :param object_desc: object short description. This will be used in a warning message if the object
    attribute was expected but not present in the json dictionary
    :param db_to_json_map: a map to get the json key(s) from a column name.
    :return: the list of attributes for the object. This list will be
    formed with the values from the json dictionary in the order of the database table columns.
    A value will be None if the field was optional and not present, or a default value if the field
    was required and not present.
    """
    object_attribute_list = []
    for db_column_schema in db_table_schema:
        missing = False
        if (db_to_json_map is not None) and (db_column_schema[0] in db_to_json_map):
            jsonkeys = db_to_json_map[db_column_schema[0]]
            missing = False
            jsondict = object_dict
            for jsonkey in jsonkeys:
                if jsonkey in jsondict:
                    jsondict = jsondict[jsonkey]
                else:
                    missing = True
                    break
            if not missing:
                object_attribute_list.append(jsondict)  # the last iteration is the value itself, not another dictionary.
            else:
                jsondesc = ""
                for jsonkey in jsonkeys:
                    jsondesc += "[\"" + jsonkey + "\"]"
        else:
            if db_column_schema[0].startswith("properties$"):
                jsonkey = "ops_monitoring:" + db_column_schema[0].split('$')[1]
            else:
                jsonkey = db_column_schema[0]

            if jsonkey in object_dict:
                object_attribute_list.append(object_dict[jsonkey])
            else:
                missing = True
                jsondesc = jsonkey

        if missing:
            if db_column_schema[2]:
                logger.warn("value for required json " + object_desc + " field "
                             + jsondesc + " is missing. Replacing with default value...")
                object_attribute_list.append(get_default_attribute_for_type(db_column_schema[1]))
            else:
                # This is OK. This was an optional field.
                object_attribute_list.append(None)
    return object_attribute_list


def getShortName(tbl_mgr, aggStores, cert_path):
    """
    Function to get the aggregate information from a list of aggregates.
    :param tbl_mgr: the TableManager object instance used by this script. It is used to 
        access the logger field to log statements, and the schema_dict field to get the DB schema 
        for certain tables.
    :param aggStores: the list of aggregate stores, as a json dictionary in the format of the
        opsconfig aggregatestores array. 
    :param cert_path: the path to the certificate.
    :return: a dictionary ordered by the aggregate URN. Each dictinary entry is a list that contains:
        the aggregate id
        the aggregate type as recognized by the /usr/local/bin/wrap_am_api_test script.
        the fully qualified domain name for the aggregate manager
        the URL of the AM API server
        the aggregate attributes in the format of a row of values to be inserted in the ops_aggregate table.
    """
    shortName = {}
    ops_agg_schema = tbl_mgr.schema_dict["ops_aggregate"]
    agg_schema_str = "http://www.gpolab.bbn.com/monitoring/schema/20140828/aggregate#"
    extck_measRef = "https://extckdatastore.gpolab.bbn.com/data/"
    nickCache = getNickCache()
    for aggregate in aggStores:

        if aggregate['amtype'] == 'instageni' or \
                aggregate['amtype'] == 'protogeni' or \
                aggregate['amtype'] == "exogeni" or \
                aggregate['amtype'] == "opengeni":
            aggDetails = handle_request(tbl_mgr.logger, cert_path, aggregate['href'])  # Use url for site's store to query site
            if aggDetails == None:
                continue
            agg_attributes = extract_row_from_json_dict(tbl_mgr.logger, ops_agg_schema, aggDetails, "aggregate")
            urn = aggDetails['urn']
            if aggregate['amtype'] == "opengeni":
                amType = aggregate['amtype']
            else:
                amType = "protogeni"
            aggShortName = aggDetails['id']
            if aggregate.has_key('amurl'):  # For non-prod aggregates
                url = aggregate['amurl']
            else:
                if nickCache.has_key(urn):
                    url = nickCache[urn][1]
                else:
                    # No point grabbing data for site without AM URL
                    tbl_mgr.logger.warning("Missing URL for " + aggShortName)
                    continue

            cols = url.strip().split('/')
            cols1 = cols[2].strip().split(':')
            fqdn = cols1[0]
            shortName[urn] = [aggShortName, amType, fqdn, url, agg_attributes]

        elif aggregate['amtype'] == "network-aggregate":  # Case for ion
            if nickCache.has_key(aggregate['urn']):
                aggDetails = handle_request(tbl_mgr.logger, cert_path, aggregate['href'])
                if aggDetails == None:
                    continue
                agg_attributes = extract_row_from_json_dict(tbl_mgr.logger, ops_agg_schema, aggDetails, "aggregate")
                urn = aggDetails['urn'];
                amType = 'myplc';
                aggShortName = aggDetails['id'];
                url = nickCache[urn][1]
                cols = url.strip().split('/');
                cols1 = cols[2].strip().split(':');
                fqdn = cols1[0]
                shortName[urn] = [aggShortName, amType, fqdn, url, agg_attributes]
        elif aggregate['amtype'] == "stitcher":  # Special case
            selfRef = aggregate['href']; 
            urn = aggregate['urn']
            amType = aggregate['amtype']
            url = "http://oingo.dragon.maxgigapop.net:8081/geni/xmlrpc"
            fqdn = '';
            aggShortName = "scs"
            ts = str(int(time.time() * 1000000))
            ops_status = "development"
            agg_attributes = (agg_schema_str,  # schema
                              aggShortName,  # id
                              selfRef,  # selfref
                              urn,  # urn
                              ts,  # time stamp
                              extck_measRef,  # meas Ref
                              None,  # # populator version
                              ops_status,  # operational status
                              None  # routable IP poolsize
                              )
            shortName[urn] = [aggShortName, amType, fqdn, url, agg_attributes]
        elif aggregate['amtype'] == "foam" :
            # FOAM and OG
            selfRef = aggregate['href']
            urn = aggregate['urn']
            amType = aggregate['amtype']

            if aggregate.has_key('amurl'):  # For non-prod foam aggregates
                url = aggregate['amurl']
                ops_status = "development"
            else:
                if nickCache.has_key(urn):
                    url = nickCache[urn][1]
                    ops_status = "production"
                else:
                    tbl_mgr.logger.warning("Missing URL for " + urn)
                    continue

            # Get aggShortName
            cols = selfRef.strip().split('/')
            aggShortName = cols[len(cols) - 1]  # Grab last component in cols

            # Get fqdn
            cols = url.strip().split('/')
            cols1 = cols[2].strip().split(':')
            fqdn = cols1[0]
            ts = str(int(time.time() * 1000000))
            agg_attributes = (agg_schema_str,  # schema
                              aggShortName,  # id
                              selfRef,  # selfref
                              urn,  # urn
                              ts,  # time stamp
                              extck_measRef,  # meas Ref
                              None,  # # populator version
                              ops_status,  # operational status
                              None  # routable IP poolsize
                              )
            shortName[urn] = [aggShortName, amType, fqdn, url, agg_attributes]
        elif aggregate['amtype'] == "wimax":
            # wimax are not really aggregates...
            # So no AM API can't be queried for their availability
            continue
        else:
            tbl_mgr.logger.warning("Unrecognized AM type: " + aggregate['amtype'])

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


def handle_request(logger, cert_path, url=None):

    if url == None:
        # Production url
        url = 'https://opsconfigdatastore.gpolab.bbn.com/info/opsconfig/geni-prod'
        # Dev url
        # url='https://tamassos.gpolab.bbn.com/info/opsconfig/geni-prod'

    resp = None
    try:
        resp = requests.get(url, verify=False, cert=cert_path)
    except Exception, e:
        logger.warning("No response from local datastore at: " + url)
        logger.warning(e)
        return None

    if resp:
        try:
            json_dict = json.loads(resp.content)
        except Exception, e:
            logger.warning("Could not load response from " + url + " into JSON")
            logger.warning(e)
            return None

        return json_dict
    else:
        logger.warning("could not reach datastore at " + url)
        return None


def usage():
    usage = '''
    extck_store.py performs information fetching on the different aggregates listed by opsconfig. 
    It puts aggregate and experiment information in the local database.  It needs to be
    called with the arguments specifying a certificate

     -c or --certpath= <pathname> provides the path to your tool certificate
     -h or --help prints the usage information.
    '''
    print(usage)
    sys.exit(1)

def parse_args(argv):
    if argv == []:
        usage()

    cert_path = ""

    try:
        opts, _ = getopt.getopt(argv, "hc:", ["help", "certpath="])
    except getopt.GetoptError:
        usage()

    for opt, arg in opts:
        if opt in("-h", "--help"):
            usage()
        elif opt in ("-c", "--certpath"):
            cert_path = arg
        else:
            usage()

    return [cert_path]


def main(argv):

    [cert_path] = parse_args(argv)
    db_name = "local"
    config_path = "../config/"
    tbl_mgr = table_manager.TableManager(db_name, config_path)
    tbl_mgr.poll_config_store()
    ip = InfoPopulator(tbl_mgr, "")
    ip.insert_externalcheck()
    # Grab urns and urls for all agg stores
    # url="https://www.genirack.nyu.edu:5001/info/aggregate/nyu-ig"
    # https://www.geni.case.edu:5001/info/aggregate/cwru-ig
    # https://www.instageni.lsu.edu:5001/info/aggregate/lsu-ig
    aggRequest = handle_request(tbl_mgr.logger, cert_path)
    # print aggRequest
    # return
    if aggRequest == None:
        tbl_mgr.logger.warning("Could not not contact opsconfigdatastore!")
        return
    aggStores = aggRequest['aggregatestores']
    # read list of urls (or short-names)
    shortName = getShortName(tbl_mgr, aggStores, cert_path)
    # Save the results in a file that will be used by extck_populator.py
    json.dump(shortName, open("/home/amcanary/shortName", 'w'))
    slices = getSlices()
    srcPingCampus = ['gpo-ig', 'utah-ig']
    srcPingCore = ['gpo-ig-3715_core', 'gpo-ig-3716_core']
    # Populate "ops_externalcheck_experiment" and "ops_experiment" tables
    ip.populateInfoTables(shortName, slices, srcPingCampus, ip.ip_campus)
    ip.populateInfoTables(shortName, slices, srcPingCore, ip.ip_core)
    # Populate "ops_externalCheck" table
    for urn in shortName:
        # Populate "ops_aggregate" table
        ip.insert_aggregate(urn, shortName[urn][4])
        # Populate "ops_externalcheck_monitoredaggregate" table
        ip.insert_externalcheck_monitoredaggregate(urn, shortName[urn][4])

if __name__ == "__main__":
    main(sys.argv[1:])
