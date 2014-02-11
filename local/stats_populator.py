#!/usr/bin/python

import psycopg2
import time
import psutil
import sys
import json
import threading
from pprint import pprint as pprint

sys.path.append("../common/")
import table_manager
import local_datastore_populator

class StatsPopulator(threading.Thread):
    def __init__(self, ldp_helper, obj_id, num_inserts, sleep_period_sec, event_types_arr):
        threading.Thread.__init__(self)
        self.ldp_helper = ldp_helper # ldp = local datastore populator
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
            ins_str = "INSERT INTO " + ev_t + " VALUES ('" + self.obj_id + "'," + str(time_sec_epoch) + "," + str(data) + ");" 

            self.ldp_helper.psql_lock.acquire()
            cur = self.ldp_helper.con.cursor()            
            cur.execute(ins_str)
            self.ldp_helper.con.commit() # could do bulk commits
            cur.close()
            self.ldp_helper.psql_lock.release()
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
    elif event_type == "ctrl_net_rx_bytes":
        return psutil.network_io_counters().bytes_recv
    elif event_type == "ctrl_net_tx_bytes":
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

    # 404 is not found and the area code in atlanta #TheGoalIsGEC19
    node_id="404-ig-pc1"
    event_types_arr = ["mem_used","cpu_util","disk_part_max_used"]

    db_con_str = "dbname=local user=rirwin";
    con = psycopg2.connect(db_con_str);
    data_schema = json.load(open("../config/data_schema"))
    info_schema = json.load(open("../config/info_schema"))
    tbl_mgr = table_manager.TableManager(con, data_schema, info_schema)

    psql_lock = threading.Lock()

    # local datastore populator helper
    ldph = local_datastore_populator.LocalDatastorePopulator(con, psql_lock, tbl_mgr)


    sp = StatsPopulator(ldph, node_id, num_ins, per_sec, event_types_arr)

    #sp.run_stats_main()
    sp.start()
    
    cur = con.cursor();
    cur.execute("select count(*) from " + event_types_arr[0]);
    print "num entries", cur.fetchone()[0]

    cur.close();
    #con.close();
    
if __name__ == "__main__":
    main()
