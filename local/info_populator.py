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

class InfoPopulator(threading.Thread):
    def __init__(self, ldp_helper):
        # ldp = local datastore populator
        self.ldp_helper = ldp_helper 

    def ins_fake_info(self):
         info_dict = {}
         url_local_info = "http://127.0.0.1:5000/info/"
         url_local_data = "http://127.0.0.1:5000/data/"
         
         agg1 = []
         agg1.append("http://www.gpolab.bbn.com/monitoring/schema/20140131/aggregate#")
         agg1.append("404-ig")
         agg1.append(url_local_info + "aggregate/" + agg1[1])
         agg1.append("urn=404-ig+urn")
         agg1.append(str(int(time.time()*1000000)))
         agg1.append(url_local_data)
         
         info_dict["aggregate"] = agg1
         
         node1 = []
         node1.append("http://unis.incntre.iu.edu/schema/20120709/node#")
         node1.append("404-ig-pc1")
         node1.append(url_local_info + "node/" + node1[1])
         node1.append("urn=404-ig+pc1+urn")
         node1.append(str(int(time.time()*1000000)))
         node1.append(str(2*1000000)) # mem_total_kb
         
         info_dict["node"] = node1
         
         sliver1 = []
         sliver1.append("http://www.gpolab.bbn.com/monitoring/schema/20140131/sliver#")
         sliver1.append("404-ig-slv1")
         sliver1.append(url_local_info + "sliver/" + sliver1[1])
         sliver1.append("urn=404-ig+slv1+urn")
         sliver1.append(str(int(time.time()*1000000)))
         
         info_dict["sliver"] = sliver1
         
         interface1 = []
         interface1.append("http://unis.incntre.iu.edu/schema/20120709/port#")
         interface1.append("404-ig-pc1:eth0")
         interface1.append(url_local_info + "interface/" + interface1[1])
         interface1.append("urn=404-ig+pc1+eth0+urn")
         interface1.append(str(int(time.time()*1000000)))
         interface1.append("ipv4")
         interface1.append("192.1.242.140")
         interface1.append("control")
         interface1.append(str(10000000)) #max bps
         interface1.append(str(1000000)) #max pps
         
         info_dict["interface"] = interface1
         
         aggres1 = []
         aggres1.append("404-ig-pc1")
         aggres1.append("404-ig")
         aggres1.append("http://gpolab.bbn.com/404-ig-pc1")
         aggres1.append(url_local_info + "node/" + aggres1[0])
         
         info_dict["aggregate_resource"] = aggres1
         
         aggsliv1 = []
         aggsliv1.append("404-ig-slv1")
         aggsliv1.append("404-ig")
         aggsliv1.append("http://gpolab.bbn.com/sliver1:404-ig-slv1")
         aggsliv1.append(url_local_info + "sliver/" + aggsliv1[0])
         
         info_dict["aggregate_sliver"] = aggsliv1
         
         nodeiface1 = []
         nodeiface1.append("404-ig-pc1:eth0")
         nodeiface1.append("404-ig-pc1")
         nodeiface1.append("http://gpolab.bbn.com/sliver1:404-ig-pc1")
         nodeiface1.append(url_local_info + "interface/" + nodeiface1[0])
         
         info_dict["node_interface"] = nodeiface1

         for k in info_dict:
             info_insert(self.ldp_helper, k, info_dict[k])

def info_insert(ldp_helper, table_str, row_arr):
    val_str = "'"

    for val in row_arr:
        val_str += val + "','" # join won't do this

    val_str = val_str[:-2] # remove last 2 of ','
    cur = ldp_helper.con.cursor()
    ldp_helper.tbl_mgr.db_lock.acquire()
    cur.execute("insert into " + table_str + " values (" + val_str + ")")
    ldp_helper.con.commit()
    ldp_helper.tbl_mgr.db_lock.release()
    cur.close()

def main():

    db_con_str = "dbname=local user=rirwin";
    con = psycopg2.connect(db_con_str);
    data_schema = json.load(open("../config/data_schema"))
    info_schema = json.load(open("../config/info_schema"))
    tbl_mgr = table_manager.TableManager(con, data_schema, info_schema)

    tbl_mgr.drop_tables(info_schema.keys())
    tbl_mgr.establish_tables(info_schema.keys())
    

    psql_lock = threading.Lock()

    # local datastore populator helper
    ldph = local_datastore_populator.LocalDatastorePopulator(con, psql_lock, tbl_mgr)

    ip = InfoPopulator(ldph)

    ip.ins_fake_info()
   
    
    cur = con.cursor();
    cur.execute("select count(*) from aggregate");
    print "num entries", cur.fetchone()[0]

    cur.close();
    con.close();
    
if __name__ == "__main__":
    main()
