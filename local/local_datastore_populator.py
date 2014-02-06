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
    def __init__(self, con, aggregate_id, node_id, num_inserts, sleep_period_sec, table_manager, event_table_str_arr, resource_table_str_arr, resource_arr):
        self.con = con;
        self.aggregate_id = aggregate_id
        self.node_id = node_id
        self.num_inserts = num_inserts
        self.sleep_period_sec = sleep_period_sec
        self.event_table_str_arr = event_table_str_arr
        self.resource_table_str_arr = resource_table_str_arr 
        self.resource_arr = resource_arr
        self.table_manager = table_manager

        self.table_manager.establish_tables(event_table_str_arr)
        self.table_manager.establish_tables(resource_table_str_arr) 
   
    def update_resource_tables(self):

        agg_schema_arr = self.table_manager.schema_dict["aggregate"]
        node_schema_arr = self.table_manager.schema_dict["node"]
        iface_schema_arr = self.table_manager.schema_dict["interface"]
        time_sec_epoch = int(time.time()*1000000)
        cur = self.con.cursor()            
        s = "','" # separator for all (incl numerics)
        for agg_dict in self.resource_arr:

            # insert each node to aggregate table
            for node_key in agg_dict["nodes"]: 
                node_dict = agg_dict["nodes"][node_key]
                ins_str = "INSERT INTO aggregate VALUES ('"
                # loop through each of agg schema, skip last bc it is a dict
                for key_i in range(len(agg_schema_arr)-1):
                    ins_str += agg_dict[agg_schema_arr[key_i][0]] + s
                
                ins_str += node_dict["id"] + "')"
                cur.execute(ins_str)
                self.con.commit()
                
                # insert each interface of node to node table
                for iface_key in node_dict["interfaces"]:
                    iface_dict = node_dict["interfaces"][iface_key]
                    ins_str = "INSERT INTO node VALUES ('"
                    for key_i in range(len(node_schema_arr)-1):
                        ins_str += node_dict[node_schema_arr[key_i][0]] + s

                    ins_str += iface_dict["id"] + "')"
                    cur.execute(ins_str)
                    self.con.commit()

                    # insert each interface into interface table
                    ins_str = "INSERT INTO interface VALUES ('" 
                    for key_i in range(len(iface_schema_arr)):
                        ins_str +=iface_dict[iface_schema_arr[key_i][0]] + s

                    ins_str = ins_str[:-2] + ")" # remove last 2 of ',' add )
                    cur.execute(ins_str)
                    self.con.commit()
                    
        cur.close()

    def run_node_inserts(self, table_str):

        for i in range(self.num_inserts):
            time_sec_epoch = int(time.time()*1000000)
            percent_mem_used = get_data(table_str)

            ins_str = "INSERT INTO " + table_str + " VALUES ('" + self.aggregate_id + "', '" + self.node_id + "'," + str(time_sec_epoch) + "," + str(percent_mem_used) + ");" 
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

def main():

    (num_ins, per_sec) = arg_parser(sys.argv)

    # 404 is not found and the area code in atlanta #TheGoalIsGEC19
    aggregate_id="404-ig" 
    node_id="pc1"
    table_str = "mem_used"

    event_table_str_arr = [table_str]
    resource_table_str_arr = ["aggregate","node","interface"]

    # For table manager
    db_templates = json.load(open("../config/db_templates"))
    event_types = json.load(open("../config/event_types"))
    resource_types = json.load(open("../config/resource_types"))
    db_con_str = "dbname=local user=rirwin";
    con = psycopg2.connect(db_con_str);

    tm = table_manager.TableManager(con, db_templates, event_types, resource_types)
    # End table manager

    # Info about this local datastore populator
    url_local_agg_info = "http://127.0.0.1:5000/info/aggregate/"

    resource_arr = []
    agg1_dict = {}
    agg1_dict["$schema"] = "http://unis.incntre.iu.edu/schema/20120709/domain#"
    agg1_dict["id"] = "404-ig"
    agg1_dict["selfRef"] = url_local_agg_info + agg1_dict["id"]
    agg1_dict["urn"] = "urn=404-ig+urn"
    agg1_dict["ts"] = str(int(time.time()*1000000))
    agg1_dict["nodes"] = {}
    
    agg1_pc1_dict = {}
    agg1_pc1_dict["$schema"] = "http://unis.incntre.iu.edu/schema/20120709/node#"
    agg1_pc1_dict["id"] = "pc1"
    agg1_pc1_dict["selfRef"] = url_local_agg_info + agg1_dict["id"] + "/" + agg1_pc1_dict["id"]
    agg1_pc1_dict["urn"] = "urn=404-ig+pc1+urn"
    agg1_pc1_dict["ts"] = str(int(time.time()*1000000))
    agg1_pc1_dict["mem_total_kb"] = str(2*1000000)
    agg1_pc1_dict["interfaces"] = {}

    agg1_pc1_eth0_dict = {}
    agg1_pc1_eth0_dict["$schema"] = "http://unis.incntre.iu.edu/schema/20120709/port#"
    agg1_pc1_eth0_dict["id"] = "eth0"
    agg1_pc1_eth0_dict["selfRef"] = url_local_agg_info + agg1_dict["id"] + "/" + agg1_pc1_dict["id"] + "/" + agg1_pc1_eth0_dict["id"]
    agg1_pc1_eth0_dict["urn"] = "urn=404-ig+pc1+eth0+urn"
    agg1_pc1_eth0_dict["ts"] = str(int(time.time()*1000000))
    agg1_pc1_eth0_dict["role"] = "control"
    agg1_pc1_eth0_dict["max_bps"] = str(10000000)
    agg1_pc1_eth0_dict["max_pps"] = str(1000000)
    agg1_pc1_eth0_dict["mac_addr"] = "12:34:56:67:89:01"
    agg1_pc1_eth0_dict["ip_addr"] = "192.1.1.101"

    # insert other interfaces for pc1 here
    # agg1_pc1_eth1_dict = {} ...
    agg1_pc1_dict["interfaces"]["eth0"] = agg1_pc1_eth0_dict
    
    # Then add to agg1_pc1_dict
    # agg1_pc1_dict["interfaces"]["eth1"] = agg1_pc1_eth1_dict

    # pc1 is complete, add it to agg1_dict
    agg1_dict["nodes"]["pc1"] = agg1_pc1_dict

    # insert other nodes for aggregate 404-ig here
    #agg1_pc2_dict = {} ...
    
    # insert interfaces to pc2 as above 
    # (be careful with reusing dicts in python)
    # agg1_pc2_dict["interfaces"]["eth1"] = agg1_pc2_eth1_dict

    # insert node to agg1_dict
    # agg1_dict["nodes"]["pc1"] = agg1_pc1_dict  

    resource_arr.append(agg1_dict)

    #pprint(resource_arr)

    ldp = LocalDatastorePopulator(con, aggregate_id, node_id, num_ins, per_sec, tm, event_table_str_arr, resource_table_str_arr, resource_arr)

    ldp.update_resource_tables()


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
