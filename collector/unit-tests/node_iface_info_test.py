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

sys.path.append("../../common/")
import table_manager
sys.path.append("../")
import single_local_datastore_crawler as sldc

def main():
    threads = {} 
    db_type = "aggregator"
    config_path = "../../config"

    # Event types to query, TODO, less hard coding of this is needed
    node_event_types = ["ops_cpu_util","ops_mem_used_kb","ops_swap_free","ops_disk_part_max_used"]
    interface_event_types = ["ops_rx_bps","ops_tx_bps","ops_rx_pps","ops_tx_pps","ops_rx_dps","ops_tx_dps","ops_rx_eps","ops_tx_eps"]

    tbl_mgr = table_manager.TableManager(db_type, config_path)
    tbl_mgr.drop_tables(tbl_mgr.schema_dict.keys())


    # Info url
    datastore_info_url = "http://datastore.utah.geniracks.net:5001/info/"

    # Aggregate ID to look up in aggregator db
    aggregate_id = "ig-utah"


    crawler = sldc.SingleLocalDatastoreCrawler(tbl_mgr, datastore_info_url, aggregate_id)    


    tbl_mgr.establish_tables(tbl_mgr.info_schema.keys())

    crawler.refresh_aggregate_info()
    crawler.refresh_all_nodes_info()
    crawler.refresh_all_interfaces_info()



if __name__ == "__main__":
    main()
