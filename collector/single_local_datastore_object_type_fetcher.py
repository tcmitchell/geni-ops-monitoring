#!/usr/bin/python
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

import time
import json
import sys
import getopt
import requests
import pprint

sys.path.append("../common/")
import table_manager
import opsconfig_loader
import logger

def usage():
    sys.stderr.write('single_datastore_object_type_fetcher.py -d -a <aggregateid> -e <extckid> -c </cert/path/cert.pem> -o <objecttype (ex: -o n for nodes -o i interfaces, s for slivers, l for links, v for vlans, a for aggregate)>')
    sys.exit(1)

def parse_args(argv):
    if argv == []:
        usage()

    aggregate_id = ""
    extck_id = ""
    object_type = ""
    cert_path = ""
    debug = False

    try:
        opts, _ = getopt.getopt(argv, "ha:e:c:o:d", ["baseurl=", "aggregateid=", "extckid=", "certpath=", "objecttype=", "help", "debug"])
    except getopt.GetoptError:
        usage()

    for opt, arg in opts:
        if opt in ("-h", "--help"):
            usage()
        elif opt in ("-a", "--aggregateid"):
            aggregate_id = arg
        elif opt in ("-e", "--extckid"):
            extck_id = arg
        elif opt in ("-c", "--certificate"):
            cert_path = arg
        elif opt in ("-o", "--objecttype"):
            object_type = arg
        elif opt in ("-d" or "--debug"):
            debug = True
        else:
            usage()

    return [aggregate_id, extck_id, object_type, cert_path, debug]


class SingleLocalDatastoreObjectTypeFetcher:

    def __init__(self, tbl_mgr, aggregate_id, extck_id, obj_type, event_types, cert_path, debug, config_path):

        self.logger = logger.get_logger(config_path)
        self.tbl_mgr = tbl_mgr

        # The local datastore this thread queries
        # Exactly one of these should be ""
        self.aggregate_id = aggregate_id
        self.extck_id = extck_id

        # Query filter parameters
        self.obj_type = obj_type

        # collector certificate path
        self.cert_path = cert_path

        # ensures tables exist
        if not self.tbl_mgr.establish_all_tables():
            self.logger.critical("Could not establish all the tables. Exiting")
            sys.exit(-1)
        self.db_event_tables = ["ops_" + obj_type + "_" + ev_str for ev_str in event_types]

        self.event_types = ["ops_monitoring:" + ev_str for ev_str in event_types]

        # Set parameter to avoid query for all history since epoch = 0
        self.time_of_last_update = self.get_latest_ts()

        self.debug = debug

        if self.aggregate_id != "":
            self.meas_ref = self.get_meas_ref("ops_aggregate", self.aggregate_id)
        elif self.extck_id != "":
            self.meas_ref = self.get_meas_ref("ops_externalcheck", self.extck_id)

        self.obj_ids = self.get_object_ids(obj_type)


    def fetch_and_insert(self):
        """
        Method to fetch the data and store it in the collector DB.
        :return: True if everything went OK, False otherwise.
        """
        ok = True
        # poll datastore
        json_texts = self.poll_datastore()
#        if self.debug:
#            print json_texts

        onlyErr = True

        # there should be at least one answer unless we had issues retrieving it
        for json_text in json_texts:
            data = None
            try:
                data = json.loads(json_text)
            except ValueError, e:
                self.logger.warning("Unable to load response in json %s\n" % e)
                self.logger.warning("response = \n" + json_text)
                ok = False

            if data is not None:
                onlyErr = False
                for result in data:
                    self.logger.debug("Result received from %s about:" % self.aggregate_id)
                    self.logger.debug(pprint.pformat(result["id"]))

                    event_type = result["eventType"]
                    if event_type.startswith("ops_monitoring:"):
                        table_str = "ops_" + self.obj_type + "_" + event_type[15:]

                        # if id is event:obj_id_that_was_queried,
                        # TODO straighten out protocol with monitoring group
                        # for now go with this
                        id_str = result["id"]

                        # remove event: and prepend aggregate_id:
                        if self.aggregate_id != "":
                            datastore_id = self.aggregate_id
                        elif self.extck_id != "":
                            datastore_id = self.extck_id
                        obj_id = id_str[id_str.find(':') + 1:]

                        tsdata = result["tsdata"]
                        if len(tsdata) > 0:
                            if not tsdata_insert(self.tbl_mgr, datastore_id, obj_id, table_str, tsdata, self.debug, self.logger):
                                ok = False

        if onlyErr:
            ok = False
        return ok

    def get_latest_ts(self):
        max_ts = 0
        for table_str in self.db_event_tables:
            ts = self.get_latest_ts_at_table(table_str)
            if ts > max_ts:
                max_ts = ts
        return max_ts

    # Retrieves these from the collector database
    def get_object_ids(self, obj_type):

        obj_ids = []

        if obj_type == "node":
            obj_ids = self.get_all_nodes_of_aggregate()

        elif obj_type == "aggregate":
            obj_ids = self.get_all_aggregates_of_extckstore()

        elif obj_type == "interface":
            obj_ids = self.get_all_interfaces_of_aggregate()

        elif obj_type == "interfacevlan":
            obj_ids = self.get_all_interfacevlans_of_aggregate()

        else:
            sys.stderr.write("Invalid object type %s" % obj_type)
            sys.exit(1)

        return obj_ids


    def create_datastore_query(self, obj_ids, req_time):
        """
        Creates a data query URL for specific objects and a specific time range.
        :param obj_ids: the arrays of object IDs to request
        :param req_time: the upper bound of the time range.
        :return: the expected data query URL. 
        """
        q = {"filters":{"eventType":self.event_types,
                        "obj":{"type": self.obj_type,
                               "id": obj_ids},
                        "ts": {"gt": self.time_of_last_update,
                               "lt": req_time}
                        }
             }

        url = self.meas_ref + "?q=" + json.dumps(q)
        url = url.replace(' ', '')
        return url;

    def poll_datastore(self):
        _MAX_URL_LEN = 2000
        # current time for lt filter and record keeping
        req_time = int(time.time() * 1000000)

        url = self.create_datastore_query(self.obj_ids, req_time)
        urls = []

        if (len(url) > _MAX_URL_LEN):
            if self.debug:
                print "Data query URL too big. Breaking it"
            ids_len = 0
            for obj_id in self.obj_ids:
                ids_len += len(obj_id) + 3  # 2 quotes and a comma
            ids_len -= 1  # removing one comma too many
            baselen = len(url) - ids_len;  # that's how big the url is without any object ids in in.
            maxids_len = _MAX_URL_LEN - baselen;  # that's the max len we can have to list obj IDs
            obj_ids = []
            running_len = 0
            for obj_id in self.obj_ids:
                obj_len = len(obj_id)
                if running_len == 0:
                    nextlen = obj_len + 2
                else:
                    nextlen = running_len + obj_len + 3
                if (nextlen) <= maxids_len:
                    # we keep going
                    obj_ids.append(obj_id)
                    running_len = nextlen
                else:
                    # it's a wrap for that portion
                    urls.append(self.create_datastore_query(obj_ids, req_time))
                    running_len = obj_len + 2
                    obj_ids = [ obj_id ]
            # out of the loop
            if (running_len > 0):
                urls.append(self.create_datastore_query(obj_ids, req_time))
            if self.debug:
                print "Will request " + str(len(urls)) + " data urls"
        else:
            urls = [url]

        contents = []
        for url in urls:
            self.logger.debug(url)
            self.logger.debug("URL length = " + str(len(url)))

            resp = None
            try:
                resp = requests.get(url, verify=False, cert=self.cert_path)
            except requests.exceptions.RequestException, e:
                self.logger.warning("No response from local datastore at: " + url)
                self.logger.warning(e)

            if resp is not None:
                if (resp.status_code == requests.codes.ok):
                    self.time_of_last_update = req_time
                    contents.append(resp.content)
                else:
                    self.logger.warning("Response from " + url + " is invalid, code = " + str(resp.status_code))

        return contents


    def get_latest_ts_at_table(self, table_str):
        tbl_mgr = self.tbl_mgr
        if self.aggregate_id != "":
            datastore_id = self.aggregate_id
        elif self.extck_id != "":
            datastore_id = self.extck_id

        self.logger.debug("Getting latest timestamp in " + table_str + " for aggregate " + datastore_id)
        res = 0
        q_res = tbl_mgr.query("select max(ts) from " + table_str + " where aggregate_id = '" + datastore_id + "'")
        if q_res is not None:
            res = q_res[0][0]  # gets first of single tuple

        # We may have gotten a None for the timestamp if the table was empty.
        if res is None:
            res = 0
        self.logger.debug("latest timestamp in " + table_str + " for aggregate " + datastore_id
                          + " is: " + str(res) + " (" + time.asctime(time.gmtime(res / 1000000)) + ")")
        return res


    def get_all_nodes_of_aggregate(self):
        tbl_mgr = self.tbl_mgr
        aggregate_id = self.aggregate_id

        res = [];
        q_res = tbl_mgr.query("select id from ops_node where id in (select id from ops_aggregate_resource where aggregate_id = '" + aggregate_id + "')")
        if q_res is not None:
            for res_i in range(len(q_res)):
                res.append(q_res[res_i][0])  # gets first of single tuple

        return res


    def get_all_aggregates_of_extckstore(self):
        tbl_mgr = self.tbl_mgr

        res = [];
        q_res = tbl_mgr.query("select id from ops_externalcheck_monitoredaggregate where externalcheck_id = '" + self.extck_id + "'")
        if q_res is not None:
            for res_i in range(len(q_res)):
                res.append(q_res[res_i][0])  # gets first of single tuple

        return res


    def get_all_interfaces_of_aggregate(self):
        tbl_mgr = self.tbl_mgr
        aggregate_id = self.aggregate_id

        res = [];
        q_res = tbl_mgr.query("select id from ops_node_interface where node_id in (select id from ops_node where id in (select id from ops_aggregate_resource where aggregate_id = '" + aggregate_id + "'))")
        if q_res is not None:
            for res_i in range(len(q_res)):
                res.append(q_res[res_i][0])  # gets first of single tuple

        return res


    def get_all_interfacevlans_of_aggregate(self):
        tbl_mgr = self.tbl_mgr
        aggregate_id = self.aggregate_id

        res = [];
        q_res = tbl_mgr.query("select id from ops_link_interfacevlan where link_id in (select id from ops_link where id in (select id from ops_aggregate_resource where aggregate_id = '" + aggregate_id + "'))")
        if q_res is not None:
            for res_i in range(len(q_res)):
                res.append(q_res[res_i][0])  # gets first of single tuple

        return res


    def get_meas_ref(self, tbl_str, object_id):
        tbl_mgr = self.tbl_mgr

        meas_ref = None
        q_res = tbl_mgr.query("select " + tbl_mgr.get_column_name("measRef") + " from " + tbl_str + " where id = '" + object_id + "' limit 1")
        if q_res is not None:
            meas_ref = q_res[0][0]  # gets first of single tuple

        if meas_ref is None:
            sys.stderr.write("ERROR: No measurement ref found for aggregate: %s\nRun the info_crawler to find this or wrong argument passed \n" % self.aggregate_id)
            sys.exit(1)

        return meas_ref


# Builds the multi-row insert value string
def tsdata_insert(tbl_mgr, agg_id, obj_id, table_str, tsdata, debug, logger):
    """
    Function to insert time series data into a given table about a given object.
    :param tbl_mgr: an instance of TableManager to use to execute the SQL statements
    :param agg_id: the id of the aggregate that reported the data
    :param obj_id: the id of the object that the data is pertaining to.
    :param table_str: the name of the table
    :param tsdata: the list of time series data in dictionary format
    :param debug: a boolean saying whether to actually perform the insertion (False) or 
        just print what would happen.
    :param logger: an instance of the logger to use.
    :return: True if the insertion happened (or would have happened in debug mode) correctly, False otherwise.
    """
    ok = True
    vals_str = ""
    for tsdata_i in tsdata:
        vals_str += "('" + str(agg_id) + "','" + str(obj_id) + "','" + str(tsdata_i["ts"]) + "','" + str(tsdata_i["v"]) + "'),"

    vals_str = vals_str[:-1]  # remove last ','

    if debug:
        logger.info("<print only> insert " + table_str + " values: " + vals_str)
    else:
        if not tbl_mgr.insert_stmt(table_str, vals_str):
            ok = False
    return ok


def main(argv):

    [aggregate_id, extck_id, object_type_param, cert_path, debug] = parse_args(argv)
    if (aggregate_id == "" and extck_id == "") or object_type_param == "" or cert_path == "":
        usage()

    db_type = "collector"
    config_path = "../config/"
    # If in debug mode, make sure to overwrite the logging configuration to print out what we want,
    if debug:
        logger.configure_logger_for_debug_info(config_path)

    tbl_mgr = table_manager.TableManager(db_type, config_path)
    tbl_mgr.poll_config_store()

    ocl = opsconfig_loader.OpsconfigLoader(config_path)
    all_event_types = ocl.get_event_types()


    node_event_types = all_event_types["node"]
    interface_event_types = all_event_types["interface"]
    interface_vlan_event_types = all_event_types["interfacevlan"]
    aggregate_event_types = all_event_types["aggregate"]

    # pprint(all_event_types)

    if object_type_param == 'n':
        event_types = node_event_types
        object_type = "node"
    elif object_type_param == 'i':
        event_types = interface_event_types
        object_type = "interface"
    elif object_type_param == 'v':
        event_types = interface_vlan_event_types
        object_type = "interfacevlan"
    elif object_type_param == 'a':
        event_types = aggregate_event_types
        object_type = "aggregate"
    else:
        sys.stderr.write("invalid object type arg %s\n" % object_type_param)
        sys.exit(1)

    fetcher = SingleLocalDatastoreObjectTypeFetcher(tbl_mgr, aggregate_id, extck_id, object_type, event_types, cert_path, debug, config_path)

    if not fetcher.fetch_and_insert():
        logger.get_logger(config_path).critical("fetch_and_insert() failed")
        sys.exit(-1)


if __name__ == "__main__":
    main(sys.argv[1:])
