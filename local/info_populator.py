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
import sys

common_path = "../common/"

sys.path.append(common_path)
import table_manager

class InfoPopulator():
    def __init__(self, tbl_mgr, url_base):

        self.tbl_mgr = tbl_mgr
        self.url_base = url_base
        # steal config path from table_manager
        self.config_path = tbl_mgr.config_path

    def insert_fake_info(self):
        ok = True

        url_local_info = self.url_base + "/info/"
        url_local_data = self.url_base + "/data/"
        url_opsconfig_local_info = self.url_base + "/info/"

        agg1 = []
        agg1.append("http://www.gpolab.bbn.com/monitoring/schema/20140828/aggregate#")
        agg1.append("gpo-ig")
        agg1.append(url_local_info + "aggregate/" + agg1[1])
        agg1.append("urn:publicid:IDN+instageni.gpolab.bbn.com+authority+cm")
        agg1.append(str(int(time.time()*1000000)))
        agg1.append(url_local_data) # measRef
        agg1.append("1.0") # populator_version
        agg1.append("development") # operational_status
        agg1.append("0") # routable_ip_poolsize

        if not info_insert(self.tbl_mgr, "ops_aggregate", agg1):
            ok = False


        node1 = []
        node1.append("http://www.gpolab.bbn.com/monitoring/schema/20140501/node#")
        node1.append("instageni.gpolab.bbn.com_node_pc1")
        node1.append(url_local_info + "node/" + node1[1])
        node1.append("urn:publicid:IDN+instageni.gpolab.bbn.com+node+pc1")
        node1.append(str(int(time.time()*1000000)))
        node1.append(str(2*1000000)) # mem_total_kb
        node1.append("xen") # vm_server_type

        if not info_insert(self.tbl_mgr, "ops_node", node1):
            ok = False


        node2 = []
        node2.append("http://www.gpolab.bbn.com/monitoring/schema/20140501/node#")
        node2.append("instageni.gpolab.bbn.com_node_pc2")
        node2.append(url_local_info + "node/" + node2[1])
        node2.append("urn:publicid:IDN+instageni.gpolab.bbn.com+node+pc2")
        node2.append(str(int(time.time()*1000000)))
        node2.append(str(2*1000000)) # mem_total_kb
        node2.append("xen") # vm_server_type

        if not info_insert(self.tbl_mgr, "ops_node", node2):
            ok = False


        sliver1 = []
        sliver1.append("http://www.gpolab.bbn.com/monitoring/schema/20140828/sliver#")
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
        sliver1.append("instageni.gpolab.bbn.com_node_pc1") # node_id
        sliver1.append("NULL") # link_id

        if not info_insert(self.tbl_mgr, "ops_sliver", sliver1):
            ok = False


        sliver2 = []
        sliver2.append("http://www.gpolab.bbn.com/monitoring/schema/20140828/sliver#")
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
        sliver2.append("instageni.gpolab.bbn.com_node_pc2") # node_id
        sliver2.append("NULL") # link_id

        if not info_insert(self.tbl_mgr, "ops_sliver", sliver2):
            ok = False


        link1 = []
        link1.append("http://www.gpolab.bbn.com/monitoring/schema/20140501/link#")
        link1.append("arbitrary_link_id_001")
        link1.append(url_local_info + "link/" + link1[1])
        link1.append("urn:publicid:IDN+instageni.gpolab.bbn.com+link_id_001")
        link1.append(str(int(time.time()*1000000)))

        if not info_insert(self.tbl_mgr, "ops_link", link1):
            ok = False


        sliver3 = []
        sliver3.append("http://www.gpolab.bbn.com/monitoring/schema/20140828/sliver#")
        sliver3.append("instageni.gpolab.bbn.com_sliver_26999")
        sliver3.append(url_local_info + "sliver/" + sliver3[1])
        sliver3.append("urn:publicid:IDN+instageni.gpolab.bbn.com+sliver+26999")
        sliver3.append("30752b06-8ea8-11e3-8d30-000006000000") #uuid
        sliver3.append(str(int(time.time()*1000000))) #current ts
        sliver3.append("urn:publicid:IDN+instageni.gpolab.bbn.com+authority+cm") # agg_urn
        sliver3.append(url_local_info + "aggregate/gpo-ig") # agg_href
        sliver3.append("urn:publicid:IDN+ch.geni.net:gpo-infra+slice+tuptyexclusive") # slice_urn
        sliver3.append("8c6b97fa-493b-400f-95ee-19accfaf4ae8") #slice uuid
        sliver3.append("urn:publicid:IDN+ch.geni.net+user+tupty") # creator
        sliver3.append(str(int(1391626683000005))) # created
        sliver3.append(str(int(1391708989000006))) # expires
        sliver3.append("NULL") # node_id
        sliver3.append("arbitrary_link_id_001") # link_id

        if not info_insert(self.tbl_mgr, "ops_sliver", sliver3):
            ok = False


        interface1 = []
        interface1.append("http://www.gpolab.bbn.com/monitoring/schema/20140828/interface#")
        interface1.append("instageni.gpolab.bbn.com_interface_pc1:eth1")
        interface1.append(url_local_info + "interface/" + interface1[1])
        interface1.append("urn:publicid:IDN+instageni.gpolab.bbn.com+interface+pc1:eth1")
        interface1.append(str(int(time.time()*1000000)))
        interface1.append("ipv4") # addr type
        interface1.append("192.1.242.140") # addr
        interface1.append("control") # role
        interface1.append(str(10000000)) #max bps
        interface1.append(str(1000000)) #max pps

        if not info_insert(self.tbl_mgr, "ops_interface", interface1):
            ok = False


        interface2 = []
        interface2.append("http://www.gpolab.bbn.com/monitoring/schema/20140828/interface#")
        interface2.append("instageni.gpolab.bbn.com_interface_pc2:eth1")
        interface2.append(url_local_info + "interface/" + interface2[1])
        interface2.append("urn:publicid:IDN+instageni.gpolab.bbn.com+interface+pc2:eth1")
        interface2.append(str(int(time.time()*1000000)))
        interface2.append("ipv4") # addr type
        interface2.append("192.1.242.140") # addr
        interface2.append("control") # role
        interface2.append(str(10000000)) #max bps
        interface2.append(str(1000000)) #max pps

        if not info_insert(self.tbl_mgr, "ops_interface", interface2):
            ok = False


        interfacevlan1 = []
        interfacevlan1.append("http://www.gpolab.bbn.com/monitoring/schema/20140828/interfacevlan#")
        interfacevlan1.append("instageni.gpolab.bbn.com_interface_pc1:eth1:1750")
        interfacevlan1.append(url_local_info + "interfacevlan/" + interfacevlan1[1])
        interfacevlan1.append("urn:publicid:IDN+instageni.gpolab.bbn.com+interface+pc1:eth1:1750")
        interfacevlan1.append(str(int(time.time()*1000000)))
        interfacevlan1.append(str(1750)) # tag type
        interfacevlan1.append("urn:publicid:IDN+instageni.gpolab.bbn.com+interface+pc1:eth1") # interface urn
        interfacevlan1.append(url_local_info + "interface/" + interface1[1]) # interface href

        if not info_insert(self.tbl_mgr, "ops_interfacevlan", interfacevlan1):
            ok = False


        interfacevlan2 = []
        interfacevlan2.append("http://www.gpolab.bbn.com/monitoring/schema/20140828/interfacevlan#")
        interfacevlan2.append("instageni.gpolab.bbn.com_interface_pc2:eth1:1750")
        interfacevlan2.append(url_local_info + "interfacevlan/" + interfacevlan2[1])
        interfacevlan2.append("urn:publicid:IDN+instageni.gpolab.bbn.com+interface+pc2:eth1:1750")
        interfacevlan2.append(str(int(time.time()*1000000)))
        interfacevlan2.append(str(1750)) # tag type
        interfacevlan2.append("urn:publicid:IDN+instageni.gpolab.bbn.com+interface+pc2:eth1") # interface urn
        interfacevlan2.append(url_local_info + "interface/" + interface2[1]) # interface href
        if not info_insert(self.tbl_mgr, "ops_interfacevlan", interfacevlan2):
            ok = False


        authority1 = []
        authority1.append("http://www.gpolab.bbn.com/monitoring/schema/20140501/authority#")
        authority1.append("ch.geni.net")
        authority1.append(url_local_info + "authority/" + authority1[1])
        authority1.append("urn:publicid:IDN+ch.geni.net+authority+ch")
        authority1.append(str(int(time.time() * 1000000)))

        if not info_insert(self.tbl_mgr, "ops_authority", authority1):
            ok = False

        slice1 = []
        slice1.append("http://www.gpolab.bbn.com/monitoring/schema/20140501/slice#")
        slice1.append("ch.geni.net_gpo-infra_slice_tuptyexclusive")
        slice1.append(url_local_info + "slice/" + slice1[1])
        slice1.append("urn:publicid:IDN+ch.geni.net:gpo-infra+slice+tuptyexclusive")
        slice1.append("8c6b97fa-493b-400f-95ee-19accfaf4ae8")
        slice1.append(str(int(time.time()*1000000)))
        slice1.append(authority1[3])  # authority urn
        slice1.append(authority1[2])  # authority href
        slice1.append("1391626683000000")
        slice1.append("1391708989000000")

        if not info_insert(self.tbl_mgr, "ops_slice", slice1):
            ok = False


        user1 = []
        user1.append("http://www.gpolab.bbn.com/monitoring/schema/20140501/user#")
        user1.append("tupty")
        user1.append(url_local_info + "user/" + user1[1])
        user1.append("tupty_user_urn")
        user1.append(str(int(time.time()*1000000)))
        user1.append("urn:publicid:IDN+ch.geni.net+authority+ch") # authority urn
        user1.append(url_opsconfig_local_info + "authority/ch.geni.net") # authority href
        user1.append("Tim Exampleuser")
        user1.append("tupty@example.com")

        if not info_insert(self.tbl_mgr, "ops_user", user1):
            ok = False


        aggres1 = []
        aggres1.append("instageni.gpolab.bbn.com_node_pc1")
        aggres1.append("gpo-ig")
        aggres1.append("urn:publicid:IDN+instageni.gpolab.bbn.com+node+pc1")
        aggres1.append(url_local_info + "node/" + aggres1[0])

        if not info_insert(self.tbl_mgr, "ops_aggregate_resource", aggres1):
            ok = False

        aggres2 = []
        aggres2.append("instageni.gpolab.bbn.com_node_pc2")
        aggres2.append("gpo-ig")
        aggres2.append("urn:publicid:IDN+instageni.gpolab.bbn.com+node+pc2")
        aggres2.append(url_local_info + "node/" + aggres2[0])

        if not info_insert(self.tbl_mgr, "ops_aggregate_resource", aggres2):
            ok = False


        aggres3 = []
        aggres3.append("arbitrary_link_id_001")
        aggres3.append("gpo-ig")
        aggres3.append("urn:publicid:IDN+instageni.gpolab.bbn.com+link_id_001")
        aggres3.append(url_local_info + "link/" + aggres3[0])

        if not info_insert(self.tbl_mgr, "ops_aggregate_resource", aggres3):
            ok = False


        aggsliv1 = []
        aggsliv1.append(sliver1[1])  # id
        aggsliv1.append("gpo-ig")
        aggsliv1.append(sliver1[3])  # urn
        aggsliv1.append(sliver1[2])  # href

        if not info_insert(self.tbl_mgr, "ops_aggregate_sliver", aggsliv1):
            ok = False


        aggsliv2 = []
        aggsliv2.append(sliver2[1])  # id
        aggsliv2.append("gpo-ig")
        aggsliv2.append(sliver2[3])  # urn
        aggsliv2.append(sliver2[2])  # href

        if not info_insert(self.tbl_mgr, "ops_aggregate_sliver", aggsliv2):
            ok = False


        aggsliv3 = []
        aggsliv3.append(sliver3[1])  # id
        aggsliv3.append("gpo-ig")
        aggsliv3.append(sliver3[3])  # urn
        aggsliv3.append(sliver3[2])  # href

        if not info_insert(self.tbl_mgr, "ops_aggregate_sliver", aggsliv3):
            ok = False


        nodeiface1 = []
        nodeiface1.append("instageni.gpolab.bbn.com_interface_pc1:eth1")
        nodeiface1.append("instageni.gpolab.bbn.com_node_pc1")
        nodeiface1.append("urn:publicid:IDN+instageni.gpolab.bbn.com+interface+pc1:eth1")
        nodeiface1.append(url_local_info + "interface/" + nodeiface1[0])

        if not info_insert(self.tbl_mgr, "ops_node_interface", nodeiface1):
            ok = False


        nodeiface2 = []
        nodeiface2.append("instageni.gpolab.bbn.com_interface_pc2:eth1")
        nodeiface2.append("instageni.gpolab.bbn.com_node_pc2")
        nodeiface2.append("urn:publicid:IDN+instageni.gpolab.bbn.com+interface+pc2:eth1")
        nodeiface2.append(url_local_info + "interface/" + nodeiface2[0])

        if not info_insert(self.tbl_mgr, "ops_node_interface", nodeiface2):
            ok = False


        linkifacevlan1 = []
        linkifacevlan1.append("instageni.gpolab.bbn.com_interface_pc1:eth1:1750")
        linkifacevlan1.append("arbitrary_link_id_001")
        linkifacevlan1.append("urn:publicid:IDN+instageni.gpolab.bbn.com+interface+pc1:eth1")
        linkifacevlan1.append(url_local_info + "interfacevlan/" + linkifacevlan1[0])

        if not info_insert(self.tbl_mgr, "ops_link_interfacevlan", linkifacevlan1):
            ok = False


        linkifacevlan2 = []
        linkifacevlan2.append("instageni.gpolab.bbn.com_interface_pc2:eth1:1750")
        linkifacevlan2.append("arbitrary_link_id_001")
        linkifacevlan2.append("urn:publicid:IDN+instageni.gpolab.bbn.com+interface+pc2:eth1")
        linkifacevlan2.append(url_local_info + "interfacevlan/" + linkifacevlan2[0])

        if not info_insert(self.tbl_mgr, "ops_link_interfacevlan", linkifacevlan2):
            ok = False


        sliceuser1 = []
        sliceuser1.append("tupty")
        sliceuser1.append("ch.geni.net_gpo-infra_slice_tuptyexclusive")
        sliceuser1.append("urn:publicid:IDN+instageni.gpolab.bbn.com+node+pc1")
        sliceuser1.append("lead")
        sliceuser1.append(url_opsconfig_local_info + "user/" + sliceuser1[0])

        if not info_insert(self.tbl_mgr, "ops_slice_user", sliceuser1):
            ok = False


        authuser1 = []
        authuser1.append("tupty")
        authuser1.append("ch.geni.net")
        authuser1.append("urn:publicid:IDN+ch.geni.net+user+tupty")
        authuser1.append(url_local_info + "user/" + authuser1[0])

        if not info_insert(self.tbl_mgr, "ops_authority_user", authuser1):
            ok = False


        authslice1 = []
        authslice1.append("ch.geni.net_gpo-infra_slice_tuptyexclusive")
        authslice1.append("ch.geni.net")
        authslice1.append("urn:publicid:IDN+ch.geni.net:gpo-infra+slice+tuptyexclusive")
        authslice1.append(url_local_info + "slice/" + authslice1[0])

        if not info_insert(self.tbl_mgr, "ops_authority_slice", authslice1):
            ok = False

        return ok

    # Dummy information to test the external check store
    def insert_externalcheck_store(self):
        return self.insert_externalcheck_store_info()

    def insert_externalcheck_store_info(self):
        ok = True
        extck_id = "gpo"
        ts = str(int(time.time() * 1000000))
        extck = ["http://www.gpolab.bbn.com/monitoring/schema/20140501/externalcheck#", extck_id, self.url_base + "/info/externalcheck/" + extck_id, ts, self.url_base + "/data/"]
        if not info_insert(self.tbl_mgr, "ops_externalcheck", extck):
            ok = False

        exp1_id = "missouri_ig_to_gpo_ig"
        extck_exp1 = [exp1_id, extck_id, self.url_base + "/info/experiment/" + exp1_id]
        if not info_insert(self.tbl_mgr, "ops_externalcheck_experiment", extck_exp1):
            ok = False

        exp1_id = "missouri_ig_to_gpo_ig"
        exp1 = ["http://www.gpolab.bbn.com/monitoring/schema/20140501/externalcheck#", exp1_id, self.url_base + "/info/experiment/" + exp1_id, ts, "urn:slice_urn", "uuid:slice_uuid", "urn:source_aggregate_urn", "source aggregate local datastore href", "urn:destination_aggregate_urn", "destination aggregate local datastore href"]
        if not info_insert(self.tbl_mgr, "ops_experiment", exp1):
            ok = False

        mon_agg = ["gpo_ig", "gpo", self.url_base + "/info/aggregate/gpo-ig"]
        if not info_insert(self.tbl_mgr, "ops_externalcheck_monitoredaggregate", mon_agg):
            ok = False

        return ok


def info_insert(tbl_mgr, table_str, row_arr):
    """
    Function to insert values into a table.
    :param tbl_mgr: the instance of TableManager to use.
    :param table_str: the name of the table to insert into.
    :param row_arr: a list of values.
    :return: True if the insertion happened correctly, false otherwise.
    """
    val_str = "('"

    for val in row_arr:
        val_str += val + "','"  # join won't do this

    val_str = val_str[:-2] + ")"  # remove last 2 of 3 chars: ',' and add )

    return tbl_mgr.insert_stmt(table_str, val_str)


def main():

    db_name = "local"
    config_path = "../config"

    tbl_mgr = table_manager.TableManager(db_name, config_path)
    tbl_mgr.poll_config_store()

    tbl_mgr.drop_all_tables()
    tbl_mgr.establish_all_tables()
    ip = InfoPopulator(tbl_mgr)

    if not ip.insert_fake_info():
        sys.stderr.write("Error executing info populator\n")
        sys.exit(-1)


    q_res = tbl_mgr.query("select count(*) from ops_aggregate");
    if q_res is not None:
        print "num entries", q_res[0][0]


if __name__ == "__main__":
    main()
