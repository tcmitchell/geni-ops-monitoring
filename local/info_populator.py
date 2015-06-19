#!/usr/bin/env python
#----------------------------------------------------------------------
# Copyright (c) 2014-2015 Raytheon BBN Technologies
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


# Using these classes for constants because we can't reference a constant to declare another constant in the same class :(
# i.e. LINK_RELATION = ( (InfoPopulator.LINK_IDS[0], InfoPopulator.LINK_IDS[1]) ) fails with NameError: name 'InfoPopulator' is not defined
# because the class has not been fully parsed to be used.

class _HackLink():
    LINK_IDS = ("arbitrary_link_id_001",
                "arbitrary_link_id_002",
                "arbitrary_link_id_003",
                "link_id_egress01"
                )

class _HackVlan():
    VLAN_ID = 1750

class _HackIf():
    IF_IDS = ("instageni.gpolab.bbn.com_interface_pc1:eth1",
              "instageni.gpolab.bbn.com_interface_pc2:eth1",
              "instageni.gpolab.bbn.com_interface_pc1:eth1:0",
              "instageni.gpolab.bbn.com_interface_pc1:eth1:1",
              "instageni.gpolab.bbn.com_interface_pc2:eth1:0",
              "instageni.gpolab.bbn.com_interface_interconnect:port0",
              "instageni.gpolab.bbn.com_interface_newy.ion.internet2.edu:ae0"
              )

    IF_URNS = ("urn:publicid:IDN+instageni.gpolab.bbn.com+interface+pc1:eth1",
               "urn:publicid:IDN+instageni.gpolab.bbn.com+interface+pc2:eth1",
               "urn:publicid:IDN+instageni.gpolab.bbn.com+interface+pc1:eth1:0",
               "urn:publicid:IDN+instageni.gpolab.bbn.com+interface+pc1:eth1:1",
               "urn:publicid:IDN+instageni.gpolab.bbn.com+interface+pc2:eth1:0",
               "urn:publicid:IDN+instageni.gpolab.bbn.com+interface+interconnect:port0",
               "urn:publicid:IDN+ion.internet2.edu+interface+rtr.newy:ae0"
               )

class _HackIfvlan():
    IFVLAN_IDS = (_HackIf.IF_IDS[0] + ":" + str(_HackVlan.VLAN_ID),
                   _HackIf.IF_IDS[1] + ":" + str(_HackVlan.VLAN_ID),
                   _HackIf.IF_IDS[5] + ":" + str(_HackVlan.VLAN_ID),
                   _HackIf.IF_IDS[6] + ":" + str(_HackVlan.VLAN_ID),
                   )


class InfoPopulator():

    __SCHEMA_BASE = 'http://www.gpolab.bbn.com/monitoring/schema/20150625/'


    AGGREGATE_ID = "gpo-ig"
    AGGREGATE_URN = "urn:publicid:IDN+instageni.gpolab.bbn.com+authority+cm"
    NODE_IDS = ("instageni.gpolab.bbn.com_node_pc1",
                "instageni.gpolab.bbn.com_node_pc2",
                "instageni.gpolab.bbn.com_node_pc1_vm1",
                "instageni.gpolab.bbn.com_node_pc2_vm2",
                "instageni.gpolab.bbn.com_node_pc1_vm3",
                "instageni.gpolab.bbn.com_node_interconnect"
                )

    NODE_URNS = ("urn:publicid:IDN+instageni.gpolab.bbn.com+node+pc1",
                 "urn:publicid:IDN+instageni.gpolab.bbn.com+node+pc2",
                 "urn:publicid:IDN+instageni.gpolab.bbn.com+node+pc1+vm1",
                 "urn:publicid:IDN+instageni.gpolab.bbn.com+node+pc2+vm2",
                 "urn:publicid:IDN+instageni.gpolab.bbn.com+node+pc1+vm3",
                 "urn:publicid:IDN+instageni.gpolab.bbn.com+node+interconnect"
                 )

    # list of Tuples = ( Node idx, Parent Node idx)
    NODE_PARENT_NODE_RELATIONS = ((2, 0),
                                  (3, 1),
                                  (4, 0)
                                 )
    LINK_IDS = _HackLink.LINK_IDS

    LINK_URNS = ("urn:publicid:IDN+instageni.gpolab.bbn.com+link_id_001",
                 "urn:publicid:IDN+instageni.gpolab.bbn.com+link_id_002",
                 "urn:publicid:IDN+instageni.gpolab.bbn.com+link_id_003",
                 "urn:publicid:IDN+instageni.gpolab.bbn.com+link_id_egress01"
                 )

    IF_IDS = _HackIf.IF_IDS

    IF_URNS = _HackIf.IF_URNS

    # list of Tuples = ( If idx, Parent If idx)
    IF_PARENT_IF_RELATIONS = ((2, 0),
                              (3, 0),
                              (4, 1),
                              )

    # tuples of addrtype, scope, address
    IF_ADDRESSES = (("IPv4", "public", "public"),
                     ("802.3", None, "ab:cd:ef:01:23")
                    )

    # tuple of IF IDs, address record idx
    IF_ADDRESS_RELATIONS = ((_HackIf.IF_IDS[0], 0),
                             (_HackIf.IF_IDS[0], 1)
                            )
    # list of Tuples = ( Node idx, IF idx)
    NODE_IF_RELATIONS = ((0, 0),
                         (1, 1),
                         (2, 2),
                         (3, 4),
                         (4, 3),
                         (5, 5)
                        )

    VLAN_ID = _HackVlan.VLAN_ID

    IFVLAN_IDS = _HackIfvlan.IFVLAN_IDS


    IFVLAN_URNS = (_HackIf.IF_URNS[0] + ":" + str(_HackVlan.VLAN_ID),
                   _HackIf.IF_URNS[1] + ":" + str(_HackVlan.VLAN_ID),
                   _HackIf.IF_URNS[2] + ":" + str(_HackVlan.VLAN_ID),
                   _HackIf.IF_URNS[3] + ":" + str(_HackVlan.VLAN_ID),
                   )

    # # Idx of interface IDS for each vlan
    IFVLAN_IF_IDS = (0, 1, 5, 6)

    LINK_VLAN_RELATIONS = ((_HackIfvlan.IFVLAN_IDS[0], _HackLink.LINK_IDS[0]),
                           (_HackIfvlan.IFVLAN_IDS[1], _HackLink.LINK_IDS[0]),
                           (_HackIfvlan.IFVLAN_IDS[0], _HackLink.LINK_IDS[1]),
                           (_HackIfvlan.IFVLAN_IDS[2], _HackLink.LINK_IDS[1]),
                           (_HackIfvlan.IFVLAN_IDS[2], _HackLink.LINK_IDS[2]),
                           (_HackIfvlan.IFVLAN_IDS[1], _HackLink.LINK_IDS[2]),
                           (_HackIfvlan.IFVLAN_IDS[2], _HackLink.LINK_IDS[3]),
                           (_HackIfvlan.IFVLAN_IDS[3], _HackLink.LINK_IDS[3])
                           )

    # first parent, second child
    LINK_PARENT_CHILD_RELATION = ((_HackLink.LINK_IDS[0], _HackLink.LINK_IDS[1]),
                                  (_HackLink.LINK_IDS[0], _HackLink.LINK_IDS[2])
                                  )

    SLIVER_IDS = ("instageni.gpolab.bbn.com_sliver_26947",
                  "instageni.gpolab.bbn.com_sliver_26950",
                  "instageni.gpolab.bbn.com_sliver_26951",
                  "instageni.gpolab.bbn.com_sliver_26999"
                  )
    SLIVER_URNS = ("urn:publicid:IDN+instageni.gpolab.bbn.com+sliver+26947",
                   "urn:publicid:IDN+instageni.gpolab.bbn.com+sliver+26950",
                   "urn:publicid:IDN+instageni.gpolab.bbn.com+sliver+26951",
                   "urn:publicid:IDN+instageni.gpolab.bbn.com+sliver+26999"
                   )

    SLIVER_UUIDS = ("30752b06-8ea8-11e3-8d30-000000000000",
                    "30752b06-8ea8-11e3-8d30-000005000000",
                    "30752b06-8ea8-11e3-8d30-000005000001",
                    "30752b06-8ea8-11e3-8d30-000006000000"
                    )

    SLICE_URNS = ("urn:publicid:IDN+ch.geni.net:gpo-infra+slice+tuptyexclusive",
                  "urn:publicid:IDN+ch.geni.net:gpo-infra+slice+tuptyexclusive2"
                  )
    SLICE_UUIDS = ("8c6b97fa-493b-400f-95ee-19accfaf4ae8",
                   "8c6b97fa-493b-400f-95ee-19accfaf4ae9"
                  )
    # at sliver idx you have slice idx
    SLIVER_SCLICE_IDX = (0, 1, 1, 0)

    USER_URNS = ("urn:publicid:IDN+ch.geni.net+user+tupty",
                 "urn:publicid:IDN+ch.geni.net+user+sblais"
                 )

    # at sliver idx you have user idx
    SLIVER_USER_IDX = (0, 1, 0, 1)

    # at sliver idx, you get pairs of (resource type, and idx in the corresponding resource array).
    SLIVER_RESOURCE_RELATION = ((("node", 2),),
                                (("node", 3),),
                                (("node", 4),),
                                (("link", 0), ("link", 1)),
                                )

    def __init__(self, tbl_mgr, url_base):

        self.tbl_mgr = tbl_mgr
        self.url_base = url_base
        # steal config path from table_manager
        self.config_path = tbl_mgr.config_path


    def insert_sliver_resources_relations(self, sliver_id, sliver_idx):
        ok = True
        for resource_relation in InfoPopulator.SLIVER_RESOURCE_RELATION[sliver_idx]:
            if resource_relation[0] == "node":
                table_relation = "ops_sliver_node"
                obj_id = InfoPopulator.NODE_IDS[resource_relation[1]]  # node_id
            elif resource_relation[0] == "link":
                table_relation = "ops_sliver_link"
                obj_id = InfoPopulator.LINK_IDS[resource_relation[1]]  # link_id
            else:
                raise Exception("unidentified resource type %s" % resource_relation[0])
            record = (obj_id, sliver_id)
            if not info_insert(self.tbl_mgr, table_relation, record):
                ok = False
        return ok

    @staticmethod
    def get_ifvlan_if_idx(ifvlan_idx):
        return InfoPopulator.IFVLAN_IF_IDS[ifvlan_idx]

    @staticmethod
    def get_parent_node_idx(node_idx):
        for node_idces in InfoPopulator.NODE_PARENT_NODE_RELATIONS:
            if node_idx == node_idces[0]:
                return node_idces[1]
        return None

    @staticmethod
    def get_parent_node_id(node_idx):
        parent_idx = InfoPopulator.get_parent_node_idx(node_idx)
        if parent_idx is not None:
            return InfoPopulator.NODE_IDS[parent_idx]
        else:
            return None

    @staticmethod
    def get_parent_if_idx(if_idx):
        for if_idces in InfoPopulator.IF_PARENT_IF_RELATIONS:
            if if_idx == if_idces[0]:
                return if_idces[1]
        return None

    @staticmethod
    def get_parent_if_id(if_idx):
        parent_idx = InfoPopulator.get_parent_if_idx(if_idx)
        if parent_idx is not None:
            return InfoPopulator.IF_IDS[parent_idx]
        else:
            return None

    @staticmethod
    def get_parent_link_id(link_id):
        for i in range(len(InfoPopulator.LINK_PARENT_CHILD_RELATION)):
            if link_id == InfoPopulator.LINK_PARENT_CHILD_RELATION[i][1]:  # child id
                return InfoPopulator.LINK_PARENT_CHILD_RELATION[i][0]  # parent id
        return None

    @staticmethod
    def get_node_idx_for_if_idx(if_idx):

        for tup in InfoPopulator.NODE_IF_RELATIONS:
            node_idx = tup[0]
            if if_idx == tup[1]:
                return node_idx
        return None
    
    @staticmethod
    def get_node_id_for_if_idx(if_idx):
        node_idx = InfoPopulator.get_node_idx_for_if_idx(if_idx)
        if node_idx is not None:
            return InfoPopulator.NODE_IDS[node_idx]
        return None
    
    @staticmethod
    def __get_schema_url_for(objecttype):
        return InfoPopulator.__SCHEMA_BASE + objecttype + '#'

    def __get_selfRef_url_for(self, objecttype, objectid):
        return self.url_base + "/info/" + objecttype + '/' + objectid

    def __fill_in_list_with_schema_id_and_url(self, array, objecttype, objectid):
        array.append(InfoPopulator.__get_schema_url_for(objecttype))
        array.append(objectid)
        array.append(self.__get_selfRef_url_for(objecttype, objectid))

    def insert_fake_info(self):
        ok = True

        url_local_data = self.url_base + "/data/"

        agg1 = []
        self.__fill_in_list_with_schema_id_and_url(agg1, "aggregate", InfoPopulator.AGGREGATE_ID)
        agg1.append(InfoPopulator.AGGREGATE_URN)
        agg1.append(str(int(time.time() * 1000000)))
        agg1.append(url_local_data)  # measRef
        agg1.append("1.0")  # populator_version
        agg1.append("development")  # operational_status
        agg1.append("0")  # routable_ip_poolsize

        if not info_insert(self.tbl_mgr, "ops_aggregate", agg1):
            ok = False


        node1 = []
        self.__fill_in_list_with_schema_id_and_url(node1, "node", InfoPopulator.NODE_IDS[0])
        node1.append(InfoPopulator.NODE_URNS[0])
        node1.append(str(int(time.time() * 1000000)))
        node1.append("server")  # node_type
        node1.append(str(2 * 1000000))  # mem_total_kb
        node1.append("xen")  # virtualization_type
        node1.append(InfoPopulator.get_parent_node_id(0))  # Parent id
        node1.append(InfoPopulator.AGGREGATE_ID)  # Aggregate id

        if not info_insert(self.tbl_mgr, "ops_node", node1):
            ok = False


        node2 = []
        self.__fill_in_list_with_schema_id_and_url(node2, "node", InfoPopulator.NODE_IDS[1])
        node2.append(InfoPopulator.NODE_URNS[1])
        node2.append(str(int(time.time() * 1000000)))
        node2.append("server")  # node_type
        node2.append(str(2 * 1000000))  # mem_total_kb
        node2.append("xen")  # virtualization_type
        node2.append(InfoPopulator.get_parent_node_id(1))  # Parent id
        node2.append(InfoPopulator.AGGREGATE_ID)  # Aggregate id

        if not info_insert(self.tbl_mgr, "ops_node", node2):
            ok = False

        node3 = []
        self.__fill_in_list_with_schema_id_and_url(node3, "node", InfoPopulator.NODE_IDS[2])
        node3.append(InfoPopulator.NODE_URNS[2])
        node3.append(str(int(time.time() * 1000000)))
        node3.append("vm")  # node_type
        node3.append(str(2 * 1000000))  # mem_total_kb
        node3.append("xen")  # virtualization_type
        node3.append(InfoPopulator.get_parent_node_id(2))  # Parent id
        node3.append(InfoPopulator.AGGREGATE_ID)  # Aggregate id

        if not info_insert(self.tbl_mgr, "ops_node", node3):
            ok = False

        node4 = []
        self.__fill_in_list_with_schema_id_and_url(node4, "node", InfoPopulator.NODE_IDS[3])
        node4.append(InfoPopulator.NODE_URNS[3])
        node4.append(str(int(time.time() * 1000000)))
        node4.append("vm")  # node_type
        node4.append(str(2 * 1000000))  # mem_total_kb
        node4.append("xen")  # virtualization_type
        node4.append(InfoPopulator.get_parent_node_id(3))  # Parent id
        node4.append(InfoPopulator.AGGREGATE_ID)  # Aggregate id

        if not info_insert(self.tbl_mgr, "ops_node", node4):
            ok = False

        node5 = []
        self.__fill_in_list_with_schema_id_and_url(node5, "node", InfoPopulator.NODE_IDS[4])
        node5.append(InfoPopulator.NODE_URNS[4])
        node5.append(str(int(time.time() * 1000000)))
        node5.append("vm")  # node_type
        node5.append(str(2 * 1000000))  # mem_total_kb
        node5.append("xen")  # virtualization_type
        node5.append(InfoPopulator.get_parent_node_id(4))  # Parent id
        node5.append(InfoPopulator.AGGREGATE_ID)  # Aggregate id

        if not info_insert(self.tbl_mgr, "ops_node", node5):
            ok = False

        switch1 = []
        self.__fill_in_list_with_schema_id_and_url(switch1, "node", InfoPopulator.NODE_IDS[5])
        switch1.append(InfoPopulator.NODE_URNS[5])
        switch1.append(str(int(time.time() * 1000000)))
        switch1.append("switch")  # node_type
        switch1.append(str(2 * 1000000))  # mem_total_kb
        switch1.append(None)  # virtualization_type
        switch1.append(InfoPopulator.get_parent_node_id(5))  # Parent id
        switch1.append(InfoPopulator.AGGREGATE_ID)  # Aggregate id
        if not info_insert(self.tbl_mgr, "ops_node", switch1):
            ok = False


        sliver1 = []
        self.__fill_in_list_with_schema_id_and_url(sliver1, "sliver", InfoPopulator.SLIVER_IDS[0])
        sliver1.append(InfoPopulator.SLIVER_URNS[0])
        sliver1.append(InfoPopulator.SLIVER_UUIDS[0])  # uuid
        sliver1.append(str(int(time.time() * 1000000)))  # current ts
        sliver1.append(InfoPopulator.AGGREGATE_ID)  # agg_id
        sliver1.append(InfoPopulator.SLICE_URNS[InfoPopulator.SLIVER_SCLICE_IDX[0]])  # slice_urn
        sliver1.append(InfoPopulator.SLICE_UUIDS[InfoPopulator.SLIVER_SCLICE_IDX[0]])  # slice uuid
        sliver1.append(InfoPopulator.USER_URNS[InfoPopulator.SLIVER_USER_IDX[0]])  # creator
        sliver1.append(str(int(1391626683000000)))  # created
        sliver1.append(str(int(1391708989000000)))  # expires

        if not info_insert(self.tbl_mgr, "ops_sliver", sliver1):
            ok = False

        if not self.insert_sliver_resources_relations(sliver1[1], 0):
            ok = False


        sliver2 = []
        self.__fill_in_list_with_schema_id_and_url(sliver2, "sliver", InfoPopulator.SLIVER_IDS[1])
        sliver2.append(InfoPopulator.SLIVER_URNS[1])
        sliver2.append(InfoPopulator.SLIVER_UUIDS[1])  # uuid
        sliver2.append(str(int(time.time() * 1000000)))  # current ts
        sliver2.append(InfoPopulator.AGGREGATE_ID)  # agg_id
        sliver2.append(InfoPopulator.SLICE_URNS[InfoPopulator.SLIVER_SCLICE_IDX[1]])  # slice_urn
        sliver2.append(InfoPopulator.SLICE_UUIDS[InfoPopulator.SLIVER_SCLICE_IDX[1]])  # slice uuid
        sliver2.append(InfoPopulator.USER_URNS[InfoPopulator.SLIVER_USER_IDX[1]])  # creator
        sliver2.append(str(int(1391626683000000)))  # created
        sliver2.append(str(int(1391708989000000)))  # expires

        if not info_insert(self.tbl_mgr, "ops_sliver", sliver2):
            ok = False

        if not self.insert_sliver_resources_relations(sliver2[1], 1):
            ok = False


        sliver3 = []
        self.__fill_in_list_with_schema_id_and_url(sliver3, "sliver", InfoPopulator.SLIVER_IDS[2])
        sliver3.append(InfoPopulator.SLIVER_URNS[2])
        sliver3.append(InfoPopulator.SLIVER_UUIDS[2])  # uuid
        sliver3.append(str(int(time.time() * 1000000)))  # current ts
        sliver3.append(InfoPopulator.AGGREGATE_ID)  # agg_id
        sliver3.append(InfoPopulator.SLICE_URNS[InfoPopulator.SLIVER_SCLICE_IDX[2]])  # slice_urn
        sliver3.append(InfoPopulator.SLICE_UUIDS[InfoPopulator.SLIVER_SCLICE_IDX[2]])  # slice uuid
        sliver3.append(InfoPopulator.USER_URNS[InfoPopulator.SLIVER_USER_IDX[2]])  # creator
        sliver3.append(str(int(1391626683000000)))  # created
        sliver3.append(str(int(1391708989000000)))  # expires

        if not info_insert(self.tbl_mgr, "ops_sliver", sliver3):
            ok = False

        if not self.insert_sliver_resources_relations(sliver3[1], 2):
            ok = False


        link1 = []
        self.__fill_in_list_with_schema_id_and_url(link1, "link", InfoPopulator.LINK_IDS[0])
        link1.append(InfoPopulator.LINK_URNS[0])
        link1.append("layer2")
        link1.append(str(int(time.time() * 1000000)))
        link1.append(InfoPopulator.AGGREGATE_ID)  # Aggregate id
        link1.append(InfoPopulator.get_parent_link_id(InfoPopulator.LINK_IDS[0]))  # Parent ID
        if not info_insert(self.tbl_mgr, "ops_link", link1):
            ok = False

        sublink1 = []
        self.__fill_in_list_with_schema_id_and_url(sublink1, "link", InfoPopulator.LINK_IDS[1])
        sublink1.append(InfoPopulator.LINK_URNS[1])
        sublink1.append("layer2")
        sublink1.append(str(int(time.time() * 1000000)))
        sublink1.append(InfoPopulator.AGGREGATE_ID)  # Aggregate id
        sublink1.append(InfoPopulator.get_parent_link_id(InfoPopulator.LINK_IDS[1]))  # Parent ID

        if not info_insert(self.tbl_mgr, "ops_link", sublink1):
            ok = False

        sublink2 = []
        self.__fill_in_list_with_schema_id_and_url(sublink2, "link", InfoPopulator.LINK_IDS[2])
        sublink2.append(InfoPopulator.LINK_URNS[2])
        sublink2.append("layer2")
        sublink2.append(str(int(time.time() * 1000000)))
        sublink2.append(InfoPopulator.AGGREGATE_ID)  # Aggregate id
        sublink2.append(InfoPopulator.get_parent_link_id(InfoPopulator.LINK_IDS[2]))  # Parent ID

        if not info_insert(self.tbl_mgr, "ops_link", sublink2):
            ok = False

        egress_link = []
        self.__fill_in_list_with_schema_id_and_url(egress_link, "link", InfoPopulator.LINK_IDS[3])
        egress_link.append(InfoPopulator.LINK_URNS[3])
        egress_link.append("layer2")
        egress_link.append(str(int(time.time() * 1000000)))
        egress_link.append(InfoPopulator.AGGREGATE_ID)  # Aggregate id
        egress_link.append(InfoPopulator.get_parent_link_id(InfoPopulator.LINK_IDS[3]))  # Parent ID

        if not info_insert(self.tbl_mgr, "ops_link", egress_link):
            ok = False

        sliver4 = []
        self.__fill_in_list_with_schema_id_and_url(sliver4, "sliver", InfoPopulator.SLIVER_IDS[3])
        sliver4.append(InfoPopulator.SLIVER_URNS[3])
        sliver4.append(InfoPopulator.SLIVER_UUIDS[3])  # uuid
        sliver4.append(str(int(time.time() * 1000000)))  # current ts
        sliver4.append(InfoPopulator.AGGREGATE_ID)  # agg_id
        sliver4.append(InfoPopulator.SLICE_URNS[InfoPopulator.SLIVER_SCLICE_IDX[3]])  # slice_urn
        sliver4.append(InfoPopulator.SLICE_UUIDS[InfoPopulator.SLIVER_SCLICE_IDX[3]])  # slice uuid
        sliver4.append(InfoPopulator.USER_URNS[InfoPopulator.SLIVER_USER_IDX[3]])  # creator
        sliver4.append(str(int(1391626683000005)))  # created
        sliver4.append(str(int(1391708989000006)))  # expires

        if not info_insert(self.tbl_mgr, "ops_sliver", sliver4):
            ok = False

        if not self.insert_sliver_resources_relations(sliver4[1], 3):
            ok = False

        interface1 = []
        self.__fill_in_list_with_schema_id_and_url(interface1, "interface", InfoPopulator.IF_IDS[0])
        interface1.append(InfoPopulator.IF_URNS[0])
        interface1.append(str(int(time.time() * 1000000)))
        interface1.append("control")  # role
        interface1.append(str(10000000))  # max bps
        interface1.append(str(1000000))  # max pps
        interface1.append(InfoPopulator.get_parent_if_id(0))  # Parent id
        interface1.append(InfoPopulator.get_node_id_for_if_idx(0))  # Node id

        if not info_insert(self.tbl_mgr, "ops_interface", interface1):
            ok = False

        interface2 = []
        self.__fill_in_list_with_schema_id_and_url(interface2, "interface", InfoPopulator.IF_IDS[1])
        interface2.append(InfoPopulator.IF_URNS[1])
        interface2.append(str(int(time.time() * 1000000)))
        interface2.append("control")  # role
        interface2.append(str(10000000))  # max bps
        interface2.append(str(1000000))  # max pps
        interface2.append(InfoPopulator.get_parent_if_id(1))  # Parent id
        interface2.append(InfoPopulator.get_node_id_for_if_idx(1))  # Node id

        if not info_insert(self.tbl_mgr, "ops_interface", interface2):
            ok = False

        interface3 = []
        self.__fill_in_list_with_schema_id_and_url(interface3, "interface", InfoPopulator.IF_IDS[2])
        interface3.append(InfoPopulator.IF_URNS[2])
        interface3.append(str(int(time.time() * 1000000)))
        interface3.append("experimental")  # role
        interface3.append(str(10000000))  # max bps
        interface3.append(str(1000000))  # max pps
        interface3.append(InfoPopulator.get_parent_if_id(2))  # Parent id
        interface3.append(InfoPopulator.get_node_id_for_if_idx(2))  # Node id

        if not info_insert(self.tbl_mgr, "ops_interface", interface3):
            ok = False

        interface4 = []
        self.__fill_in_list_with_schema_id_and_url(interface4, "interface", InfoPopulator.IF_IDS[3])
        interface4.append(InfoPopulator.IF_URNS[3])
        interface4.append(str(int(time.time() * 1000000)))
        interface4.append("experimental")  # role
        interface4.append(str(10000000))  # max bps
        interface4.append(str(1000000))  # max pps
        interface4.append(InfoPopulator.get_parent_if_id(3))  # Parent id
        interface4.append(InfoPopulator.get_node_id_for_if_idx(3))  # Node id

        if not info_insert(self.tbl_mgr, "ops_interface", interface4):
            ok = False

        interface5 = []
        self.__fill_in_list_with_schema_id_and_url(interface5, "interface", InfoPopulator.IF_IDS[4])
        interface5.append(InfoPopulator.IF_URNS[4])
        interface5.append(str(int(time.time() * 1000000)))
        interface5.append("control")  # role
        interface5.append(str(10000000))  # max bps
        interface5.append(str(1000000))  # max pps
        interface5.append(InfoPopulator.get_parent_if_id(4))  # Parent id
        interface5.append(InfoPopulator.get_node_id_for_if_idx(4))  # Node id

        if not info_insert(self.tbl_mgr, "ops_interface", interface5):
            ok = False

        interface6 = []
        self.__fill_in_list_with_schema_id_and_url(interface6, "interface", InfoPopulator.IF_IDS[5])
        interface6.append(InfoPopulator.IF_URNS[5])
        interface6.append(str(int(time.time() * 1000000)))
        interface6.append("control")  # role
        interface6.append(str(10000000))  # max bps
        interface6.append(str(1000000))  # max pps
        interface6.append(InfoPopulator.get_parent_if_id(5))  # Parent id
        interface6.append(InfoPopulator.get_node_id_for_if_idx(5))  # Node id

        if not info_insert(self.tbl_mgr, "ops_interface", interface6):
            ok = False

        remoteinterface1 = []
        self.__fill_in_list_with_schema_id_and_url(remoteinterface1, "interface", InfoPopulator.IF_IDS[6])
        remoteinterface1.append(InfoPopulator.IF_URNS[6])
        remoteinterface1.append(str(int(time.time() * 1000000)))
        remoteinterface1.append("stub")  # role
        remoteinterface1.append(str(10000000))  # max bps
        remoteinterface1.append(str(1000000))  # max pps
        remoteinterface1.append(InfoPopulator.get_parent_if_id(6))  # Parent id
        remoteinterface1.append(InfoPopulator.get_node_id_for_if_idx(6))  # Node id

        if not info_insert(self.tbl_mgr, "ops_interface", remoteinterface1):
            ok = False

        for i in range(len(InfoPopulator.IF_IDS)):
            for j in range(len(InfoPopulator.IF_ADDRESS_RELATIONS)):
                if InfoPopulator.IF_IDS[i] == InfoPopulator.IF_ADDRESS_RELATIONS[j][0]:
                    addr_idx = InfoPopulator.IF_ADDRESS_RELATIONS[j][1]
                    interfaceaddr = []
                    interfaceaddr.append(InfoPopulator.IF_IDS[i])  # interface_id
                    interfaceaddr.append(InfoPopulator.IF_ADDRESSES[addr_idx][0])  # addrtype
                    interfaceaddr.append(InfoPopulator.IF_ADDRESSES[addr_idx][1])  # scope
                    interfaceaddr.append(InfoPopulator.IF_ADDRESSES[addr_idx][2])  # address
                    if not info_insert(self.tbl_mgr, "ops_interface_addresses", interfaceaddr):
                        ok = False


        vlan1 = InfoPopulator.VLAN_ID

        interfacevlan1 = []
        self.__fill_in_list_with_schema_id_and_url(interfacevlan1, "interfacevlan", InfoPopulator.IFVLAN_IDS[0])
        interfacevlan1.append(InfoPopulator.IFVLAN_URNS[0])
        interfacevlan1.append(str(int(time.time() * 1000000)))
        interfacevlan1.append(str(vlan1))  # tag type
        if_idx = InfoPopulator.get_ifvlan_if_idx(0)
        interfacevlan1.append(InfoPopulator.IF_IDS[if_idx])  # Interface ID
        if not info_insert(self.tbl_mgr, "ops_interfacevlan", interfacevlan1):
            ok = False


        interfacevlan2 = []
        self.__fill_in_list_with_schema_id_and_url(interfacevlan2, "interfacevlan", InfoPopulator.IFVLAN_IDS[1])
        interfacevlan2.append(InfoPopulator.IFVLAN_URNS[1])
        interfacevlan2.append(str(int(time.time() * 1000000)))
        interfacevlan2.append(str(vlan1))  # tag type
        if_idx = InfoPopulator.get_ifvlan_if_idx(1)
        interfacevlan2.append(InfoPopulator.IF_IDS[if_idx])  # Interface ID
        if not info_insert(self.tbl_mgr, "ops_interfacevlan", interfacevlan2):
            ok = False

        interfacevlan3 = []
        self.__fill_in_list_with_schema_id_and_url(interfacevlan3, "interfacevlan", InfoPopulator.IFVLAN_IDS[2])
        interfacevlan3.append(InfoPopulator.IFVLAN_URNS[2])
        interfacevlan3.append(str(int(time.time() * 1000000)))
        interfacevlan3.append(str(vlan1))  # tag type
        if_idx = InfoPopulator.get_ifvlan_if_idx(2)
        interfacevlan3.append(InfoPopulator.IF_IDS[if_idx])  # Interface ID
        if not info_insert(self.tbl_mgr, "ops_interfacevlan", interfacevlan3):
            ok = False


        remoteinterfacevlan1 = []
        self.__fill_in_list_with_schema_id_and_url(remoteinterfacevlan1, "interfacevlan", InfoPopulator.IFVLAN_IDS[3])
        remoteinterfacevlan1.append(InfoPopulator.IFVLAN_URNS[3])
        remoteinterfacevlan1.append(str(int(time.time() * 1000000)))
        remoteinterfacevlan1.append(str(vlan1))  # tag type
        if_idx = InfoPopulator.get_ifvlan_if_idx(3)
        remoteinterfacevlan1.append(InfoPopulator.IF_IDS[if_idx])  # Interface ID
        if not info_insert(self.tbl_mgr, "ops_interfacevlan", remoteinterfacevlan1):
            ok = False


        authority1 = []
        self.__fill_in_list_with_schema_id_and_url(authority1, "authority", "ch.geni.net")
        authority1.append("urn:publicid:IDN+ch.geni.net+authority+ch")
        authority1.append(str(int(time.time() * 1000000)))

        if not info_insert(self.tbl_mgr, "ops_authority", authority1):
            ok = False

        slice1 = []
        self.__fill_in_list_with_schema_id_and_url(slice1, "slice", "ch.geni.net_gpo-infra_slice_tuptyexclusive")
        slice1.append("urn:publicid:IDN+ch.geni.net:gpo-infra+slice+tuptyexclusive")
        slice1.append("8c6b97fa-493b-400f-95ee-19accfaf4ae8")
        slice1.append(str(int(time.time() * 1000000)))
        slice1.append(authority1[1])  # authority id
        slice1.append("1391626683000000")
        slice1.append("1391708989000000")

        if not info_insert(self.tbl_mgr, "ops_slice", slice1):
            ok = False


        user1 = []
        self.__fill_in_list_with_schema_id_and_url(user1, "user", "tupty")
        user1.append("tupty_user_urn")
        user1.append(str(int(time.time() * 1000000)))
        user1.append(authority1[1])  # authority id
        user1.append("Tim Exampleuser")
        user1.append("tupty@example.com")

        if not info_insert(self.tbl_mgr, "ops_user", user1):
            ok = False


#         aggres1 = []
#         aggres1.append(node1[1])
#         aggres1.append(agg1[1])
#
#         if not info_insert(self.tbl_mgr, "ops_aggregate_resource", aggres1):
#             ok = False
#
#         aggres2 = []
#         aggres2.append(node2[1])
#         aggres2.append(agg1[1])
#
#         if not info_insert(self.tbl_mgr, "ops_aggregate_resource", aggres2):
#             ok = False
#
#
#         aggres3 = []
#         aggres3.append(node3[1])
#         aggres3.append(agg1[1])
#
#         if not info_insert(self.tbl_mgr, "ops_aggregate_resource", aggres3):
#             ok = False
#
#
#         aggres4 = []
#         aggres4.append(node4[1])
#         aggres4.append(agg1[1])
#
#         if not info_insert(self.tbl_mgr, "ops_aggregate_resource", aggres4):
#             ok = False
#
#
#         aggres5 = []
#         aggres5.append(node5[1])
#         aggres5.append(agg1[1])
#
#         if not info_insert(self.tbl_mgr, "ops_aggregate_resource", aggres5):
#             ok = False
#
#
#         aggres6 = []
#         aggres6.append(link1[1])
#         aggres6.append(agg1[1])
#
#         if not info_insert(self.tbl_mgr, "ops_aggregate_resource", aggres6):
#             ok = False
#
#
#         aggres7 = []
#         aggres7.append(sublink1[1])
#         aggres7.append(agg1[1])
#
#         if not info_insert(self.tbl_mgr, "ops_aggregate_resource", aggres7):
#             ok = False
#
#
#         aggres8 = []
#         aggres8.append(sublink2[1])
#         aggres8.append(agg1[1])
#
#         if not info_insert(self.tbl_mgr, "ops_aggregate_resource", aggres8):
#             ok = False
#
#
#         aggres9 = []
#         aggres9.append(egress_link[1])
#         aggres9.append(agg1[1])
#
#         if not info_insert(self.tbl_mgr, "ops_aggregate_resource", aggres9):
#             ok = False
#
#
#         aggres10 = []
#         aggres10.append(switch1[1])
#         aggres10.append(agg1[1])
#
#         if not info_insert(self.tbl_mgr, "ops_aggregate_resource", aggres10):
#             ok = False


#         aggsliv1 = []
#         aggsliv1.append(sliver1[1])  # id
#         aggsliv1.append(agg1[1])
#
#         if not info_insert(self.tbl_mgr, "ops_aggregate_sliver", aggsliv1):
#             ok = False
#
#
#         aggsliv2 = []
#         aggsliv2.append(sliver2[1])  # id
#         aggsliv2.append(agg1[1])
#
#         if not info_insert(self.tbl_mgr, "ops_aggregate_sliver", aggsliv2):
#             ok = False
#
#
#         aggsliv3 = []
#         aggsliv3.append(sliver3[1])  # id
#         aggsliv3.append(agg1[1])
#
#         if not info_insert(self.tbl_mgr, "ops_aggregate_sliver", aggsliv3):
#             ok = False
#
#
#         aggsliv4 = []
#         aggsliv4.append(sliver4[1])  # id
#         aggsliv4.append(agg1[1])
#
#         if not info_insert(self.tbl_mgr, "ops_aggregate_sliver", aggsliv4):
#             ok = False

#         for node_if_idxes in InfoPopulator.NODE_IF_RELATIONS:
#             node_idx = node_if_idxes[0]
#             if_idx = node_if_idxes[1]
#             nodeiface = []
#             nodeiface.append(InfoPopulator.IF_IDS[if_idx])
#             nodeiface.append(InfoPopulator.NODE_IDS[node_idx])
#             nodeiface.append(InfoPopulator.IF_URNS[if_idx])
#             if_url = self.__get_selfRef_url_for("interface", InfoPopulator.IF_IDS[if_idx])
#             nodeiface.append(if_url)
#
#             if not info_insert(self.tbl_mgr, "ops_node_interface", nodeiface):
#                 ok = False


        for i in range(len(InfoPopulator.LINK_VLAN_RELATIONS)):
            link1ifacevlan = []
            link1ifacevlan.append(InfoPopulator.LINK_VLAN_RELATIONS[i][0])  # id
            link1ifacevlan.append(InfoPopulator.LINK_VLAN_RELATIONS[i][1])  # link_id

            if not info_insert(self.tbl_mgr, "ops_link_interfacevlan", link1ifacevlan):
                ok = False


        sliceuser1 = []
        sliceuser1.append(user1[1])
        sliceuser1.append(slice1[1])
        sliceuser1.append("lead")

        if not info_insert(self.tbl_mgr, "ops_slice_user", sliceuser1):
            ok = False


#         authuser1 = []
#         authuser1.append(user1[1])
#         authuser1.append(authority1[1])
#
#         if not info_insert(self.tbl_mgr, "ops_authority_user", authuser1):
#             ok = False


#         authslice1 = []
#         authslice1.append(slice1[1])
#         authslice1.append(authority1[1])
#
#         if not info_insert(self.tbl_mgr, "ops_authority_slice", authslice1):
#             ok = False

        return ok

    def update_ts_in_record(self, ts, tablename, obj_id):
        self.tbl_mgr.execute_sql("UPDATE " + tablename + " SET ts=" + str(ts) + " WHERE id='" + obj_id + "'")


    def update_fake_info(self):
        update_time = int(time.time() * 1000000)
        self.update_ts_in_record(update_time, "ops_aggregate", InfoPopulator.AGGREGATE_ID)
        for node_id in InfoPopulator.NODE_IDS:
            self.update_ts_in_record(update_time, "ops_node", node_id)
        for link_id in InfoPopulator.LINK_IDS:
            self.update_ts_in_record(update_time, "ops_link", link_id)
        for if_id in InfoPopulator.IF_IDS:
            self.update_ts_in_record(update_time, "ops_interface", if_id)
        for ifvlan_id in InfoPopulator.IFVLAN_IDS:
            self.update_ts_in_record(update_time, "ops_interfacevlan", ifvlan_id)
        for sliver_id in InfoPopulator.SLIVER_IDS:
            self.update_ts_in_record(update_time, "ops_sliver", sliver_id)

    # Dummy information to test the external check store
    def insert_externalcheck_store(self):
        return self.insert_externalcheck_store_info()

    def insert_externalcheck_store_info(self):
        ok = True
        extck_id = "gpo"
        ts = str(int(time.time() * 1000000))
        extck = []
        self.__fill_in_list_with_schema_id_and_url(extck, "externalcheck", extck_id)
        extck.append(ts)
        extck.append(self.url_base + "/data/")
        if not info_insert(self.tbl_mgr, "ops_externalcheck", extck):
            ok = False

        exp1_id = "missouri_ig_to_gpo_ig"

        exp1 = []
        self.__fill_in_list_with_schema_id_and_url(exp1, "experiment", exp1_id)
        exp1.append(ts)
        exp1.append("urn:slice_urn")
        exp1.append("uuid:slice_uuid")
        exp1.append("urn:source_aggregate_urn")
        exp1.append("source aggregate local datastore href")
        exp1.append("urn:destination_aggregate_urn")
        exp1.append("destination aggregate local datastore href")
        exp1.append(extck_id)
        if not info_insert(self.tbl_mgr, "ops_experiment", exp1):
            ok = False

#         extck_exp1 = []
#         extck_exp1.append(exp1_id)
#         extck_exp1.append(extck_id)
#         if not info_insert(self.tbl_mgr, "ops_externalcheck_experiment", extck_exp1):
#             ok = False

        mon_agg = []
        mon_agg.append(InfoPopulator.AGGREGATE_ID)
        mon_agg.append(extck_id)
        if not info_insert(self.tbl_mgr, "ops_externalcheck_monitoredaggregate", mon_agg):
            ok = False

        return ok


def info_insert(tbl_mgr, table_str, row_arr):
    """
    Function to insert values into a table.
    :param tbl_mgr: the instance of TableManager to use.
    :param table_str: the name of the table to insert into.
    :param row_arr: a list of values.  If any of the values are None,
                    they are translated to a SQL NULL.
    :return: True if the insertion happened correctly, false otherwise.
    """
    val_str = "("

    for col in range(len(row_arr)):
        if col > 0:
            val_str += ", "
        if row_arr[col] is None:
            val_str += "NULL"
        else:
            val_str += "'" + row_arr[col] + "'"
    val_str += ")"

    return tbl_mgr.insert_stmt(table_str, val_str)


def main():

    db_name = "local"
    config_path = "../config/"

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
