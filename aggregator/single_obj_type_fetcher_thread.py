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

import threading
import time 
import json
import json_receiver
import sys
import requests
from pprint import pprint as pprint
import single_local_datastore_crawler
sys.path.append("../common/")
import table_manager

class SingleObjectTypeFetcherThread(threading.Thread):

    def __init__(self, tbl_mgr, info_crawler, thread_name, aggregate_id, obj_type, event_types, sleep_period_sec, time_of_last_update):
        threading.Thread.__init__(self)

        self.tbl_mgr = tbl_mgr
        self.thread_name = thread_name

        # The local datastore this thread queries
        self.aggregate_id = aggregate_id

        # Interval between aggregator queries in seconds
        self.sleep_period_sec = sleep_period_sec

        # Internal counter of the number of queries
        # TODO every 100th query or some time window, have the
        # info_crawler update the tables
        self.counter = 0
        
        # Set parameter to avoid query for all history since epoch = 0
        self.time_of_last_update = time_of_last_update

        # Periodic updates
        self.info_crawler = info_crawler

        # Query filter parameters
        self.obj_type = obj_type

        self.tbl_mgr.establish_tables(event_types)
        self.db_event_tables = event_types

        # removes "ops_" (first 4 chars) from each string
        self.event_types = ["ops_monitoring:" + ev_str[4:] for ev_str in event_types]

        [self.meas_ref, self.obj_ids] = self.refresh_info_for_type(obj_type)

        #self.json_receiver = json_receiver.JsonReceiver(schema_dict)


    def run(self):

        print "Starting " + self.name

        thread_main(self)

        print "Exiting " + self.name


    # Has the info crawler go update resource information
    def refresh_info_for_type(self, obj_type):

        obj_ids = []

        self.info_crawler.refresh_aggregate_info()
        meas_ref = self.info_crawler.get_meas_ref()

        if obj_type == "node":
            self.info_crawler.refresh_all_nodes_info()
            obj_ids = self.info_crawler.get_all_nodes_of_aggregate()

        elif obj_type == "sliver":
            self.info_crawler.refresh_all_slivers_info()
            #obj_ids = self.info_crawler.get_all_slivers_of_aggregate()

        elif obj_type == "interface":
            self.info_crawler.refresh_all_nodes_info()
            self.info_crawler.refresh_all_interfaces_info() 
            #obj_ids = self.info_crawler.get_all_interfaces_of_aggregate()
           
        elif obj_type == "interfacevlan":
            ic.refresh_all_links_info()
            ic.refresh_all_interfacevlans_info()
            #obj_ids = self.info_crawler.get_all_interfacevlans_of_aggregate()

        else:
            print "Invalid object type", obj_type
            sys.exit(1)

        return meas_ref, obj_ids


    def poll_datastore(self):
        
        req_time = int(time.time()*1000000)

        q = {"filters":{"eventType":self.event_types, 
                        "obj":{"type": self.obj_type,
                               "id": self.obj_ids},
                        "ts": {"gt": self.time_of_last_update}}}

        url = self.meas_ref + "?q=" + str(q)
        url = url.replace(' ', '%20')

        resp = requests.get(url)
             
        if resp:
            self.time_of_last_update = req_time
        
        # need to handle response codes
        return resp.content


    def insert_query(self, rows):
        num_rows = len(rows)
        ins_str = self.insert_base_str

        for i in range(num_rows-1):
            ins_str = ins_str + rows[i]
            ins_str = ins_str + ","
        ins_str = ins_str + rows[num_rows-1] + ";"
         
        print "Insert Query = ", ins_str

        self.psql_lock.acquire()

        cur = self.con.cursor()
        cur.execute(ins_str) # todo try execption block
        self.con.commit() 
        cur.close()

        self.psql_lock.release()

        print "Committed"

    def thread_sleep(self):
        time.sleep(self.sleep_period_sec)


# thread main outside of thread class, is this a good idea? 
def thread_main(sotft): # sotft = SingleObjectTypeFetcherThread
    
    while (True): 

        # poll datastore
        json_text = sotft.poll_datastore()

        try:
            data = json.loads(json_text)
        except Exception, e:
            print "Unable to load response in json\n"+e

        for result in data:
            pprint(result)
            event_type = result["eventType"]
            if event_type.startswith("ops_monitoring:"):
                table_str = "ops_" + event_type[15:]
                id_str = result["id"]
                # if id is of like event:obj_id_that_was_queried,
                # remove event:
                # TODO straighten out protocol with monitoring group
                obj_id = sotft.aggregate_id + ":" + id_str[id_str.find(':')+1:]
                tsdata = result["tsdata"]
                tsdata_insert(sotft.tbl_mgr, obj_id, table_str, tsdata)

        sotft.counter = sotft.counter + 1
    
        if(sotft.counter) > 3:
            break; # Exits loop and thread_main()
        else: 
            sotft.thread_sleep();
  

def tsdata_insert(tbl_mgr, obj_id, table_str, tsdata):
    vals_str = ""
    for tsdata_i in tsdata:
        vals_str += "('" + str(obj_id) + "','" + str(tsdata_i["ts"]) + "','" + str(tsdata_i["v"]) + "'),"

    vals_str = vals_str[:-1] # remove last ','

    tbl_mgr.insert_stmt(table_str, vals_str)
      
def main(): 


    threads = {} 
    db_name = "aggregator"
    config_path = "../config"

    # Event types to query, TODO, less hard coding of this is needed
    node_event_types = ["ops_cpu_util","ops_mem_used_kb","ops_swap_free","ops_disk_part_max_used"]
    interface_event_types = ["ops_rx_bps","ops_tx_bps","ops_rx_pps","ops_tx_pps","ops_rx_dps","ops_tx_dps","ops_rx_eps","ops_tx_eps"]

    tbl_mgr = table_manager.TableManager(db_name, config_path)

    datastore_info_url = "http://127.0.0.1:5000/info/"

    # Set time of last update to 5 minutes in the past
    # change 5000 to 5
    time_of_last_update = (time.time()-(5000*60))*1000000

    # Sleep period in seconds (should be larger than 60 for production)
    sleep_period_sec = 1

    # Aggregate ID to look up in aggregator db
    aggregate_id = "gpo-ig"

    # Object type to look up in aggregator db
    obj_type = "node"

    thread_name = aggregate_id + ":" + obj_type + ":" + "all_events"
    
    event_types = node_event_types

    ic = single_local_datastore_crawler.InfoCrawler(tbl_mgr, datastore_info_url, aggregate_id)    

    threads[thread_name] = SingleObjectTypeFetcherThread(tbl_mgr, ic, thread_name, aggregate_id, obj_type, event_types, sleep_period_sec, time_of_last_update)

    threads[thread_name].start()

    print "Exiting main thread"


if __name__ == "__main__":
    main()
