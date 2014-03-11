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
import psutil
import sys
import json
import threading
from pprint import pprint as pprint


common_path = "../common/"

sys.path.append(common_path)
import table_manager

class InfoPopulator(threading.Thread):
    def __init__(self, tbl_mgr, url_base):

        self.tbl_mgr = tbl_mgr 
        self.url_base = url_base

    def ins_fake_info(self): 
         info_dict = {}
         url_local_info = self.url_base + "/info/"
         url_local_data = self.url_base + "/data/"
         url_opsconfig_local_info = self.url_base + "/info/"
         
         agg1 = []
         agg1.append("http://www.gpolab.bbn.com/monitoring/schema/20140131/aggregate#")
         agg1.append("gpo-ig")
         agg1.append(url_local_info + "aggregate/" + agg1[1])
         agg1.append("urn:publicid:IDN+instageni.gpolab.bbn.com+authority+cm")
         agg1.append(str(int(time.time()*1000000)))
         agg1.append(url_local_data)
         
         info_insert(self.tbl_mgr, "ops_aggregate", agg1)

         
         node1 = []
         node1.append("http://unis.incntre.iu.edu/schema/20120709/node#")
         node1.append("instageni.gpolab.bbn.com_node_pc1")
         node1.append(url_local_info + "node/" + node1[1])
         node1.append("urn:publicid:IDN+instageni.gpolab.bbn.com+node+pc1")
         node1.append(str(int(time.time()*1000000)))
         node1.append(str(2*1000000)) # mem_total_kb
         
         info_insert(self.tbl_mgr, "ops_node", node1)


         node2 = []
         node2.append("http://unis.incntre.iu.edu/schema/20120709/node#")
         node2.append("instageni.gpolab.bbn.com_node_pc2")
         node2.append(url_local_info + "node/" + node2[1])
         node2.append("urn:publicid:IDN+instageni.gpolab.bbn.com+node+pc2")
         node2.append(str(int(time.time()*1000000)))
         node2.append(str(2*1000000)) # mem_total_kb
         
         info_insert(self.tbl_mgr, "ops_node", node2)


         sliver1 = []
         sliver1.append("http://www.gpolab.bbn.com/monitoring/schema/20140131/sliver#")
         sliver1.append("instageni.gpolab.bbn.com_sliver_26947")
         sliver1.append(url_local_info + "sliver/" + sliver1[1])
         sliver1.append("urn:publicid:IDN+instageni.gpolab.bbn.com+sliver+26947")
         sliver1.append("30752b06-8ea8-11e3-8d30-000000000000") #uuid
         sliver1.append(str(int(time.time()*1000000))) #current ts
         sliver1.append("urn:publicid:IDN+instageni.gpolab.bbn.com+authority+cm") # agg_urn
         sliver1.append(url_local_info + "aggregate/gpo-ig") # agg_href
         sliver1.append("urn:publicid:IDN+ch.geni.net:gpo-infra+slice+tuptyexclusive") # slice_urn
         sliver1.append("8c6b97fa-493b-400f-95ee-19accfaf4ae8") #slice uuid
         sliver1.append("urn:publicid:IDN+ch.geni.net+user+tupty") # creator
         sliver1.append(str(int(1391626683000000))) # created
         sliver1.append(str(int(1391708989000000))) # expires

         info_insert(self.tbl_mgr, "ops_sliver", sliver1)

                   
         sliver2 = []
         sliver2.append("http://www.gpolab.bbn.com/monitoring/schema/20140131/sliver#")
         sliver2.append("instageni.gpolab.bbn.com_sliver_26950")
         sliver2.append(url_local_info + "sliver/" + sliver2[1])
         sliver2.append("urn:publicid:IDN+instageni.gpolab.bbn.com+sliver+26950")
         sliver2.append("30752b06-8ea8-11e3-8d30-000005000000") #uuid
         sliver2.append(str(int(time.time()*1000000))) #current ts
         sliver2.append("urn:publicid:IDN+instageni.gpolab.bbn.com+authority+cm") # agg_urn
         sliver2.append(url_local_info + "aggregate/gpo-ig") # agg_href
         sliver2.append("urn:publicid:IDN+ch.geni.net:gpo-infra+slice+tuptyexclusive2") # slice_urn
         sliver2.append("8c6b97fa-493b-400f-95ee-19accfaf4ae8") #slice uuid
         sliver2.append("urn:publicid:IDN+ch.geni.net+user+tupty") # creator
         sliver2.append(str(int(1391626683000000))) # created
         sliver2.append(str(int(1391708989000000))) # expires   

         info_insert(self.tbl_mgr, "ops_sliver", sliver2)


         link1 = []
         link1.append("http://www.gpolab.bbn.com/monitoring/schema/20140131/link#")
         link1.append("arbitrary_link_id_001")
         link1.append(url_local_info + "link/" + link1[1])
         link1.append("urn:publicid:IDN+instageni.gpolab.bbn.com+link_id_001")
         link1.append(str(int(time.time()*1000000)))
         
         info_insert(self.tbl_mgr, "ops_link", link1)


         interface1 = []
         interface1.append("http://unis.incntre.iu.edu/schema/20120709/port#")
         interface1.append("instageni.gpolab.bbn.com_interface_pc1:eth1")
         interface1.append(url_local_info + "interface/" + interface1[1])
         interface1.append("urn:publicid:IDN+instageni.gpolab.bbn.com+interface+pc1:eth1")
         interface1.append(str(int(time.time()*1000000)))
         interface1.append("ipv4") # addr type
         interface1.append("192.1.242.140") # addr
         interface1.append("control") # role
         interface1.append(str(10000000)) #max bps
         interface1.append(str(1000000)) #max pps
         
         info_insert(self.tbl_mgr, "ops_interface", interface1)

         
         interface2 = []
         interface2.append("http://unis.incntre.iu.edu/schema/20120709/port#")
         interface2.append("instageni.gpolab.bbn.com_interface_pc2:eth1")
         interface2.append(url_local_info + "interface/" + interface2[1])
         interface2.append("urn:publicid:IDN+instageni.gpolab.bbn.com+interface+pc2:eth1")
         interface2.append(str(int(time.time()*1000000)))
         interface2.append("ipv4") # addr type
         interface2.append("192.1.242.140") # addr
         interface2.append("control") # role
         interface2.append(str(10000000)) #max bps
         interface2.append(str(1000000)) #max pps
         
         info_insert(self.tbl_mgr, "ops_interface", interface2)


         interfacevlan1 = []
         interfacevlan1.append("http://www.gpolab.bbn.com/monitoring/schema/20140131/port-vlan#")
         interfacevlan1.append("instageni.gpolab.bbn.com_interface_pc1:eth1:1750")
         interfacevlan1.append(url_local_info + "interfacevlan/" + interfacevlan1[1])
         interfacevlan1.append("urn:publicid:IDN+instageni.gpolab.bbn.com+interface+pc1:eth1:1750")
         interfacevlan1.append(str(int(time.time()*1000000)))
         interfacevlan1.append(str(1750)) # tag type
         interfacevlan1.append("urn:publicid:IDN+instageni.gpolab.bbn.com+interface+pc1:eth1") # port urn
         interfacevlan1.append(url_local_info + "interface/" + interface1[1]) # port href

         info_insert(self.tbl_mgr, "ops_interfacevlan", interfacevlan1)


         interfacevlan2 = []
         interfacevlan2.append("http://www.gpolab.bbn.com/monitoring/schema/20140131/port-vlan#")
         interfacevlan2.append("instageni.gpolab.bbn.com_interface_pc2:eth1:1750")
         interfacevlan2.append(url_local_info + "interfacevlan/" + interfacevlan2[1])
         interfacevlan2.append("urn:publicid:IDN+instageni.gpolab.bbn.com+interface+pc2:eth1:1750")
         interfacevlan2.append(str(int(time.time()*1000000)))
         interfacevlan2.append(str(1750)) # tag type
         interfacevlan2.append("urn:publicid:IDN+instageni.gpolab.bbn.com+interface+pc2:eth1") # port urn
         interfacevlan2.append(url_local_info + "interface/" + interface2[1]) # port href
         info_insert(self.tbl_mgr, "ops_interfacevlan", interfacevlan2)



         slice1 = []
         slice1.append("http://www.gpolab.bbn.com/monitoring/schema/20140131/slice#")
         slice1.append("ch.geni.net_gpo-infra_slice_tuptyexclusive")
         slice1.append(url_local_info + "slice/" + slice1[1])
         slice1.append("urn:publicid:IDN+ch.geni.net:gpo-infra+slice+tuptyexclusive")
         slice1.append("8c6b97fa-493b-400f-95ee-19accfaf4ae8")
         slice1.append(str(int(time.time()*1000000)))
         slice1.append("urn:publicid:IDN+ch.geni.net+authority+ch") # authority urn
         slice1.append(url_opsconfig_local_info + "authority/ch.geni.net") # authority href
         slice1.append("1391626683000000")
         slice1.append("1391708989000000")

         info_insert(self.tbl_mgr, "ops_slice", slice1)


         user1 = []
         user1.append("http://www.gpolab.bbn.com/monitoring/schema/20140131/user#")
         user1.append("tupty")
         user1.append(url_local_info + "user/" + user1[1])
         user1.append("tupty_user_urn") 
         user1.append(str(int(time.time()*1000000)))
         user1.append("urn:publicid:IDN+ch.geni.net+authority+ch") # authority urn
         user1.append(url_opsconfig_local_info + "authority/ch.geni.net") # authority href
         user1.append("Tim Exampleuser")
         user1.append("tupty@example.com")

         info_insert(self.tbl_mgr, "ops_user", user1)


         authority1 = []
         authority1.append("http://www.gpolab.bbn.com/monitoring/schema/20140131/authority#")
         authority1.append("ch.geni.net")
         authority1.append(url_local_info + "authority/" + authority1[1])
         authority1.append("urn:publicid:IDN+ch.geni.net+authority+ch")
         authority1.append(str(int(time.time()*1000000))) 

         info_insert(self.tbl_mgr, "ops_authority", authority1)


         opsconfig1 = []
         opsconfig1.append("http://www.gpolab.bbn.com/monitoring/schema/20140131/opsconfig#")
         opsconfig1.append("geni-prod")
         opsconfig1.append(url_local_info + "opsconfig/" + opsconfig1[1])
         opsconfig1.append(str(int(time.time()*1000000))) 

         info_insert(self.tbl_mgr, "ops_opsconfig", opsconfig1)


         aggres1 = []
         aggres1.append("instageni.gpolab.bbn.com_node_pc1")
         aggres1.append("gpo-ig")
         aggres1.append("urn:publicid:IDN+instageni.gpolab.bbn.com+node+pc1")
         aggres1.append(url_local_info + "node/" + aggres1[0])
         
         info_insert(self.tbl_mgr, "ops_aggregate_resource", aggres1)

         aggres2 = []
         aggres2.append("instageni.gpolab.bbn.com_node_pc2")
         aggres2.append("gpo-ig")
         aggres2.append("urn:publicid:IDN+instageni.gpolab.bbn.com+node+pc2")
         aggres2.append(url_local_info + "node/" + aggres2[0])
         
         info_insert(self.tbl_mgr, "ops_aggregate_resource", aggres2)


         aggres3 = []
         aggres3.append("arbitrary_link_id_001")
         aggres3.append("gpo-ig")
         aggres3.append("urn:publicid:IDN+instageni.gpolab.bbn.com+link_id_001")
         aggres3.append(url_local_info + "link/" + aggres3[0])

         info_insert(self.tbl_mgr, "ops_aggregate_resource", aggres3)

         
         aggsliv1 = []
         aggsliv1.append("instageni.gpolab.bbn.com_sliver_26947")
         aggsliv1.append("gpo-ig")
         aggsliv1.append("urn:publicid:IDN+instageni.gpolab.bbn.com+authority+cm")
         aggsliv1.append(url_local_info + "sliver/" + aggsliv1[0])
         
         info_insert(self.tbl_mgr, "ops_aggregate_sliver", aggsliv1)
         

         aggsliv2 = []
         aggsliv2.append("instageni.gpolab.bbn.com_sliver_26950")
         aggsliv2.append("gpo-ig")
         aggsliv2.append("urn:publicid:IDN+instageni.gpolab.bbn.com+authority+cm")
         aggsliv2.append(url_local_info + "sliver/" + aggsliv2[0])
         
         info_insert(self.tbl_mgr, "ops_aggregate_sliver", aggsliv2)

         
         nodeiface1 = []
         nodeiface1.append("instageni.gpolab.bbn.com_interface_pc1:eth1")
         nodeiface1.append("instageni.gpolab.bbn.com_node_pc1")
         nodeiface1.append("urn:publicid:IDN+instageni.gpolab.bbn.com+interface+pc1:eth1")
         nodeiface1.append(url_local_info + "interface/" + nodeiface1[0])
         
         info_insert(self.tbl_mgr, "ops_node_interface", nodeiface1)


         nodeiface2 = []
         nodeiface2.append("instageni.gpolab.bbn.com_interface_pc2:eth1")
         nodeiface2.append("instageni.gpolab.bbn.com_node_pc2")
         nodeiface2.append("urn:publicid:IDN+instageni.gpolab.bbn.com+interface+pc2:eth1")
         nodeiface2.append(url_local_info + "interface/" + nodeiface2[0])

         info_insert(self.tbl_mgr, "ops_node_interface", nodeiface2)


         linkifacevlan1 = []
         linkifacevlan1.append("instageni.gpolab.bbn.com_interface_pc1:eth1:1750")
         linkifacevlan1.append("arbitrary_link_id_001")
         linkifacevlan1.append("urn:publicid:IDN+instageni.gpolab.bbn.com+interface+pc1:eth1")
         linkifacevlan1.append(url_local_info + "interfacevlan/" + linkifacevlan1[0])
         
         info_insert(self.tbl_mgr, "ops_link_interfacevlan", linkifacevlan1)


         linkifacevlan2 = []
         linkifacevlan2.append("instageni.gpolab.bbn.com_interface_pc2:eth1:1750")
         linkifacevlan2.append("arbitrary_link_id_001")
         linkifacevlan2.append("urn:publicid:IDN+instageni.gpolab.bbn.com+interface+pc2:eth1")
         linkifacevlan2.append(url_local_info + "interfacevlan/" + linkifacevlan2[0])
         
         info_insert(self.tbl_mgr, "ops_link_interfacevlan", linkifacevlan2)


         slivernode1 = []
         slivernode1.append("instageni.gpolab.bbn.com_node_pc1")
         slivernode1.append("instageni.gpolab.bbn.com_sliver_26947")
         slivernode1.append("urn:publicid:IDN+instageni.gpolab.bbn.com+node+pc1")
         slivernode1.append(url_local_info + "node/" + slivernode1[0])
         
         info_insert(self.tbl_mgr, "ops_sliver_resource", slivernode1)


         slivernode2 = []
         slivernode2.append("instageni.gpolab.bbn.com_node_pc2")
         slivernode2.append("instageni.gpolab.bbn.com_sliver_26950")
         slivernode2.append("urn:publicid:IDN+instageni.gpolab.bbn.com+node+pc2")
         slivernode2.append(url_local_info + "node/" + slivernode2[0])
         
         info_insert(self.tbl_mgr, "ops_sliver_resource", slivernode2)


         sliverlink1 = []
         sliverlink1.append("arbitrary_link_id_001")
         sliverlink1.append("instageni.gpolab.bbn.com_sliver_26947")
         sliverlink1.append("urn:publicid:IDN+instageni.gpolab.bbn.com+link_id_001")
         sliverlink1.append(url_local_info + "link/" + sliverlink1[0])
         
         info_insert(self.tbl_mgr, "ops_sliver_resource", sliverlink1)

         sliceuser1 = []
         sliceuser1.append("tupty")
         sliceuser1.append("ch.geni.net_gpo-infra_slice_tuptyexclusive")
         sliceuser1.append("urn:publicid:IDN+instageni.gpolab.bbn.com+node+pc1")
         sliceuser1.append("lead")
         sliceuser1.append(url_opsconfig_local_info + "user/" + sliceuser1[0])

         info_insert(self.tbl_mgr, "ops_slice_user", sliceuser1)


         authuser1 = []
         authuser1.append("tupty")
         authuser1.append("ch.geni.net")
         authuser1.append("urn:publicid:IDN+ch.geni.net+user+tupty")
         authuser1.append(url_local_info + "user/" + authuser1[0])

         info_insert(self.tbl_mgr, "ops_authority_user", authuser1)


         authslice1 = []
         authslice1.append("ch.geni.net_gpo-infra_slice_tuptyexclusive")
         authslice1.append("ch.geni.net")
         authslice1.append("urn:publicid:IDN+ch.geni.net:gpo-infra+slice+tuptyexclusive")
         authslice1.append(url_local_info + "slice/" + authslice1[0])

         info_insert(self.tbl_mgr, "ops_authority_slice", authslice1)


         opsconfigagg1 = []
         opsconfigagg1.append("gpo-ig")
         opsconfigagg1.append("geni-prod")
         opsconfigagg1.append("protogeni")
         opsconfigagg1.append("urn:publicid:IDN+instageni.gpolab.bbn.com+authority+cm")
         opsconfigagg1.append(url_local_info + "aggregate/" + opsconfigagg1[0])
         
         info_insert(self.tbl_mgr, "ops_opsconfig_aggregate", opsconfigagg1)

         opsconfigagg2 = []
         opsconfigagg2.append("ion.internet2.edu")
         opsconfigagg2.append("geni-prod")
         opsconfigagg2.append("ion")
         opsconfigagg2.append("urn:publicid:IDN+ion.internet2.edu+authority+cm")
         opsconfigagg2.append("http://aj-dev6.grnoc.iu.edu/geni-local-datastore/info/aggregate/" + opsconfigagg2[0])
         
         info_insert(self.tbl_mgr, "ops_opsconfig_aggregate", opsconfigagg2)

         opsconfigagg3 = []
         opsconfigagg3.append("dragon.maxgigapop.net")
         opsconfigagg3.append("geni-prod")
         opsconfigagg3.append("ion")
         opsconfigagg3.append("urn:publicid:IDN+al2s.net.internet2.edu+authority+cm")
         opsconfigagg3.append("http://maxam.maxgigapop.net:5000/info/aggregate/" + opsconfigagg3[0])
         
         info_insert(self.tbl_mgr, "ops_opsconfig_aggregate", opsconfigagg3)

         opsconfigagg4 = []
         opsconfigagg4.append("al2s.net.internet2.edu")
         opsconfigagg4.append("geni-prod")
         opsconfigagg4.append("al2s")
         opsconfigagg4.append("urn:publicid:IDN+al2s.net.internet2.edu+authority+cm")
         opsconfigagg4.append("http://aj-dev6.grnoc.iu.edu/geni-local-datastore/info/aggregate/" + opsconfigagg4[0])
         
         info_insert(self.tbl_mgr, "ops_opsconfig_aggregate", opsconfigagg4)

         opsconfigauth1 = []
         opsconfigauth1.append("ch.geni.net")
         opsconfigauth1.append("geni-prod")
         opsconfigauth1.append("urn:publicid:IDN+ch.geni.net+authority+ch")
         opsconfigauth1.append(url_opsconfig_local_info + "authority/" + opsconfigauth1[0])
         info_insert(self.tbl_mgr, "ops_opsconfig_authority", opsconfigauth1)


def info_insert(tbl_mgr, table_str, row_arr):
    val_str = "('"

    for val in row_arr:
        val_str += val + "','" # join won't do this

    val_str = val_str[:-2] + ")" # remove last 2 of 3 chars: ',' and add )

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
