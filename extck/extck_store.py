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
import os
import requests
import multiprocessing
import multiprocessing.pool


extck_path = os.path.abspath(os.path.dirname(__file__))
top_path = os.path.dirname(extck_path)
common_path = os.path.join(top_path, "common")
config_path = os.path.join(top_path, "config")
sys.path.append(common_path)
sys.path.append(extck_path)

# import opsconfig_loader
import table_manager
import extck_config
import pinger
import extck_populate_stitching_experiment
import opsconfig_loader


BASE_SCHEMA_URL = "http://www.gpolab.bbn.com/monitoring/schema/20151105/"


def getSiteInfo(nickCache, srcSiteName, aggStores):
    am_urn = nickCache.get_am_urn(srcSiteName)
    am_url = nickCache.get_am_url(srcSiteName)
    datastore_url = ""
    # First let's try from the cache.
    if am_urn is not None:

        for store in aggStores:
            if store["urn"] == am_urn:
                datastore_url = store["href"]
                break
    else:
        # if am_urn is None then so is am_url
        # then let's try from the opsconfig
        am_urn = ""
        for store in aggStores:
            if "am_nickname" in store and store["am_nickname"] == srcSiteName:
                am_urn = store["urn"]
                datastore_url = store["href"]
                if 'am_url' in store:
                    am_url = store['am_url']
                break
    return (am_urn, datastore_url, am_url)


class InfoPopulator():
    PING_CAMPUS = object()
    PING_CORE = object()

    EXPERIMENT_METRICSGROUP_PINGS = "pings"
    EXPERIMENT_METRICSGROUP_STITCHING = "stitching"
    AGGREGATE_METRICSGROUP_AVAILABILITY = "availability"
    AGGREGATE_METRICSGROUP_AVAILABILITY_AND_FREE_RES = "availability_and_resources"

    def __init__(self, tbl_mgr, config, nickCache):
        """
        Constructor for InfoPopulator object
        :param tbl_mgr: the instance of table manager used to access the database.
        :param config: the ExtckConfigLoader instance used to get the configuration of the external check store.
        :param nickCache:the AggregateNickCache instance used to get urns from site nicknames.
        """
        self.tbl_mgr = tbl_mgr
        self._config = config
        self._nickCache = nickCache
        self.extckStoreBaseUrl = self._config.get_extck_store_base_url()
        self._extckStoreSite = self._config.get_extck_store_id()

        self._ipsconfig = ConfigParser.ConfigParser()
        self._ipsconfig.read(os.path.join(extck_path, "ips.conf"))

        # Try to get the software version we're running from the VERSION file
        # in the top-level directory.
        version_filename = top_path + "/VERSION"
        try:
            version_file = open(version_filename)
            self.monitoring_version = version_file.readline().strip()
            version_file.close()
        except Exception as e:
            self.tbl_mgr.logger.warning("Could not read monitoring version from file %s: %s" % (
                version_filename, str(e)))
            self.monitoring_version = "unknown"

        self.tbl_mgr.logger.info(
            "Monitoring version is %s" %
            (self.monitoring_version))
        self.__setUp_metricsgroups()

    def __getSiteInfo(self, srcSiteName, aggStores):
        return getSiteInfo(self._nickCache, srcSiteName, aggStores)

    def __addExperimentGroupInfo(self, group_id, group_desc):
        expgroup_tablename = "ops_experimentgroup"
        expgroup_schema = self.tbl_mgr.schema_dict[expgroup_tablename]
        ts = str(int(time.time() * 1000000))
        expgroup = [BASE_SCHEMA_URL + "experimentgroup#", group_id,
                    self.extckStoreBaseUrl +
                    "/info/experimentgroup/" + group_id,
                    ts, group_desc
                    ]
        self.tbl_mgr.upsert(expgroup_tablename, expgroup_schema, expgroup,
                            self.tbl_mgr.get_column_from_schema(expgroup_schema, "id"))

    def populateExperimentInfoTables(self, aggStores):
        slices = self._config.get_experiment_slices_info()
        ping_sets = self._config.get_experiment_ping_set()

        experiment_names = set()

        for ping_set in ping_sets:
            srcPing = self._config.get_experiment_source_ping_for_set(ping_set)
            # Populate "ops_experimentgroup" table
            (group_id, group_desc) = self._config.get_experiment_group_for_ping_set(
                ping_set)
            self.__addExperimentGroupInfo(group_id, group_desc)
            # Populate "ops_experiment" table
            self.__populateExperimentInfoTables(slices, srcPing, ping_set, aggStores, experiment_names,
                                                group_id, InfoPopulator.EXPERIMENT_METRICSGROUP_PINGS)

        (group_id, group_desc) = self._config.get_experiment_group_for_stitching(
            "scs-geni")
        self.__addExperimentGroupInfo(group_id, group_desc)

        stitch_site_info = extck_populate_stitching_experiment.get_stitch_sites_details(
            self.tbl_mgr)
        stitch_slicename = self._config.get_stitch_experiment_slicename()
        sliceUrn = slices[stitch_slicename][0]
        sliceUuid = slices[stitch_slicename][1]

        for idx1 in range(len(stitch_site_info)):
            site1 = stitch_site_info[idx1]
            for idx2 in range(idx1 + 1, len(stitch_site_info)):
                site2 = stitch_site_info[idx2]
                exp_id = extck_populate_stitching_experiment.name_stitch_path_experiment(
                    site1[0],
                    site2[0])
                self.__addExperimentInfo(exp_id, sliceUrn, sliceUuid, site1[1], site1[2], site2[1], site2[2],
                                         experiment_names, group_id, InfoPopulator.EXPERIMENT_METRICSGROUP_STITCHING)

        self.__cleanUpObsoleteExperiments(experiment_names)

    def __addExperimentInfo(self, exp_id, sliceUrn, sliceUuid, srcAmUrn, srcAmHref,
                            dstAmUrn, dstAmHref, experiment_names, group_id, metricsgroup_id):
        exp_tablename = "ops_experiment"
        exp_schema = self.tbl_mgr.schema_dict[exp_tablename]
#         ext_exp_tablename = "ops_externalcheck_experiment"
#         ext_exp_schema = self.tbl_mgr.schema_dict[ext_exp_tablename]
        ts = str(int(time.time() * 1000000))
        exp = [BASE_SCHEMA_URL + "experiment#",
               exp_id,
               self.extckStoreBaseUrl + "/info/experiment/" + exp_id,
               ts,
               sliceUrn,
               sliceUuid,
               srcAmUrn,
               srcAmHref,
               dstAmUrn,
               dstAmHref,
               self._extckStoreSite,
               group_id,
               metricsgroup_id
               ]
        self.tbl_mgr.upsert(
            exp_tablename,
            exp_schema,
            exp,
            self.tbl_mgr.get_column_from_schema(
                exp_schema,
                "id"))
#         extck_exp = [exp_id, self._extckStoreSite, self.extckStoreBaseUrl + "/info/experiment/" + exp_id]
#         self.tbl_mgr.upsert(ext_exp_tablename, ext_exp_schema, extck_exp,
#                             (self.tbl_mgr.get_column_from_schema(ext_exp_schema, "id"),
# self.tbl_mgr.get_column_from_schema(ext_exp_schema,
# "externalcheck_id")))
        experiment_names.add(exp_id)

    def __populateExperimentInfoTables(
            self, slices, srcPing, ping_set, aggStores, experiment_names, group_id, metricsgroup_id):
        ipList = dict(self._ipsconfig.items(ping_set))

        for srcSite in srcPing:
            for dstSite in ipList:
                if srcSite == dstSite:
                    # A site must not ping itself
                    continue

                slice_name = self._config.get_experiment_source_ping_slice_name(
                    ping_set,
                    srcSite)
                sliceUrn = slices[slice_name][0]
                sliceUuid = slices[slice_name][1]

                (exp_id,
                 srcSiteName,
                 dstSiteName) = pinger.get_ping_experiment_name(ping_set,
                                                                srcSite,
                                                                dstSite)

                if exp_id is None:
                    continue

                (srcAmUrn,
                 srcAmHref,
                 _) = self.__getSiteInfo(srcSiteName,
                                         aggStores)
                (dstAmUrn,
                 dstAmHref,
                 _) = self.__getSiteInfo(dstSiteName,
                                         aggStores)
                if srcAmUrn == '' or srcAmHref == '' or dstAmUrn == '' or dstAmHref == '':
                    self.tbl_mgr.logger.warning("Error when getting info from source %s and dest %s, got src urn %s, src href %s, dst urn %s, dst href %s"
                                                % (srcSite, dstSite, srcAmUrn, srcAmHref, dstAmUrn, dstAmHref))
                    continue
                else:
                    self.__addExperimentInfo(
                        exp_id,
                        sliceUrn,
                        sliceUuid,
                        srcAmUrn,
                        srcAmHref,
                        dstAmUrn,
                        dstAmHref,
                        experiment_names,
                        group_id,
                        metricsgroup_id)

    def __cleanUpObsoleteExperiments(self, experiment_names):
        registeredExperiments = self.tbl_mgr.query(
            "select id from ops_experiment")
        if registeredExperiments is None:
            return
        for experiment in registeredExperiments:
            if experiment[0] not in experiment_names:
                # Looks like we had an old experiment registered
                self.tbl_mgr.logger.info(
                    "Experiment %s is obsolete: deleting corresponding records" %
                    experiment[0])
#                 self.tbl_mgr.execute_sql("delete from ops_externalcheck_experiment where id='%s'" % experiment[0])
                self.tbl_mgr.execute_sql(
                    "delete from ops_experiment_ping_rtt_ms where id='%s'" %
                    experiment[0])
                self.tbl_mgr.execute_sql(
                    "delete from ops_experiment where id='%s'" %
                    experiment[0])

    def insert_externalcheck_monitoredaggregate(
            self, aggregate_id, avail_only):
        if avail_only:
            metric_group_id = InfoPopulator.AGGREGATE_METRICSGROUP_AVAILABILITY
        else:
            metric_group_id = InfoPopulator.AGGREGATE_METRICSGROUP_AVAILABILITY_AND_FREE_RES
        mon_agg = [aggregate_id,
                   self._extckStoreSite,
                   metric_group_id
                   ]
        ext_monagg_tablename = "ops_externalcheck_monitoredaggregate"
        ext_monagg_schema = self.tbl_mgr.schema_dict[ext_monagg_tablename]

        self.tbl_mgr.upsert(ext_monagg_tablename, ext_monagg_schema, mon_agg,
                            (self.tbl_mgr.get_column_from_schema(ext_monagg_schema, "id"),
                             self.tbl_mgr.get_column_from_schema(ext_monagg_schema, "externalcheck_id")))

    def insert_aggregate(self, urn, aggRow):
        agg_tablename = "ops_aggregate"
        agg_schema = self.tbl_mgr.schema_dict[agg_tablename]

        self.tbl_mgr.upsert(agg_tablename, agg_schema, aggRow,
                            self.tbl_mgr.get_column_from_schema(agg_schema, "urn"))

    def update_aggregate_ts(self, urn):
        statement = "UPDATE ops_aggregate SET ts=%d WHERE urn='%s'" % \
            (int(time.time() * 1000000), urn)
        self.tbl_mgr.execute_sql(statement)
        statement = "select * from ops_aggregate WHERE urn='%s'" % urn
        return self.tbl_mgr.query(statement)

    def insert_aggregate_url(self, aggregate_id, aggregate_manager_url):
        agg_amurl_tablename = "extck_aggregate_amurl"
        agg_amurl_schema = self.tbl_mgr.schema_dict[agg_amurl_tablename]
        index_agg = self.tbl_mgr.get_column_from_schema(
            agg_amurl_schema,
            "aggregate_id")
        index_amurl = self.tbl_mgr.get_column_from_schema(
            agg_amurl_schema,
            "amurl")
        if index_agg < index_amurl:
            row = (aggregate_id, aggregate_manager_url)
        else:
            row = (aggregate_manager_url, aggregate_id)
        self.tbl_mgr.upsert(
            agg_amurl_tablename,
            agg_amurl_schema,
            row,
            (index_agg,
             index_amurl))

    def insert_aggregate_type(self, aggregate_id, aggregate_type):
        agg_tablename = "extck_aggregate"
        agg_schema = self.tbl_mgr.schema_dict[agg_tablename]
        index_agg = self.tbl_mgr.get_column_from_schema(
            agg_schema,
            "aggregate_id")
        index_type = self.tbl_mgr.get_column_from_schema(agg_schema, "type")
        if index_agg < index_type:
            row = (aggregate_id, aggregate_type)
        else:
            row = (aggregate_type, aggregate_id)
        self.tbl_mgr.upsert(agg_tablename, agg_schema, row, index_agg)

    def insert_externalcheck(self):
        ts = str(int(time.time() * 1000000))
        extck = [BASE_SCHEMA_URL + "externalcheck#",
                 self._extckStoreSite,
                 self.extckStoreBaseUrl +
                 "/info/externalcheck/" + self._extckStoreSite,
                 ts,
                 self.extckStoreBaseUrl + "/data/",
                 self.monitoring_version
                 ]
        table_str = "ops_externalcheck"
        extck_schema = self.tbl_mgr.schema_dict[table_str]
        self.tbl_mgr.upsert(
            table_str,
            extck_schema,
            extck,
            self.tbl_mgr.get_column_from_schema(
                extck_schema,
                "id"))

    def __setUp_metricsgroups(self):
        exp_metricsgrp_table = "ops_experiment_metricsgroup"
        exp_metricsgrp_relation_table = "ops_experiment_metricsgroup_relation"
        agg_metricsgrp_table = "ops_aggregate_metricsgroup"
        agg_metricsgrp_relation_table = "ops_aggregate_metricsgroup_relation"
        exp_metricsgr_schema = self.tbl_mgr.schema_dict[exp_metricsgrp_table]
        exp_metricsgr_relation_schema = self.tbl_mgr.schema_dict[
            exp_metricsgrp_relation_table]
        agg_metricsgr_schema = self.tbl_mgr.schema_dict[agg_metricsgrp_table]
        agg_metricsgr_relation_schema = self.tbl_mgr.schema_dict[
            agg_metricsgrp_relation_table]

        self.tbl_mgr.upsert(
            exp_metricsgrp_table,
            exp_metricsgr_schema,
            (InfoPopulator.EXPERIMENT_METRICSGROUP_PINGS,
             ),
            0)
        self.tbl_mgr.upsert(
            exp_metricsgrp_table,
            exp_metricsgr_schema,
            (InfoPopulator.EXPERIMENT_METRICSGROUP_STITCHING,
             ),
            0)

        self.tbl_mgr.upsert(
            agg_metricsgrp_table,
            agg_metricsgr_schema,
            (InfoPopulator.AGGREGATE_METRICSGROUP_AVAILABILITY,
             ),
            0)

        self.tbl_mgr.upsert(
            agg_metricsgrp_table,
            agg_metricsgr_schema,
            (InfoPopulator.AGGREGATE_METRICSGROUP_AVAILABILITY_AND_FREE_RES,
             ),
            0)

        self.tbl_mgr.upsert(exp_metricsgrp_relation_table, exp_metricsgr_relation_schema,
                            ('ping_rtt_ms',
                             self._config.get_experiment_ping_frequency(),
                             InfoPopulator.EXPERIMENT_METRICSGROUP_PINGS),
                            (self.tbl_mgr.get_column_from_schema(exp_metricsgr_relation_schema, 'id'),
                             self.tbl_mgr.get_column_from_schema(exp_metricsgr_relation_schema, 'group_id'))
                            )
        self.tbl_mgr.upsert(exp_metricsgrp_relation_table, exp_metricsgr_relation_schema,
                            ('is_stitch_path_available', self._config.get_experiment_stitching_frequency(),
                             InfoPopulator.EXPERIMENT_METRICSGROUP_STITCHING),
                            (self.tbl_mgr.get_column_from_schema(exp_metricsgr_relation_schema, 'id'),
                             self.tbl_mgr.get_column_from_schema(exp_metricsgr_relation_schema, 'group_id'))
                            )

        amcheck_frequency = self._config.get_experiment_amcheck_frequency()
        self.tbl_mgr.upsert(agg_metricsgrp_relation_table, agg_metricsgr_relation_schema,
                            ('is_available', amcheck_frequency,
                             InfoPopulator.AGGREGATE_METRICSGROUP_AVAILABILITY),
                            (self.tbl_mgr.get_column_from_schema(agg_metricsgr_relation_schema, 'id'),
                             self.tbl_mgr.get_column_from_schema(agg_metricsgr_relation_schema, 'group_id'))
                            )

        self.tbl_mgr.upsert(agg_metricsgrp_relation_table, agg_metricsgr_relation_schema,
                            ('is_available', amcheck_frequency,
                             InfoPopulator.AGGREGATE_METRICSGROUP_AVAILABILITY_AND_FREE_RES),
                            (self.tbl_mgr.get_column_from_schema(agg_metricsgr_relation_schema, 'id'),
                             self.tbl_mgr.get_column_from_schema(agg_metricsgr_relation_schema, 'group_id'))
                            )

        self.tbl_mgr.upsert(agg_metricsgrp_relation_table, agg_metricsgr_relation_schema,
                            ('routable_ip_available', amcheck_frequency,
                             InfoPopulator.AGGREGATE_METRICSGROUP_AVAILABILITY_AND_FREE_RES),
                            (self.tbl_mgr.get_column_from_schema(agg_metricsgr_relation_schema, 'id'),
                             self.tbl_mgr.get_column_from_schema(agg_metricsgr_relation_schema, 'group_id'))
                            )

        self.tbl_mgr.upsert(agg_metricsgrp_relation_table, agg_metricsgr_relation_schema,
                            ('raw_pc_available', amcheck_frequency,
                             InfoPopulator.AGGREGATE_METRICSGROUP_AVAILABILITY_AND_FREE_RES),
                            (self.tbl_mgr.get_column_from_schema(agg_metricsgr_relation_schema, 'id'),
                             self.tbl_mgr.get_column_from_schema(agg_metricsgr_relation_schema, 'group_id'))
                            )

    def cleanUpObsoleteAggregates(self, aggStores):
        """
        Method to clean up existing aggregate manager entries that no longer exists
        in the opsconfig data store.
        :param aggStores: a json dictionary object corresponding to the "aggregatestores"
          entry of the opsconfig json.
        """
        registeredAggs = self.tbl_mgr.query(
            "select urn, id from ops_aggregate")
        if registeredAggs is None:
            return
        currentUrnList = []
        for store in aggStores:
            currentUrnList.append(store["urn"])
        for agg_details in registeredAggs:
            if agg_details[0] not in currentUrnList:
                # Looks like we had an old aggregate registered
                self.tbl_mgr.logger.info(
                    "Aggregate %s (%s) is obsolete: deleting corresponding records" %
                    (agg_details[1], agg_details[0]))
                self.tbl_mgr.execute_sql(
                    "delete from ops_aggregate_is_available where id='%s'" %
                    agg_details[1])
                self.tbl_mgr.execute_sql(
                    "delete from ops_externalcheck_monitoredaggregate where id='%s'" %
                    agg_details[1])
                self.tbl_mgr.execute_sql(
                    "delete from extck_aggregate where aggregate_id='%s'" %
                    agg_details[1])
                self.tbl_mgr.execute_sql(
                    "delete from extck_aggregate_amurl where aggregate_id='%s'" %
                    agg_details[1])
                self.tbl_mgr.execute_sql(
                    "delete from ops_aggregate where id='%s'" %
                    agg_details[1])


# def db_insert(tbl_mgr, table_str, row_arr):
#     val_str = "('"
#
#     for val in row_arr:
# val_str += val + "','"  # join won't do this
#
# val_str = val_str[:-2] + ")"  # remove last 2 of 3 chars: ',' and add )
#
#     tbl_mgr.insert_stmt(table_str, val_str)

def get_default_attribute_for_type(vartype):
    val = ""
    if vartype.startswith("int"):
        val = 0
    return val


def extract_row_from_json_dict(
        logger, db_table_schema, object_dict, object_desc, db_to_json_map=None):
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
        if (db_to_json_map is not None) and (
                db_column_schema[0] in db_to_json_map):
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
                # the last iteration is the value itself, not another
                # dictionary.
                object_attribute_list.append(jsondict)
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
                object_attribute_list.append(
                    get_default_attribute_for_type(
                        db_column_schema[1]))
            else:
                # This is OK. This was an optional field.
                object_attribute_list.append(None)
    return object_attribute_list


class AggregateNickCache:

    __NICKNAMES_SECTION = "aggregate_nicknames"

    def __init__(self, nickfile):
        """
        :param nickfile: the name of the aggregate nickname cache configuration file.
        """
        self._nickfile = nickfile
        self._nickconfig = ConfigParser.ConfigParser()
        self._has_read = False

    def parseNickCache(self):
        """
        method to parse an omni-type  aggregate nickname cache configuration file.
        :return: a map that has aggregate managers as keys and sets of AM API URLs
        as values.
        """
        urn_to_urls_map = dict()
        if not self._has_read:
            if self._nickfile in self._nickconfig.read(self._nickfile):
                self._has_read = True

        # Going over the whole section
        nicknames = self._nickconfig.items(
            AggregateNickCache.__NICKNAMES_SECTION)
        for _key, urn_url in nicknames:
            [urn, url] = urn_url.split(",")
            urn = urn.strip()
            url = url.strip()
            if urn != "":
                if urn not in urn_to_urls_map:
                    urn_to_urls_map[urn] = set()
                urn_to_urls_map[urn].add(url)
        return urn_to_urls_map

    def updateCache(self, urn_to_urls_map, aggStores):
        """
        method to update the map of urns to AM API URLS for the Aggregate Managers, per
        the ops config information, which may contain the AM API URL, for AM that are not
        in production yet.
        :param urn_to_urls_map: the map of urns to AM API URLS for the Aggregate Managers.
        :param aggStores: a json dictionary object corresponding to the "aggregatestores"
          entry of the opsconfig json.
        """
        for aggregate in aggStores:
            if 'amurl' in aggregate:
                urn = aggregate['urn']
                if urn not in urn_to_urls_map:
                    urn_to_urls_map[urn] = set()
                for agg_key in aggregate.keys():
                    # Add url for all keys starting with amurl
                    if agg_key[:5] == "amurl":
                        urn_to_urls_map[urn].add(aggregate[agg_key])

    def get_am_urn(self, am_nickname):
        """
        Method to get the AM URN given its nickname.
        :param am_nickname: the nickname of the AM
        :return: Returns the AM URN or None if the nickname wasn't found.
        """
        try:
            valstr = self._nickconfig.get(
                AggregateNickCache.__NICKNAMES_SECTION,
                am_nickname)
        except:
            return None

        vals = valstr.split(',')
        return vals[0].strip()

    def get_am_url(self, am_nickname):
        """
        Method to get the AM URL given its nickname.
        :param am_nickname: the nickname of the AM
        :return: Returns the AM URL or None if the nickname wasn't found.
        """
        try:
            valstr = self._nickconfig.get(
                AggregateNickCache.__NICKNAMES_SECTION,
                am_nickname)
        except:
            return None

        vals = valstr.split(',')
        return vals[1].strip()


def registerOneAggregate(arg_tuple):
    (cert_path, urn_to_urls_map, ip, amtype, urn,
     ops_agg_schema, agg_schema_str, monitoring_version,
     extck_measRef, aggregate, lock) = arg_tuple
    avail_only = True
    register = True
    if amtype == 'instageni' or \
            amtype == 'protogeni' or \
            amtype == "exogeni" or \
            amtype == "opengeni" or \
            amtype == "network-aggregate":
        if urn not in urn_to_urls_map:
            lock.acquire()
            ip.tbl_mgr.logger.warning(
                "No known AM API URL for aggregate: %s\n Will NOT monitor" %
                urn)
            lock.release()
            return
        if amtype == 'instageni' or \
                amtype == 'protogeni':
            avail_only = False
        aggDetails = handle_request(
            ip.tbl_mgr.logger,
            cert_path,
            aggregate['href'])  # Use url for site's store to query site
        if aggDetails is None:
            # The aggregate didn't answer, but we'll update the timestamp if the record
            # exist. This is so the record does not get removed automatically from the DB after a week
            # if the AM has been having an issue for a long time...
            agg_attributes = ip.update_aggregate_ts(urn)
            register = False
            if agg_attributes is None:
                # the aggregrate was never registered
                return
        else:
            # don't care about what's being reported by the aggregate here.
            aggDetails[
                'metricsgroup_id'] = table_manager.TableManager.EMPTY_METRICSGROUP_ID
            if ip.tbl_mgr.aging_timeout > 0:
                current_ts = int(time.time() * 1000000)
                threshold = current_ts - (ip.tbl_mgr.aging_timeout * 1000000)
                if aggDetails['ts'] < threshold:
                    lock.acquire()
                    ip.tbl_mgr.logger.debug(
                        "replacing outdated timestamp for aggregate %s" %
                        aggDetails['id'])
                    lock.release()
                    aggDetails['ts'] = current_ts
            agg_attributes = extract_row_from_json_dict(
                ip.tbl_mgr.logger,
                ops_agg_schema,
                aggDetails,
                "aggregate")
    elif amtype == "stitcher":  # Special case
        selfRef = aggregate['href']
        if 'am_nickname' not in aggregate:
            lock.acquire()
            ip.tbl_mgr.logger.warning(
                "stitcher AM has missing nickname for %s\n Will NOT monitor" %
                selfRef)
            lock.release()
            return
        if 'am_status' not in aggregate:
            lock.acquire()
            ip.tbl_mgr.logger.warning(
                "stitcher AM has missing status for %s\n Will NOT monitor" %
                selfRef)
            lock.release()
            return
        aggId = aggregate['am_nickname']
        ts = str(int(time.time() * 1000000))
        ops_status = aggregate['am_status']
        agg_attributes = (agg_schema_str,  # schema
                          aggId,  # id
                          selfRef,  # selfref
                          urn,  # urn
                          ts,  # time stamp
                          extck_measRef,  # meas Ref
                          monitoring_version,  # # populator version
                          ops_status,  # operational status
                          None,  # routable IP poolsize
                          # metricsgroup_id
                          table_manager.TableManager.EMPTY_METRICSGROUP_ID
                          )
    elif amtype == "foam":
        # FOAM
        if urn not in urn_to_urls_map:
            lock.acquire()
            ip.tbl_mgr.logger.warning(
                "No known AM API URL for aggregate: %s\n Will NOT monitor" %
                urn)
            lock.release()
            return

        selfRef = aggregate['href']

        if 'amurl' in aggregate:  # For non-prod foam aggregates
            ops_status = "development"
        else:
            ops_status = "production"

        # Get aggregate id
        cols = selfRef.strip().split('/')
        aggId = cols[len(cols) - 1]  # Grab last component in cols

        ts = str(int(time.time() * 1000000))
        agg_attributes = (agg_schema_str,  # schema
                          aggId,  # id
                          selfRef,  # selfref
                          urn,  # urn
                          ts,  # time stamp
                          extck_measRef,  # meas Ref
                          monitoring_version,  # # populator version
                          ops_status,  # operational status
                          None,  # routable IP poolsize
                          # metricsgroup_id
                          table_manager.TableManager.EMPTY_METRICSGROUP_ID
                          )
    elif amtype == "wimax":
        # wimax are not really aggregates...
        # So no AM API can't be queried for their availability
        lock.acquire()
        ip.tbl_mgr.logger.info("Wimax aggregate won't be monitored (%s)" % urn)
        lock.release()
        return
    elif amtype == "iminds":
        # iMinds store. Registering them for now
        if urn not in urn_to_urls_map:
            lock.acquire()
            ip.tbl_mgr.logger.warning(
                "No known AM API URL for aggregate: %s\n Will NOT monitor" %
                urn)
            lock.release()
            return

        selfRef = aggregate['href']
        ops_status = "production"

        # Get aggregate id
        cols = selfRef.strip().split('/')
        aggId = cols[len(cols) - 1]  # Grab last component in cols

        ts = str(int(time.time() * 1000000))
        agg_attributes = (agg_schema_str,  # schema
                          aggId,  # id
                          selfRef,  # selfref
                          urn,  # urn
                          ts,  # time stamp
                          extck_measRef,  # meas Ref
                          monitoring_version,  # # populator version
                          ops_status,  # operational status
                          None,  # routable IP poolsize
                          # metricsgroup_id
                          table_manager.TableManager.EMPTY_METRICSGROUP_ID
                          )
    else:
        lock.acquire()
        ip.tbl_mgr.logger.warning("Unrecognized AM type: " + amtype)
        lock.release()
        return

    lock.acquire()
    if register:
        # Populate "ops_aggregate" table
        ip.insert_aggregate(urn, agg_attributes)
    # Populate "ops_externalcheck_monitoredaggregate" table
    agg_id = agg_attributes[1]
    ip.insert_externalcheck_monitoredaggregate(agg_id, avail_only)
    ip.insert_aggregate_type(agg_id, amtype)
    am_urls = urn_to_urls_map[urn]
    for am_url in am_urls:
        ip.insert_aggregate_url(agg_id, am_url)
    lock.release()


def registerAggregates(aggStores, cert_path, urn_to_urls_map, ip, config):
    """
    Function to register aggregates in the database.
    :param aggStores: a json dictionary object corresponding to the "aggregatestores"
      entry of the opsconfig json.
    :param cert_path: the path to the collector certificate used to retrieve the
      aggregate manager characteristics from the aggregate data store.
    :param urn_to_urls_map: Map of aggregate manager URN to AM API URLs.
    :param ip: instance of the InfoPopulator object used to populate the DB
    """
    ops_agg_schema = ip.tbl_mgr.schema_dict["ops_aggregate"]
    # TODO parameterize these
    agg_schema_str = BASE_SCHEMA_URL + "/aggregate#"
    version_filename = top_path + "/VERSION"
    try:
        version_file = open(version_filename)
        monitoring_version = version_file.readline().strip()
        version_file.close()
    except Exception as e:
        ip.tbl_mgr.logger.warning("Could not read monitoring version from file %s: %s" % (
            version_filename, str(e)))
        monitoring_version = "unknown"

    extck_measRef = ip.extckStoreBaseUrl + "/data/"

    myLock = multiprocessing.Lock()
    argsList = []
    for aggregate in aggStores:
        amtype = aggregate['amtype']
        urn = aggregate['urn']
        args = (cert_path, urn_to_urls_map, ip, amtype, urn,
                ops_agg_schema, agg_schema_str, monitoring_version,
                extck_measRef, aggregate, myLock)
        argsList.append(args)

    pool = multiprocessing.pool.ThreadPool(
        processes=int(
            config.get_populator_pool_size()))
    pool.map(registerOneAggregate, argsList)


def handle_request(logger, cert_path, url):

    resp = None
    try:
        resp = requests.get(url, verify=False, cert=cert_path)
    except Exception as e:
        logger.warning("No response from datastore at: " + url)
        logger.warning(e)
        return None

    if resp:
        try:
            json_dict = json.loads(resp.content)
        except Exception as e:
            logger.warning(
                "Could not load response from " +
                url +
                " into JSON")
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
    tbl_mgr = table_manager.TableManager(db_name, config_path)
    tbl_mgr.poll_config_store()
    opsConfigLoader = opsconfig_loader.OpsconfigLoader(config_path)
    config = extck_config.ExtckConfigLoader(tbl_mgr.logger)

    # Set up info about extra extck tables and establish them.
    config.configure_extck_tables(tbl_mgr)

    nickCache = AggregateNickCache(config.get_nickname_cache_file_location())

    ip = InfoPopulator(tbl_mgr, config, nickCache)
    # Populate "ops_externalCheck" table
    ip.insert_externalcheck()

    # Grab urns and urls for all agg stores
    opsconfig_url = opsConfigLoader.config_json['selfRef']

    aggRequest = handle_request(tbl_mgr.logger, cert_path, opsconfig_url)

    if aggRequest is None:
        tbl_mgr.logger.warning("Could not not contact opsconfigdatastore!")
        return
    aggStores = aggRequest['aggregatestores']

    urn_map = nickCache.parseNickCache()
    nickCache.updateCache(urn_map, aggStores)

    ip.cleanUpObsoleteAggregates(aggStores)

    registerAggregates(aggStores, cert_path, urn_map, ip, config)

    # Populate "ops_experiment" tables
    ip.populateExperimentInfoTables(aggStores)

if __name__ == "__main__":
    main(sys.argv[1:])
