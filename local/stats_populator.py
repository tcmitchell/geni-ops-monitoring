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

import psycopg2
import time
import psutil
import sys
import json
import threading
from pprint import pprint as pprint


common_path = "../common/"

sys.path.append(common_path)
import table_manager


class StatsPopulator(threading.Thread):
    def __init__(self, tbl_mgr, obj_id, num_inserts, sleep_period_sec, event_types_arr):
        threading.Thread.__init__(self)
        self.tbl_mgr = tbl_mgr # ldp = local datastore populator
        self.obj_id = obj_id
        self.num_inserts = num_inserts
        self.sleep_period_sec = sleep_period_sec
        self.event_types_arr = event_types_arr

    def run(self):

        print "Starting thread for populating stats about" + self.obj_id
        
        self.run_stats_main()

        print "Exiting thread for populating stats about" + self.obj_id

    def run_stats_main(self):

        for i in range(self.num_inserts):
            for ev_t in self.event_types_arr:
                self.stat_insert(ev_t)
            time.sleep(self.sleep_period_sec)    

    def stat_insert(self, ev_t):    
        
        time_sec_epoch = int(time.time()*1000000)
        data = get_data(ev_t)
        if data != None:
            val_str = "'" + self.obj_id + "'," + str(time_sec_epoch) + "," + str(data) 
            #ins_str = "INSERT INTO " + ev_t + " VALUES ('" + self.obj_id + "'," + str(time_sec_epoch) + "," + str(data) + ");" 
            self.tbl_mgr.insert_stmt("ops_" + ev_t, val_str)
        else:
            print "No data received for event_type:", ev_t

# Simple calls to get data
# These should be non-blocking
def get_data(event_type):        
    if event_type == "mem_used":
        return psutil.virtual_memory().used
    elif event_type == "swap_free":
        return (100.0 - psutil.swap_memory().percent)
    elif event_type == "cpu_util":
        return psutil.cpu_percent(interval=0)
    elif event_type == "disk_part_max_used":
        return psutil.disk_usage('/').percent
    elif event_type == "rx_bytes":
        return psutil.network_io_counters().bytes_recv
    elif event_type == "tx_bytes":
        return psutil.network_io_counters().bytes_sent
    else: # TODO add more
        return None

def arg_parser(argv):

    if (len(argv) != 3):
        print "Provide exactly two args: (1) for num inserts, (2) for period between inserts in seconds"
        sys.exit(1)

    num_ins = 0

    try:
        num_ins = int(argv[1])
    except ValueError:
        print "Not a postive int. Provide number of inserts for run of program."
        sys.exit(1)

    per_sec = 0

    try:
        per_sec = float(argv[2])
    except ValueError:
        print "Not a postive float. Provide period of time in seconds between inserts."
        sys.exit(1)

    if (per_sec < 0 or num_ins < 0):
        print "Both numeric args should be positive"
        sys.exit(1)

    return num_ins, per_sec



def main():

    (num_ins, per_sec) = arg_parser(sys.argv)


    db_name = "local"
    config_path = "../config/"
    tbl_mgr = table_manager.TableManager(db_name, config_path)
    

    node_id="instageni.gpolab.bbn.com_node_pc1"
    event_types_arr = ["mem_used","cpu_util","disk_part_max_used"]
    nsp = StatsPopulator(tbl_mgr, node_id, num_ins, per_sec, event_types_arr)
 
    iface_id="instageni.gpolab.bbn.com_interface_pc1:eth0"
    event_types_arr = ["rx_bytes","tx_bytes"]
    isp = StatsPopulator(tbl_mgr, iface_id, num_ins, per_sec, event_types_arr)

    nsp.start()
    isp.start()
    
    cur = tbl_mgr.con.cursor();
    cur.execute("select count(*) from ops_" + event_types_arr[0]);
    print "num entries", cur.fetchone()[0]

    cur.close();

    threads = []
    threads.append(nsp)
    threads.append(isp)

    # join all threads
    for t in threads:
        t.join()

    tbl_mgr.close_con();
    
if __name__ == "__main__":
    main()
