#!/usr/bin/python

import psycopg2
import time
import psutil
import sys
import json
from pprint import pprint as pprint

#todo threading similar to single noun fetcher

sys.path.append("../common/db-tools")
import table_manager

# TODO add locking from threading in case multiple LocalStorePopulators

# TODO make class LocalStorePopulator for this class to inherit
# Intent is for each table to have its own object getting data
class LocalDatastorePopulator:
    def __init__(self, con, aggregate_id, node_id, num_inserts, sleep_period_sec, table_manager, data_table_str_arr, info_table_str_arr):
        self.con = con;
        self.aggregate_id = aggregate_id
        self.node_id = node_id
        self.num_inserts = num_inserts
        self.sleep_period_sec = sleep_period_sec
        self.data_table_str_arr = data_table_str_arr
        self.info_table_str_arr = info_table_str_arr 
        self.table_manager = table_manager

        self.table_manager.establish_tables(data_table_str_arr)
        self.table_manager.establish_tables(info_table_str_arr) 
   
    def run_node_inserts(self, table_str):

        for i in range(self.num_inserts):
            time_sec_epoch = int(time.time()*1000000)
            percent_mem_used = get_data(table_str)

            ins_str = "INSERT INTO " + table_str + " VALUES ('" + self.node_id + "'," + str(time_sec_epoch) + "," + str(percent_mem_used) + ");" 
            cur = self.con.cursor()            
            cur.execute(ins_str)
            self.con.commit()
            cur.close()

            time.sleep(self.sleep_period_sec)    

def get_data(table_str): 
        if table_str == "mem_used":
            return get_mem_util()

def get_mem_util():
    # despite being called virtual, this is physical memory
    mem = psutil.virtual_memory() 
    return mem.used

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

def info_insert(con, table_str, row_arr):
    val_str = "'"
    for val in row_arr:
        val_str += val + "','" # join won't do this
    val_str = val_str[:-2] # remove last 2 of ','
    cur = con.cursor()
    print val_str
    cur.execute("insert into " + table_str + " values (" + val_str + ")")
    con.commit()
    cur.close()


def generate_and_insert_config_data(data_schema, info_schema):
    # 404 is not found and the area code in atlanta #TheGoalIsGEC19
    aggregate_id="404-ig" 
    node_id="404-ig-pc1"
    table_str = "mem_used"

    data_table_str_arr = [table_str]
    info_table_str_arr = ["aggregate","resource","port"]

    # For table manager    
    db_con_str = "dbname=local user=rirwin";
    con = psycopg2.connect(db_con_str);

    tm = table_manager.TableManager(con, data_schema, info_schema)
    tm.drop_tables(data_schema.keys())
    tm.drop_tables(info_schema.keys())
    tm.establish_tables(data_schema.keys())
    tm.establish_tables(info_schema.keys())
    # End table manager

    # Info about this local datastore populator
    url_local_info = "http://127.0.0.1:5000/info/"
    url_local_data = "http://127.0.0.1:5000/data/"

    agg1 = []
    agg1.append("http://www.gpolab.bbn.com/monitoring/schema/20140131/aggregate#")
    agg1.append("404-ig")
    agg1.append(url_local_info + "aggregate/" + agg1[1])
    agg1.append("urn=404-ig+urn")
    agg1.append(str(int(time.time()*1000000)))
    agg1.append(url_local_data)

    resource1 = []
    resource1.append("http://unis.incntre.iu.edu/schema/20120709/resource#")
    resource1.append("404-ig-pc1")
    resource1.append(url_local_info + "resource/" + resource1[1])
    resource1.append("urn=404-ig+pc1+urn")
    resource1.append(str(int(time.time()*1000000)))
    resource1.append(str(2*1000000)) # mem_total_kb

    sliver1 = []
    sliver1.append("http://www.gpolab.bbn.com/monitoring/schema/20140131/sliver#")
    sliver1.append("404-ig-slv1")
    sliver1.append(url_local_info + "sliver/" + sliver1[1])
    sliver1.append("urn=404-ig+slv1+urn")
    sliver1.append(str(int(time.time()*1000000)))

    port1 = []
    port1.append("http://unis.incntre.iu.edu/schema/20120709/port#")
    port1.append("404-ig-pc1:eth0")
    port1.append(url_local_info + "interface/" + port1[1])
    port1.append("urn=404-ig+pc1+eth0+urn")
    port1.append(str(int(time.time()*1000000)))
    port1.append("ipv4")
    port1.append("192.1.242.140")
    port1.append("control")
    port1.append(str(10000000)) #max bps
    port1.append(str(1000000)) #max pps

    aggres1 = []
    aggres1.append("404-ig-pc1")
    aggres1.append("404-ig")
    aggres1.append("http://gpolab.bbn.com/404-ig-pc1")
    aggres1.append(url_local_info + "node/" + aggres1[0])

    aggsliv1 = []
    aggsliv1.append("404-ig-slv1")
    aggsliv1.append("404-ig")
    aggsliv1.append("http://gpolab.bbn.com/sliver1:404-ig-slv1")
    aggsliv1.append(url_local_info + "sliver/" + aggsliv1[0])
                 
    resport1 = []
    resport1.append("404-ig-pc1:eth0")
    resport1.append("404-ig-pc1")
    resport1.append("http://gpolab.bbn.com/sliver1:404-ig-pc1")
    resport1.append(url_local_info + "interface/" + resport1[0])

    info_insert(con, "aggregate", agg1)
    info_insert(con, "resource", resource1)
    info_insert(con, "sliver", sliver1)
    info_insert(con, "port", port1)
    info_insert(con, "aggregate_resource",aggres1)
    info_insert(con, "resource_port", resport1)
    info_insert(con, "aggregate_sliver", aggsliv1)

def main():

    (num_ins, per_sec) = arg_parser(sys.argv)

    # 404 is not found and the area code in atlanta #TheGoalIsGEC19
    aggregate_id="404-ig" 
    node_id="404-ig-pc1"
    table_str = "mem_used"

    data_table_str_arr = [table_str]
    info_table_str_arr = ["aggregate","resource","port"]

    db_con_str = "dbname=local user=rirwin";
    con = psycopg2.connect(db_con_str);
    data_schema = json.load(open("../config/data_schema"))
    info_schema = json.load(open("../config/info_schema"))
    tm = table_manager.TableManager(con, data_schema, info_schema)

    ldp = LocalDatastorePopulator(con, aggregate_id, node_id, num_ins, per_sec, tm, data_table_str_arr, info_table_str_arr)
    

    #ldp.update_resource_tables()


    #
    # TODO pass a dictionary and have it iterate through keys and pass
    # to this function

    ldp.run_node_inserts("mem_used")
        
    
    cur = con.cursor();
    cur.execute("select count(*) from " + table_str);
    print "num entries", cur.fetchone()[0]

    cur.close();
    con.close();

if __name__ == "__main__":
    main()
