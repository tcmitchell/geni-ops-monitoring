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
import ConfigParser
from pprint import pprint as pprint
sys.path.append("../common/")
import table_manager

def usage():
    sys.stderr.write('single_datastore_object_type_fetcher.py -d -a <aggregate-id> -o <object-type (ex: -o n for nodes -o i interfaces, s for slivers, l for links, v for vlans)>')
    sys.exit(1)

def parse_args(argv):
    if argv == []:
        usage()

    aggregate_id = ""
    object_type = ""
    debug = False

    try:
        opts, args = getopt.getopt(argv,"ha:o:d",["baseurl=","aggregateid=","object-type=","help","debug"])
    except getopt.GetoptError:
        usage()

    for opt, arg in opts:
        if opt in ("-h", "--help"):
            usage()
        elif opt in ("-a", "--aggregateid"):
            aggregate_id = arg
        elif opt in ("-o", "--object-type"):
            object_type = arg
        elif opt in ("-d" or "--debug"):
            debug = True
        else:
            usage()

    return [aggregate_id, object_type, debug]


class SingleLocalDatastoreObjectTypeFetcher:

    def __init__(self, tbl_mgr, aggregate_id, obj_type, event_types, debug):

        self.tbl_mgr = tbl_mgr

        # The local datastore this thread queries
        self.aggregate_id = aggregate_id


        # Query filter parameters
        self.obj_type = obj_type

        # ensures tables exist
        self.tbl_mgr.establish_tables(event_types)
        self.db_event_tables = event_types

        # removes "ops_" (first 4 chars) from each string
        self.event_types = ["ops_monitoring:" + ev_str[4:] for ev_str in event_types]

        # Set parameter to avoid query for all history since epoch = 0
        self.time_of_last_update = self.get_latest_ts()

        self.debug = debug

        self.meas_ref = self.get_meas_ref()
        self.obj_ids = self.get_object_ids(obj_type)


    def fetch(self): 
    
        # poll datastore
        json_text = self.poll_datastore()

        try:
            data = json.loads(json_text)
        except Exception, e:
            sys.stderr.write("Unable to load response in json %s" % e)

        for result in data:
            if self.debug:
                print "Result received from %s about:" % self.aggregate_id
                pprint(result["id"])

            event_type = result["eventType"]
            if event_type.startswith("ops_monitoring:"):
                table_str = "ops_" + event_type[15:]

                # if id is event:obj_id_that_was_queried,
                # TODO straighten out protocol with monitoring group
                id_str = result["id"]

                # remove event: and prepend aggregate_id:
                agg_id = self.aggregate_id
                obj_id = id_str[id_str.find(':')+1:]

                tsdata = result["tsdata"]
                tsdata_insert(self.tbl_mgr, agg_id, obj_id, table_str, tsdata, self.debug)


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

        elif obj_type == "sliver":
            pass  # TODO implement and test
            #obj_ids = self.info_crawler.get_all_slivers_of_aggregate()

        elif obj_type == "interface":
            obj_ids = self.get_all_interfaces_of_aggregate()
           
        elif obj_type == "interfacevlan":
            pass   # TODO implement and test
            #obj_ids = self.get_all_interfacevlans_of_aggregate()

        else:
            sys.stderr.write("Invalid object type %s" % obj_type)
            sys.exit(1)

        return obj_ids


    def poll_datastore(self):
        
        # current time for lt filter and record keeping
        req_time = int(time.time()*1000000)

        #q = {"filters":{"eventType":self.event_types, 
        #                "obj":{"type": self.obj_type,
        #                       "id": self.obj_ids},
        #                "ts": {"gt": self.time_of_last_update
        #                       }
        #                }
        #     }
        
        q = {"filters":{"eventType":self.event_types, 
                        "obj":{"type": self.obj_type,
                               "id": self.obj_ids},
                        "ts": {"gt": self.time_of_last_update,
                               "lt": req_time}
                        }
             }

        url = self.meas_ref + "?q=" + str(q)
        url = url.replace(' ', '%20')
        if self.debug:
            print url

        resp = requests.get(url)
             
        if resp:
            self.time_of_last_update = req_time
        
        # need to handle response codes
        return resp.content


    def get_latest_ts_at_table(self, table_str):
        tbl_mgr = self.tbl_mgr
        aggregate_id = self.aggregate_id
        res = 0
        cur = tbl_mgr.con.cursor()
        tbl_mgr.db_lock.acquire()
        try:
            cur.execute("select max(ts) from " + table_str + " where aggregate_id = '" + aggregate_id + "'")
            q_res = cur.fetchall()
            res = q_res[0][0] # gets first of single tuple
            
        except Exception, e:
            sys.stderr.write("%s\n" % e)
            tbl_mgr.con.commit()
        
        cur.close()
        tbl_mgr.db_lock.release()
        
        return res


    def get_all_nodes_of_aggregate(self):
        tbl_mgr = self.tbl_mgr
        aggregate_id = self.aggregate_id

        cur = tbl_mgr.con.cursor()
        res = [];
        tbl_mgr.db_lock.acquire()
        try:
            cur.execute("select id from ops_node where id in (select id from ops_aggregate_resource where aggregate_id = '" + aggregate_id + "');")
            q_res = cur.fetchall()

            tbl_mgr.con.commit()
            for res_i in range(len(q_res)):
                res.append(q_res[res_i][0]) # gets first of single tuple
            
        except Exception, e:
            sys.stderr.write("%s\n" % e)
            tbl_mgr.con.commit()
        
        cur.close()
        tbl_mgr.db_lock.release()
        
        return res


    def get_all_interfaces_of_aggregate(self):
        tbl_mgr = self.tbl_mgr
        aggregate_id = self.aggregate_id

        cur = tbl_mgr.con.cursor()
        res = [];
        tbl_mgr.db_lock.acquire()
        try:
            cur.execute("select id from ops_node_interface where node_id in (select id from ops_node where id in (select id from ops_aggregate_resource where aggregate_id = '" + aggregate_id + "'));")

            q_res = cur.fetchall()
            tbl_mgr.con.commit()
            for res_i in range(len(q_res)):
                res.append(q_res[res_i][0]) # gets first of single tuple
            
        except Exception, e:
            sys.stderr.write("%s\n" % e)
            tbl_mgr.con.commit()
        
        cur.close()
        tbl_mgr.db_lock.release()
        
        return res


    def get_all_links_of_aggregate(self):
        tbl_mgr = self.tbl_mgr
        aggregate_id = self.aggregate_id

        cur = tbl_mgr.con.cursor()
        res = [];
        tbl_mgr.db_lock.acquire()
        try:
            cur.execute("select id from ops_link where id in (select id from ops_aggregate_resource where aggregate_id = '" + aggregate_id + "');")
            q_res = cur.fetchall()
            
            tbl_mgr.con.commit()
            for res_i in range(len(q_res)):
                res.append(q_res[res_i][0]) # gets first of single tuple
            
        except Exception, e:
            sys.stderr.write("%s\n" % e)
            tbl_mgr.con.commit()
        
        cur.close()
        tbl_mgr.db_lock.release()
        
        return res


    def get_meas_ref(self):
        tbl_mgr = self.tbl_mgr
        object_id = self.aggregate_id
        cur = tbl_mgr.con.cursor()
        res = []
        meas_ref = None
        tbl_mgr.db_lock.acquire()
        try:

            # two queries avoids regex split with ,
            if tbl_mgr.database_program == "postgres":
                cur.execute("select \"measRef\" from ops_aggregate where id = '" + object_id + "' limit 1")
            elif tbl_mgr.database_program == "mysql":
                cur.execute("select measRef from ops_aggregate where id = '" + object_id + "' limit 1")
            q_res = cur.fetchone()
            tbl_mgr.con.commit()
            if q_res is not None:
                meas_ref = q_res[0] # gets first of single tuple
            
        except Exception, e:
            sys.stderr.write("%s\n" % e)
            tbl_mgr.con.commit()
        
        cur.close()
        tbl_mgr.db_lock.release()
        
        if meas_ref is None:
            sys.stderr.write("ERROR: No measurement ref found for aggregate: %s\nRun the info_crawler to find this or wrong argument passed \n" % self.aggregate_id)
            sys.exit(1)

        return meas_ref

  
# Builds the multi-row insert value string
def tsdata_insert(tbl_mgr, agg_id, obj_id, table_str, tsdata, debug):
    vals_str = ""
    for tsdata_i in tsdata:
        vals_str += "('" + str(agg_id) + "','" + str(obj_id) + "','" + str(tsdata_i["ts"]) + "','" + str(tsdata_i["v"]) + "'),"

    vals_str = vals_str[:-1] # remove last ','

    if debug:
        print "<print only> insert " + table_str + " values: " + vals_str
    else:
        tbl_mgr.insert_stmt(table_str, vals_str)

      
def main(argv): 

    [aggregate_id, object_type_param, debug] = parse_args(argv)
    if aggregate_id == "" or object_type_param == "":
        usage()

    db_type = "collector"
    config_path = "../config/"
    data_schema = json.load(open("../config/data_schema"))
    event_types = json.load(open("../config/event_types"))

    tbl_mgr = table_manager.TableManager(db_type, config_path, debug)

    # ensures tables exist in database
    tbl_mgr.establish_tables(data_schema.keys())

    # Event types to query, TODO, less hard coding of this is needed
    node_event_types = ["ops_cpu_util","ops_mem_used_kb","ops_swap_free","ops_disk_part_max_used"]
    
    print node_event_types
    print event_types["node"]
    node_event_types = event_types["node"]

    interface_event_types = ["ops_rx_bps","ops_tx_bps","ops_rx_pps","ops_tx_pps","ops_rx_dps","ops_tx_dps","ops_rx_eps","ops_tx_eps"]

    if object_type_param == 'n':
        event_types = node_event_types
        object_type = "node"
    elif object_type_param == 'i':
        event_types = interface_event_types
        object_type = "interface"
    else:
        sys.stderr.write("invalid object type arg %s\n" % object_type_param)
        sys.exit(1)

    fetcher = SingleLocalDatastoreObjectTypeFetcher(tbl_mgr, aggregate_id, object_type, event_types, debug)

    fetcher.fetch()


if __name__ == "__main__":
    main(sys.argv[1:])
