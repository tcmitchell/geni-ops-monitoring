#!/usr/bin/python

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

class InfoPopulator(threading.Thread):
    def __init__(self, tbl_mgr):

        self.tbl_mgr = tbl_mgr 

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
         sliver1.append("instageni.gpolab.bbn.com_sliver_26947")
         sliver1.append(url_local_info + "sliver/" + sliver1[1])
         sliver1.append("urn:publicid:IDN+instageni.gpolab.bbn.com+sliver+26947")
         sliver1.append("30752b06-8ea8-11e3-8d30-000000000000") #uuid
         sliver1.append(str(int(time.time()*1000000))) #current ts
         sliver1.append("urn:publicid:IDN+instageni.gpolab.bbn.com+authority+cm") # agg_urn
         sliver1.append("https://datastore.instageni.gpolab.bbn.com/aggregates/gpo-ig") # agg_href
         sliver1.append("urn:publicid:IDN+ch.geni.net:gpo-infra+slice+tuptyexclusive") # slice_urn
         sliver1.append("8c6b97fa-493b-400f-95ee-19accfaf4ae8") #slice uuid
         sliver1.append("urn:publicid:IDN+ch.geni.net+user+tupty") # creator
         sliver1.append(str(int(1391626683000000))) # created
         sliver1.append(str(int(1391708989000000))) # expires

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

         slivernode1 = []
         slivernode1.append("instageni.gpolab.bbn.com_node_pc1")
         slivernode1.append("instageni.gpolab.bbn.com_sliver_26947")
         slivernode1.append("urn:publicid:IDN+instageni.gpolab.bbn.com+node+pc1")
         slivernode1.append(url_local_info + "node/" + nodeiface1[0])
         
         info_dict["sliver_node"] = slivernode1

         for k in info_dict:
             info_insert(self.tbl_mgr, k, info_dict[k])

def info_insert(tbl_mgr, table_str, row_arr):
    val_str = "'"

    for val in row_arr:
        val_str += val + "','" # join won't do this

    val_str = val_str[:-2] # remove last 2 of 3 chars: ','

    tbl_mgr.insert_stmt(table_str, val_str)


def main():

   
    db_name = "local"
    config_path = "../config"

    tbl_mgr = table_manager.TableManager(db_name, config_path)

    data_schema = json.load(open("../config/data_schema"))
    info_schema = json.load(open("../config/info_schema"))
   

    tbl_mgr.drop_tables(info_schema.keys())
    tbl_mgr.establish_tables(info_schema.keys())
    ip = InfoPopulator(tbl_mgr)

    ip.ins_fake_info()
   
    
    cur = tbl_mgr.con.cursor();
    cur.execute("select count(*) from aggregate");
    print "num entries", cur.fetchone()[0]

    cur.close();
    tbl_mgr.close_con();
    
if __name__ == "__main__":
    main()
