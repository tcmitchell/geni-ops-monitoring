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
import sys
import requests
import ConfigParser
from pprint import pprint as pprint
import single_local_datastore_crawler as sldc
sys.path.append("../../common/")
import table_manager
import single_obj_type_fetcher_thread as sotft

def main(): 

    threads = {} 
    db_type = "collector"
    config_path = "../../config"

    # Event types to query, TODO, less hard coding of this is needed
    node_event_types = ["ops_cpu_util","ops_mem_used_kb","ops_swap_free","ops_disk_part_max_used"]
    interface_event_types = ["ops_rx_bps","ops_tx_bps","ops_rx_pps","ops_tx_pps","ops_rx_dps","ops_tx_dps","ops_rx_eps","ops_tx_eps"]

    tbl_mgr = table_manager.TableManager(db_type, config_path)
    tbl_mgr.drop_tables(tbl_mgr.schema_dict.keys())

    cp = ConfigParser.ConfigParser()
    cp.read(config_path + "/collector_operator.conf") 

    # Gets multiple datastores from the configuration file
    datastores_dict = json.loads(cp.get("main","datastores_dict"))

    sleep_period_sec = int(json.loads(cp.get("main","sleep_period_sec")))
    sleep_period_sec = 2
    # time of last update set to 15 minutes in the past
    time_of_last_update = int((time.time() - 15*60)*1000000)

    # Set to true, <don't care>, and remove time_of_last_update
    run_indefinitely, stop_cnt, time_of_last_update = False, 2, 0

    for agg_id in datastores_dict:

        # Aggregate ID to look up in collector db
        aggregate_id = agg_id
        datastore_info_url = datastores_dict[agg_id]

        # Object type to look up in collector db
        obj_type = "node"
        thread_name = aggregate_id + ":" + obj_type + ":" + "all_events"
        event_types = node_event_types

        print datastore_info_url

        # Crawl datastore for info population
        crawler = sldc.SingleLocalDatastoreCrawler(tbl_mgr, datastore_info_url, aggregate_id)    
        
        # TODO put in function to avoid calling all of these
        crawler.refresh_aggregate_info()
        crawler.refresh_all_nodes_info()
        crawler.refresh_all_links_info()
        crawler.refresh_all_slivers_info()
        crawler.refresh_all_interfaces_info()
        crawler.refresh_all_interfacevlans_info()


        threads[thread_name] = sotft.SingleObjectTypeFetcherThread(tbl_mgr, thread_name, aggregate_id, obj_type, event_types, sleep_period_sec, time_of_last_update, run_indefinitely, stop_cnt)
        
        # Another thread about interface data
        obj_type = "interface"
        event_types = interface_event_types
        thread_name = aggregate_id + ":" + obj_type + ":" + "all_events"
        
        threads[thread_name] = sotft.SingleObjectTypeFetcherThread(tbl_mgr, thread_name, aggregate_id, obj_type, event_types, sleep_period_sec, time_of_last_update, run_indefinitely, stop_cnt)
        
        
    for thread_name in threads:
        threads[thread_name].start()

    print threads, "running"

    for thread_name in threads:
        threads[thread_name].join()
    
    print "Exiting main thread"


if __name__ == "__main__":
    main()
