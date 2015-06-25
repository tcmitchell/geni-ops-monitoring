#!/usr/bin/python
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


import unittest
import requests
import json
import sys
import os
import subprocess
import time
from optparse import OptionParser

ut_path = os.path.abspath(os.path.dirname(__file__))
local_path = os.path.dirname(ut_path)
top_path = os.path.dirname(local_path)
common_path = os.path.join(top_path, "common")
config_path = os.path.join(top_path, "config/")
sys.path.append(local_path)
sys.path.append(common_path)
sys.path.append(ut_path)
import table_manager
import opsconfig_loader
import info_populator
import stats_populator


class TestResponses(unittest.TestCase):
    NUM_INS = 10;
    PER_SEC = 0.2;
    BASE_SCHEMA = "http://www.gpolab.bbn.com/monitoring/schema/20150625/"

    CERT_PATH = "/vagrant/collector-gpo-withnpkey2.pem"
    IP_ADDR_FILE = "/tmp/ip.conf"

    def __init__(self, methodName):
        super(TestResponses, self).__init__(methodName)
        db_type = "local"
        self.tbl_mgr = table_manager.TableManager(db_type, config_path)
        self.tbl_mgr.poll_config_store()

        ocl = opsconfig_loader.OpsconfigLoader(config_path)
        self.event_types = ocl.get_event_types()

        f = open(TestResponses.IP_ADDR_FILE)
        self.ip = f.read().strip()
        f.close()
        self.base_url = "https://%s" % self.ip

    def db_cleanup(self):
        print
        print "Cleaning up DB tables"
        if not self.tbl_mgr.drop_all_tables():
            self.fail("Could not clean up tables");
        if not self.tbl_mgr.establish_all_tables():
            self.fail("Could not establish all tables");

    def setUp(self):
        super(TestResponses, self).setUp()
        self.startTime = int(time.time() * 1000000)
        # dropping existing tables
        self.db_cleanup()

    def tearDown(self):
        self.db_cleanup()
        super(TestResponses, self).tearDown()

    def request_url(self, url, cert_path):
        resp = None
        http_headers = {}
        status_string = "No Response"
        fail_str = None

        try:
            print "fetching content for %s" % url
            resp = requests.get(url, verify=False, cert=cert_path,
                                headers=http_headers)
            status_string = str(resp.status_code) + " " + resp.reason
        except Exception as e:
            fail_str = "No response from local datastore for URL %s\n%s" % (url, str(e))

        return (resp, status_string, fail_str)

    def check_json_dictionary_for_field_presence(self, dict, fieldName, desc):
        self.assertTrue(dict.has_key(fieldName),
                        "json dictionary for %s does not contains the expected field %s" % (desc, fieldName))

    def check_json_dictionary_for_field_absence(self, dict, fieldName, desc):
        self.assertFalse(dict.has_key(fieldName),
                        "json dictionary for %s does contains the unexpected field %s" % (desc, fieldName))

    def check_json_dictionary_for_field(self, dict, fieldName, fieldValue, desc):
        self.check_json_dictionary_for_field_presence(dict, fieldName, desc)
        self.assertEqual(dict[fieldName], fieldValue,
                         "json dictionary for %s does not contains the expected value for field %s" % (desc, fieldName));

    def find_keys_and_values_in_json_array(self, json_array, expected_dict, id_key, obj_desc):
        for i in range(len(json_array)):
            obj_dict = json_array[i]
            if obj_dict.has_key(id_key) and obj_dict[id_key] == expected_dict[id_key]:
                break
        else:
            self.fail("Did not find %s with %s %s" % (obj_desc, id_key, expected_dict[id_key]))

        for key in expected_dict.keys():
            if key != id_key:
                self.assertTrue(obj_dict.has_key(key), "%s json object does not have an %s field" % (obj_desc, key))
                self.assertEqual(expected_dict[key], obj_dict[key], "unexpected %s for %s %s" % (key, obj_desc, expected_dict[id_key]))

    def find_urn_and_href_object_in_json_array(self, json_array, urn, href, obj_desc):
        expected_dict = dict()
        expected_dict['urn'] = urn
        expected_dict['href'] = href
        self.find_keys_and_values_in_json_array(json_array, expected_dict, 'urn', obj_desc)
#         for i in range(len(json_array)):
#             obj_dict = json_array[i]
#             if obj_dict.has_key("urn") and obj_dict["urn"] == urn:
#                 break
#         else:
#             self.fail("Did not find %s with urn %s" % (obj_desc, urn))
#
#         self.assertTrue(obj_dict.has_key("href"), "%s json object does not have an href field" % obj_desc)
#         self.assertEqual(href, obj_dict["href"], "unexpected href for %s %s" % (obj_desc, urn))



    def get_json_dictionary(self, url):
        (resp, status, fail_msg) = self.request_url(url, TestResponses.CERT_PATH)
        print status
        json_dict = None
        if fail_msg is not None:
            self.fail(fail_msg)
        else:
            try:
                json_dict = json.loads(resp.content)
            except Exception as e:
                self.fail("Could not parse JSON from URL %s, %s\n%s" % (url, resp.content,
                                                                    str(e)))
        return json_dict

    def check_error_response(self, url, expected_error):
        import urlparse
        error_dict = self.get_json_dictionary(url)
        self.check_json_dictionary_for_field(error_dict, "$schema", TestResponses.BASE_SCHEMA + "error#", "JSON Error response")
        self.check_json_dictionary_for_field(error_dict, "error_message", expected_error, "JSON Error response")
        parseRes = urlparse.urlparse(url)
        self.check_json_dictionary_for_field(error_dict, "origin_url", parseRes.path, "JSON Error response")

class TestLocalResponses(TestResponses):
    NEW_PURGE_TIMEOUT = 100
    NEW_PURGE_PERIOD = 15


    def __init__(self, methodName):
        super(TestLocalResponses, self).__init__(methodName)

    def populate_info(self):
        ip = info_populator.InfoPopulator(self.tbl_mgr, self.base_url)
        if not ip.insert_fake_info():
            self.fail("Could not insert test info data into tables");

    def populate_measurements(self):
        threads = []

        obj_type = "node"
        for node_id in info_populator.InfoPopulator.NODE_IDS:
            node_sp = stats_populator.StatsPopulator(self.tbl_mgr, obj_type,
                                                     node_id,
                                                     TestResponses.NUM_INS,
                                                     TestResponses.PER_SEC,
                                                     self.event_types[obj_type])
            threads.append(node_sp)

        obj_type = "interface"
        for if_id in info_populator.InfoPopulator.IF_IDS:
            interface_sp = stats_populator.StatsPopulator(self.tbl_mgr, obj_type,
                                                          if_id,
                                                          TestResponses.NUM_INS,
                                                          TestResponses.PER_SEC,
                                                          self.event_types[obj_type])
            threads.append(interface_sp)

        obj_type = "interfacevlan"
        for ifvlan_id in info_populator.InfoPopulator.IFVLAN_IDS:
            interfacevlan_sp = stats_populator.StatsPopulator(self.tbl_mgr, obj_type,
                                                              ifvlan_id,
                                                              TestResponses.NUM_INS,
                                                              TestResponses.PER_SEC,
                                                              self.event_types[obj_type])
            threads.append(interfacevlan_sp)

        obj_type = "aggregate"
        aggregate_sp = stats_populator.StatsPopulator(self.tbl_mgr, obj_type,
                                                      info_populator.InfoPopulator.AGGREGATE_ID,
                                                      TestResponses.NUM_INS,
                                                      TestResponses.PER_SEC,
                                                      self.event_types[obj_type])
        threads.append(aggregate_sp)

        # start threads
        for t in threads:
            t.start()

        ok = True
        # join all threads
        for t in threads:
            t.join()
            if not t.run_ok:
                ok = False

        if not ok:
            self.fail("Error while inserting measurement data into tables");

    def restart_apache(self):
        # this works on Ubuntu.
        subprocess.call(["sudo", "/usr/sbin/service", "apache2", "restart"])

    def modify_purging_values(self, timeout, period):
        local_config_file = os.path.join(config_path, "local_datastore_operator.conf")
        subprocess.call(["sed", "-i", "s/^aging_timeout:.*/aging_timeout: %s/" % str(timeout), local_config_file])
        subprocess.call(["sed", "-i", "s/^purge_period:.*/purge_period: %s/" % str(period), local_config_file])

    def setUp(self):
        super(TestLocalResponses, self).setUp()

        if "purge" in self.id():
            self.saved_timeout = self.tbl_mgr.conf_loader.get_aging_timeout()
            self.saved_period = self.tbl_mgr.conf_loader.get_purge_period()
            self.modify_purging_values(TestLocalResponses.NEW_PURGE_TIMEOUT, TestLocalResponses.NEW_PURGE_PERIOD)
            self.restart_apache()


        self.populate_info()

        if ("stats" in self.id()) or ("purge" in self.id()):
            self.populate_measurements()

        print
        print "Done with setUp()"
        self.endOfSetUp = int(time.time() * 1000000)


    def tearDown(self):
        if "purge" in self.id():
            self.modify_purging_values(self.saved_timeout, self.saved_period)
            self.restart_apache()
        super(TestLocalResponses, self).tearDown()


    def test_get_aggregate_info(self):
        url = self.base_url + "/info/aggregate/" + info_populator.InfoPopulator.AGGREGATE_ID
        json_dict = self.get_json_dictionary(url)

        desc = "aggregate %s info" % info_populator.InfoPopulator.AGGREGATE_ID

        self.assertIsNotNone(json_dict, "Error parsing return from %s" % url)
        self.check_json_dictionary_for_field(json_dict, "$schema", TestLocalResponses.BASE_SCHEMA + "aggregate#", desc)
        self.check_json_dictionary_for_field(json_dict, "selfRef", url, desc)
        self.check_json_dictionary_for_field(json_dict, "id", info_populator.InfoPopulator.AGGREGATE_ID, desc)
        self.check_json_dictionary_for_field(json_dict, "urn", info_populator.InfoPopulator.AGGREGATE_URN, desc)

        expected_measRef = self.base_url + "/data/"
        self.check_json_dictionary_for_field(json_dict, "measRef", expected_measRef, desc)
        self.check_json_dictionary_for_field(json_dict, "operational_status", "development", desc)
        self.check_json_dictionary_for_field_presence(json_dict, "ts", desc)
        self.check_json_dictionary_for_field_presence(json_dict, "monitoring_version", desc)
        self.check_json_dictionary_for_field(json_dict, "populator_version", info_populator.InfoPopulator.POPULATOR_VERSION, desc)
        self.check_json_dictionary_for_field_presence(json_dict, "resources", desc)
        self.check_json_dictionary_for_field_presence(json_dict, "slivers", desc)

        for i in range(len(info_populator.InfoPopulator.SLIVER_IDS)):
            self.find_urn_and_href_object_in_json_array(json_dict["slivers"],
                                                        info_populator.InfoPopulator.SLIVER_URNS[i],
                                                        "%s/info/sliver/%s" % (self.base_url, info_populator.InfoPopulator.SLIVER_IDS[i]),
                                                        "sliver")

        for i in range(len(info_populator.InfoPopulator.NODE_IDS)):
           self.find_urn_and_href_object_in_json_array(json_dict["resources"],
                                                       info_populator.InfoPopulator.NODE_URNS[i],
                                                       "%s/info/node/%s" % (self.base_url, info_populator.InfoPopulator.NODE_IDS[i]),
                                                       'resource')
        for i in range(len(info_populator.InfoPopulator.LINK_IDS)):
           self.find_urn_and_href_object_in_json_array(json_dict["resources"],
                                                       info_populator.InfoPopulator.LINK_URNS[i],
                                                       "%s/info/link/%s" % (self.base_url, info_populator.InfoPopulator.LINK_IDS[i]),
                                                       'resource')


    def test_get_wrong_aggregate_info(self):
        incorrect_agg_id = info_populator.InfoPopulator.AGGREGATE_ID + "_WRONG"
        url = self.base_url + "/info/aggregate/" + incorrect_agg_id
        self.check_error_response(url, ("aggregate not found: " + incorrect_agg_id))

    def _get_node_interface(self, node_idx):
        for node_if_idxes in info_populator.InfoPopulator.NODE_IF_RELATIONS:
            if node_idx == node_if_idxes[0]:
                return node_if_idxes[1]
        return None

    def _node_has_interface(self, node_idx):
        if self._get_node_interface(node_idx) is None:
            return False
        return True

    def test_get_nodes_info(self):
        for i in range(len(info_populator.InfoPopulator.NODE_IDS)):
            url = self.base_url + "/info/node/" + info_populator.InfoPopulator.NODE_IDS[i]
            json_dict = self.get_json_dictionary(url)
            self.assertIsNotNone(json_dict, "Error parsing return from %s" % url)
            desc = "node %s info" % info_populator.InfoPopulator.NODE_IDS[i]
            self.check_json_dictionary_for_field(json_dict, "$schema", TestLocalResponses.BASE_SCHEMA + "node#", desc)
            self.check_json_dictionary_for_field(json_dict, "selfRef", url, desc)
            self.check_json_dictionary_for_field(json_dict, "id", info_populator.InfoPopulator.NODE_IDS[i], desc)
            self.check_json_dictionary_for_field(json_dict, "urn", info_populator.InfoPopulator.NODE_URNS[i], desc)
            self.check_json_dictionary_for_field_presence(json_dict, "ts", desc)
            self.check_json_dictionary_for_field_presence(json_dict, "node_type", desc)
            if json_dict["node_type"] == "server" or json_dict["node_type"] == "vm":
                self.check_json_dictionary_for_field_presence(json_dict, "virtualization_type", desc)
            self.check_json_dictionary_for_field_presence(json_dict, "ops_monitoring:mem_total_kb", desc)
            if self._node_has_interface(i):
                self.check_json_dictionary_for_field_presence(json_dict, "interfaces", desc)
                if_array = json_dict["interfaces"]
                if_idx = self._get_node_interface(i)
                self.find_urn_and_href_object_in_json_array(if_array,
                                                            info_populator.InfoPopulator.IF_URNS[if_idx],
                                                            "%s/info/interface/%s" % (self.base_url, info_populator.InfoPopulator.IF_IDS[if_idx]),
                                                            "interface")
            else:
                self.check_json_dictionary_for_field_absence(json_dict, "interfaces", desc)

            parent_idx = info_populator.InfoPopulator.get_parent_node_idx(i)
            if parent_idx is None:
                self.check_json_dictionary_for_field_absence(json_dict, "parent_node", desc)
            else:
                self.check_json_dictionary_for_field_presence(json_dict, "parent_node", desc)
                parent_obj = json_dict["parent_node"]
                tmp_array = [parent_obj]
                self.find_urn_and_href_object_in_json_array(tmp_array,
                                                            info_populator.InfoPopulator.NODE_URNS[parent_idx],
                                                            "%s/info/node/%s" % (self.base_url, info_populator.InfoPopulator.NODE_IDS[parent_idx]),
                                                            "parent node")

    def test_get_wrong_node_info(self):
        incorrect_node_id = info_populator.InfoPopulator.NODE_IDS[0] + "_WRONG"
        url = self.base_url + "/info/node/" + incorrect_node_id
        self.check_error_response(url, "node not found: " + incorrect_node_id)

    def get_ifvlan_index(self, ifvlan_id):
        """
        Method to return the index in the InfoPopulator IFVLAN_IDS array of a given ifvlan_id
        @param ifvlan_id: the vlan id to look for
        """
        index = -1
        for i in range(len(info_populator.InfoPopulator.IFVLAN_IDS)):
            if ifvlan_id == info_populator.InfoPopulator.IFVLAN_IDS[i]:
                index = i
                break
        else:
            self.fail("could not find the index of interface vlan: %s" % ifvlan_id)

        return index

    def get_endpoints_indexes(self, link_id):
        """
        Method to return the indexes of the interface vlan endpoints of a given link id.
        """
        indexes = []
        for i in range(len(info_populator.InfoPopulator.LINK_VLAN_RELATIONS)):
            if link_id == info_populator.InfoPopulator.LINK_VLAN_RELATIONS[i][1]:
                indexes.append(self.get_ifvlan_index(info_populator.InfoPopulator.LINK_VLAN_RELATIONS[i][0]))

        return indexes

    def get_link_index(self, link_id):
        """
        Method to return the index in the InfoPopulator LINK_IDS array of a given link_id
        @param link_id: the link id to look for
        """
        for i in range(len(info_populator.InfoPopulator.LINK_IDS)):
            if link_id == info_populator.InfoPopulator.LINK_IDS[i]:
                index = i
                break
        else:
            self.fail("could not find the index of link: %s" % link_id)

        return index

    def get_children_link_indexes(self, link_idx):
        """
        Method to return the indexes of the children link ids of a given link index.
        :param link_idx: the index of the link being considered.
        :return: a list of children link indexes 
        """
        indexes = []
        for i in range(len(info_populator.InfoPopulator.LINK_PARENT_CHILD_RELATION)):
            if link_idx == info_populator.InfoPopulator.LINK_PARENT_CHILD_RELATION[i][0]:
                indexes.append(self.get_link_index(info_populator.InfoPopulator.LINK_PARENT_CHILD_RELATION[i][1]))
        return indexes

    def get_parent_link_index(self, link_idx):
        """
        Method to return the index of the parent link id of a given link id.
        :param link_idx: the index of the link being considered.
        :return: the index of the parent link or None if the link does not have a parent.
        """
        indexes = []
        for i in range(len(info_populator.InfoPopulator.LINK_PARENT_CHILD_RELATION)):
            if link_idx == info_populator.InfoPopulator.LINK_PARENT_CHILD_RELATION[i][1]:
                return self.get_link_index(info_populator.InfoPopulator.LINK_PARENT_CHILD_RELATION[i][0])
        return None

    def test_get_links_info(self):
        for i in range(len(info_populator.InfoPopulator.LINK_IDS)):
            url = self.base_url + "/info/link/" + info_populator.InfoPopulator.LINK_IDS[i]
            json_dict = self.get_json_dictionary(url)
            self.assertIsNotNone(json_dict, "Error parsing return from %s" % url)
            desc = "link %s info" % info_populator.InfoPopulator.LINK_IDS[i]
            self.check_json_dictionary_for_field(json_dict, "$schema", TestLocalResponses.BASE_SCHEMA + "link#", desc)
            self.check_json_dictionary_for_field(json_dict, "selfRef", url, desc)
            self.check_json_dictionary_for_field(json_dict, "id", info_populator.InfoPopulator.LINK_IDS[i], desc)
            self.check_json_dictionary_for_field(json_dict, "urn", info_populator.InfoPopulator.LINK_URNS[i], desc)
            self.check_json_dictionary_for_field_presence(json_dict, "ts", desc)
            self.check_json_dictionary_for_field_presence(json_dict, "layer", desc)
            self.check_json_dictionary_for_field_presence(json_dict, "endpoints", desc)
            endpoints_array = json_dict["endpoints"]
            vlan_indexes = self.get_endpoints_indexes(info_populator.InfoPopulator.LINK_IDS[i]);
            for vlan_idx in vlan_indexes:
                self.find_urn_and_href_object_in_json_array(endpoints_array,
                                                            info_populator.InfoPopulator.IFVLAN_URNS[vlan_idx],
                                                            "%s/info/interfacevlan/%s" % (self.base_url, info_populator.InfoPopulator.IFVLAN_IDS[vlan_idx]),
                                                            "interfacevlan")
            parent_idx = self.get_parent_link_index(i);
            if parent_idx is not None:
                self.check_json_dictionary_for_field_presence(json_dict, "parent")
                parent_array = [json_dict["parent"]]
                self.find_urn_and_href_object_in_json_array(parent_array,
                                                            info_populator.InfoPopulator.LINK_URNS[parent_idx],
                                                            "%s/info/link/%s"
                                                                % (self.base_url, info_populator.InfoPopulator.LINK_IDS[parent_idx]),
                                                            "link")
            children_indexes = self.get_children_link_indexes(info_populator.InfoPopulator.LINK_IDS[i])
            if len(children_indexes) != 0:
                self.check_json_dictionary_for_field_presence(json_dict, "children", desc)
                children_array = json_dict["children"]
                for sublink_idx in children_indexes:
                    self.find_urn_and_href_object_in_json_array(children_array,
                                                                info_populator.InfoPopulator.LINK_URNS[sublink_idx],
                                                                "%s/info/link/%s"
                                                                    % (self.base_url, info_populator.InfoPopulator.LINK_IDS[sublink_idx]),
                                                                "link")

    def test_get_wrong_link_info(self):
        incorrect_link_id = info_populator.InfoPopulator.LINK_IDS[0] + "_WRONG"
        url = self.base_url + "/info/link/" + incorrect_link_id
        self.check_error_response(url, "link not found: " + incorrect_link_id)

    def get_if_addresses_indexes(self, if_id):
        """
        Method to return the indexes of the addresses of a given interface id.
        @param if_id: the interface id
        """
        indexes = []
        for i in range(len(info_populator.InfoPopulator.IF_ADDRESS_RELATIONS)):
            if if_id == info_populator.InfoPopulator.IF_ADDRESS_RELATIONS[i][0]:
                indexes.append(info_populator.InfoPopulator.IF_ADDRESS_RELATIONS[i][1])
        return indexes

    def find_if_address_in_json_array(self, json_array, type, scope, addr):
        for i in range(len(json_array)):
            obj_dict = json_array[i]
            if obj_dict.has_key("addrtype") and obj_dict["addrtype"] == type \
                and obj_dict.has_key("address") and obj_dict["address"] == addr:
                if scope is None:
                    if not obj_dict.has_key("scope"):
                        break
                else:
                    if obj_dict.has_key("scope") and obj_dict["scope"] == scope:
                        break

        else:
            self.fail("Did not find %s with urn %s" % (obj_desc, urn))

    def test_get_ifs_info(self):
        for i in range(len(info_populator.InfoPopulator.IF_IDS)):
            url = self.base_url + "/info/interface/" + info_populator.InfoPopulator.IF_IDS[i]
            json_dict = self.get_json_dictionary(url)
            self.assertIsNotNone(json_dict, "Error parsing return from %s" % url)
            desc = "interface %s info" % info_populator.InfoPopulator.IF_IDS[i]
            self.check_json_dictionary_for_field(json_dict, "$schema", TestLocalResponses.BASE_SCHEMA + "interface#", desc)
            self.check_json_dictionary_for_field(json_dict, "selfRef", url, desc)
            self.check_json_dictionary_for_field(json_dict, "id", info_populator.InfoPopulator.IF_IDS[i], desc)
            self.check_json_dictionary_for_field(json_dict, "urn", info_populator.InfoPopulator.IF_URNS[i], desc)
            self.check_json_dictionary_for_field_presence(json_dict, "ts", desc)
            self.check_json_dictionary_for_field_presence(json_dict, "ops_monitoring:max_pps", desc)
            self.check_json_dictionary_for_field_presence(json_dict, "ops_monitoring:max_bps", desc)
            self.check_json_dictionary_for_field_presence(json_dict, "ops_monitoring:role", desc)
            addr_indexes = self.get_if_addresses_indexes(info_populator.InfoPopulator.IF_IDS[i])
            if (len(addr_indexes) == 0):
                self.check_json_dictionary_for_field_absence(json_dict, "addresses", desc)
            else:
                self.check_json_dictionary_for_field_presence(json_dict, "addresses", desc)
                for addr_idx in addr_indexes:
                    self.find_if_address_in_json_array(json_dict["addresses"],
                                                       info_populator.InfoPopulator.IF_ADDRESSES[addr_idx][0],
                                                       info_populator.InfoPopulator.IF_ADDRESSES[addr_idx][1],
                                                       info_populator.InfoPopulator.IF_ADDRESSES[addr_idx][2])


    def test_get_wrong_if_info(self):
        incorrect_if_id = info_populator.InfoPopulator.IF_IDS[0] + "_WRONG"
        url = self.base_url + "/info/interface/" + incorrect_if_id
        self.check_error_response(url, "interface not found: " + incorrect_if_id)

    def test_get_ifvlans_info(self):
        for i in range(len(info_populator.InfoPopulator.IFVLAN_IDS)):
            url = self.base_url + "/info/interfacevlan/" + info_populator.InfoPopulator.IFVLAN_IDS[i]
            json_dict = self.get_json_dictionary(url)
            self.assertIsNotNone(json_dict, "Error parsing return from %s" % url)
            desc = "interfacevlan %s info" % info_populator.InfoPopulator.IFVLAN_IDS[i]
            self.check_json_dictionary_for_field(json_dict, "$schema", TestLocalResponses.BASE_SCHEMA + "interfacevlan#", desc)
            self.check_json_dictionary_for_field(json_dict, "selfRef", url, desc)
            self.check_json_dictionary_for_field(json_dict, "id", info_populator.InfoPopulator.IFVLAN_IDS[i], desc)
            self.check_json_dictionary_for_field(json_dict, "urn", info_populator.InfoPopulator.IFVLAN_URNS[i], desc)
            self.check_json_dictionary_for_field_presence(json_dict, "ts", desc)
            self.check_json_dictionary_for_field(json_dict, "tag", info_populator.InfoPopulator.VLAN_ID, desc)
            self.check_json_dictionary_for_field_presence(json_dict, "interface", desc)
            interface_obj = json_dict["interface"]
            # just so I can reuse an existing method
            if_array = (interface_obj,)
            if_idx = info_populator.InfoPopulator.get_ifvlan_if_idx(i)
            self.find_urn_and_href_object_in_json_array(if_array,
                                                        info_populator.InfoPopulator.IF_URNS[if_idx],
                                                        self.base_url + "/info/interface/" + info_populator.InfoPopulator.IF_IDS[if_idx],
                                                        "interface")

    def test_get_wrong_ifvlan_info(self):
        incorrect_ifvlan_id = info_populator.InfoPopulator.IFVLAN_IDS[0] + "_WRONG"
        url = self.base_url + "/info/interfacevlan/" + incorrect_ifvlan_id
        self.check_error_response(url, "interfacevlan not found: " + incorrect_ifvlan_id)

    def test_get_sliver_info(self):
        for i in range(len(info_populator.InfoPopulator.SLIVER_IDS)):
            url = self.base_url + "/info/sliver/" + info_populator.InfoPopulator.SLIVER_IDS[i]
            json_dict = self.get_json_dictionary(url)
            self.assertIsNotNone(json_dict, "Error parsing return from %s" % url)
            desc = "sliver %s info" % info_populator.InfoPopulator.SLIVER_IDS[i]
            self.check_json_dictionary_for_field(json_dict, "$schema", TestLocalResponses.BASE_SCHEMA + "sliver#", desc)
            self.check_json_dictionary_for_field(json_dict, "selfRef", url, desc)
            self.check_json_dictionary_for_field(json_dict, "id", info_populator.InfoPopulator.SLIVER_IDS[i], desc)
            self.check_json_dictionary_for_field(json_dict, "urn", info_populator.InfoPopulator.SLIVER_URNS[i], desc)
            self.check_json_dictionary_for_field(json_dict, "uuid", info_populator.InfoPopulator.SLIVER_UUIDS[i], desc)
            self.check_json_dictionary_for_field(json_dict, "slice_uuid",
                                                 info_populator.InfoPopulator.SLICE_UUIDS[info_populator.InfoPopulator.SLIVER_SLICE_IDX[i]],
                                                 desc)
            self.check_json_dictionary_for_field(json_dict, "creator",
                                                 info_populator.InfoPopulator.SLIVER_USER_URNS[info_populator.InfoPopulator.SLIVER_USER_IDX[i]],
                                                 desc)
            self.check_json_dictionary_for_field_presence(json_dict, "ts", desc)
            self.check_json_dictionary_for_field_presence(json_dict, "expires", desc)
            self.check_json_dictionary_for_field_presence(json_dict, "created", desc)
            self.check_json_dictionary_for_field_presence(json_dict, "aggregate", desc)
            agg_obj = json_dict["aggregate"]
            # just so I can reuse an existing method
            agg_array = (agg_obj,)
            self.find_urn_and_href_object_in_json_array(agg_array,
                                                        info_populator.InfoPopulator.AGGREGATE_URN,
                                                        self.base_url + "/info/aggregate/" + info_populator.InfoPopulator.AGGREGATE_ID,
                                                        "aggregate")
            self.check_json_dictionary_for_field_presence(json_dict, "resources", desc)
            sliver_resources = json_dict["resources"]
            sliver_resources_relations = info_populator.InfoPopulator.SLIVER_RESOURCE_RELATION[i]
            self.assertEqual(len(sliver_resources_relations), len(sliver_resources), "unexpected number of resources associated with sliver")
            for res_obj in sliver_resources:
                self.check_json_dictionary_for_field_presence(res_obj, "resource_type", desc)
                self.check_json_dictionary_for_field_presence(res_obj, "urn", desc)
                self.check_json_dictionary_for_field_presence(res_obj, "href", desc)
                for sliver_resource_relation in sliver_resources_relations:
                    type = sliver_resource_relation[0]
                    idx = sliver_resource_relation[1]
                    if (res_obj['resource_type'] == type):
                        if type == "node":
                            urn = info_populator.InfoPopulator.NODE_URNS[idx]
                            url = self.base_url + "/info/node/" + info_populator.InfoPopulator.NODE_IDS[idx]
                        elif type == "link":
                            urn = info_populator.InfoPopulator.LINK_URNS[idx]
                            url = self.base_url + "/info/link/" + info_populator.InfoPopulator.LINK_IDS[idx]
                        else:
                            self.fail("unrecognized resource type for sliver %s" % info_populator.InfoPopulator.SLIVER_IDS[i])
                        if (res_obj['urn'] == urn) and (res_obj['href'] == url):
                            break
                else:
                    # no break in loop, so not found
                    self.fail("unexpected resource (%s, %s) for sliver %s" % (res_obj['urn'], res_obj['href'],
                                                                              info_populator.InfoPopulator.SLIVER_IDS[i]))


    def test_get_wrong_sliver_info(self):
        incorrect_sliver_id = info_populator.InfoPopulator.SLIVER_IDS[0] + "_WRONG"
        url = self.base_url + "/info/sliver/" + incorrect_sliver_id
        self.check_error_response(url, "sliver not found: " + incorrect_sliver_id)


    def translate_event_types(self, ev_types):
        evs = []
        for ev in ev_types:
            evs.append("ops_monitoring:" + ev)
        return tuple(evs)

    def construct_stats_query(self, obj_type, obj_ids, req_time, event_types):
        evs = self.translate_event_types(event_types)

        q = {"filters":{"eventType": evs,
                        "obj":{"type": obj_type,
                               "id": obj_ids},
                        "ts": {"gt": self.startTime,
                               "lt": req_time}
                        }
             }
        jsonquery = json.dumps(q)
        jsonquery = jsonquery.replace(" ", "")
        return jsonquery

    def get_units(self, obj_type, event_type):
        return self.tbl_mgr.schema_dict["units"]["ops_" + obj_type + "_" + event_type]

    def get_data_dictionary(self, obj_type, obj_ids, event_types, req_time):
        # build URL query for objects.
        jsonquery = self.construct_stats_query(obj_type, obj_ids, req_time, event_types)
        url = self.base_url + "/data/?q=" + jsonquery
        json_dict = self.get_json_dictionary(url)
        self.assertIsNotNone(json_dict, "Error parsing return from %s" % url)
        return json_dict


    def check_on_object_stats(self, obj_type, obj_ids, event_types):
        req_time = int(time.time() * 1000000)
        json_dict = self.get_data_dictionary(obj_type, obj_ids, event_types, req_time)
        self.assertTrue(len(json_dict) > 0, "Got no stats back")

        data_map = {};
        # check that every object in the dictionary corresponds to the data schema.
        desc = obj_type + " stats"
        for json_obj in json_dict:
            self.check_json_dictionary_for_field(json_obj, "$schema", TestLocalResponses.BASE_SCHEMA + "data#", desc)
            self.check_json_dictionary_for_field_presence(json_obj, "description", desc)
            self.check_json_dictionary_for_field_presence(json_obj, "tsdata", desc)
            self.check_json_dictionary_for_field_presence(json_obj, "eventType", desc)
            self.check_json_dictionary_for_field_presence(json_obj, "units", desc)
            self.check_json_dictionary_for_field_presence(json_obj, "id", desc)
            self.check_json_dictionary_for_field_presence(json_obj, "subject", desc)
            data_map[json_obj["id"]] = json_obj
            self.assertEqual(TestLocalResponses.NUM_INS, len(json_obj["tsdata"]), "Number of stats does not match what was expected")
            for tsdata in json_obj["tsdata"]:
                self.check_json_dictionary_for_field_presence(tsdata, "ts", "time and value")
                self.check_json_dictionary_for_field_presence(tsdata, "v", "time and value")
                self.assertTrue(tsdata["ts"] >= self.startTime, "time stamp is not after the start of the test")
                self.assertTrue(tsdata["ts"] <= req_time, "time stamp is not before the time of the query")

        # check that we have NUM_INS for each node and events
        for obj in obj_ids:
            for event in event_types:
                desc = "stat " + event + " for " + obj_type + " " + obj
                id_str = event + ":" + obj
                self.assertTrue(id_str in data_map.keys(), "Did not find time series for %s %s and event %s" % (obj_type, obj, event))
                data_dict = data_map[id_str]
                self.check_json_dictionary_for_field(data_dict, "eventType", "ops_monitoring:" + event, desc)
                self.check_json_dictionary_for_field(data_dict, "units", self.get_units(obj_type, event), desc)

        self.assertEqual(len(obj_ids) * len(event_types),
                         len(json_dict),
                         "did not get the expected number of statistics objects")

    def test_get_aggregate_stats(self):
        self.check_on_object_stats("aggregate", (info_populator.InfoPopulator.AGGREGATE_ID,), self.event_types["aggregate"])

    def test_get_nodes_stats(self):
        # check for all nodes
        self.check_on_object_stats("node", info_populator.InfoPopulator.NODE_IDS, self.event_types["node"])
        # check for one node and all events
        self.check_on_object_stats("node",
                                   (info_populator.InfoPopulator.NODE_IDS[0],),
                                   self.event_types["node"])
        # check for one node and one event
        self.check_on_object_stats("node",
                                   (info_populator.InfoPopulator.NODE_IDS[0],),
                                   (self.event_types["node"][0],))


    def test_get_interfaces_stats(self):
        self.check_on_object_stats("interface", info_populator.InfoPopulator.IF_IDS, self.event_types["interface"])
        # check for one interface and all events
        self.check_on_object_stats("interface",
                                   (info_populator.InfoPopulator.IF_IDS[0],),
                                   self.event_types["interface"])
        # check for one interface and one event
        self.check_on_object_stats("interface",
                                   (info_populator.InfoPopulator.IF_IDS[0],),
                                   (self.event_types["interface"][0],))

    def test_get_interfacevlans_stats(self):
        self.check_on_object_stats("interfacevlan", info_populator.InfoPopulator.IFVLAN_IDS, self.event_types["interfacevlan"])
        # check for one interfacevlan and all events
        self.check_on_object_stats("interfacevlan",
                                   (info_populator.InfoPopulator.IFVLAN_IDS[0],),
                                   self.event_types["interfacevlan"])
        # check for one interfacevlan and one event
        self.check_on_object_stats("interfacevlan",
                                   (info_populator.InfoPopulator.IFVLAN_IDS[0],),
                                   (self.event_types["interfacevlan"][0],))


    def test_purge_statistics(self):
        # short aging timeout is set up in setUp()

        # Get the initial data and make sure it's what we populated
        self.test_get_aggregate_stats()
        self.test_get_nodes_stats()
        self.test_get_interfaces_stats()
        self.test_get_interfacevlans_stats()

        # Wait more than the timeout + purging period, all the while refreshing the time stamps in info tables.
        current_time = int(time.time() * 1000000)
        time_purged = self.endOfSetUp + (TestLocalResponses.NEW_PURGE_TIMEOUT + TestLocalResponses.NEW_PURGE_PERIOD) * 1000000
        ip = info_populator.InfoPopulator(self.tbl_mgr, self.base_url)
        while current_time < time_purged:
            time.sleep(2)
            ip.update_fake_info()
            current_time = int(time.time() * 1000000)

        # make sure no data is returned.
        json_dict = self.get_data_dictionary("aggregate", (info_populator.InfoPopulator.AGGREGATE_ID,), self.event_types["aggregate"], current_time)
        print json.dumps(json_dict, indent=2)
        self.assertEqual(len(json_dict), 0, "Got some stats back")
        json_dict = self.get_data_dictionary("node", info_populator.InfoPopulator.NODE_IDS, self.event_types["node"], current_time)
        print json.dumps(json_dict, indent=2)
        self.assertEqual(len(json_dict), 0, "Got some stats back")
        json_dict = self.get_data_dictionary("interface", info_populator.InfoPopulator.IF_IDS, self.event_types["interface"], current_time)
        print json.dumps(json_dict, indent=2)
        self.assertEqual(len(json_dict), 0, "Got some stats back")
        json_dict = self.get_data_dictionary("interfacevlan", info_populator.InfoPopulator.IFVLAN_IDS, self.event_types["interfacevlan"], current_time)
        print json.dumps(json_dict, indent=2)
        self.assertEqual(len(json_dict), 0, "Got some stats back")


class TestAuthorityStoreResponses(TestResponses):

    def __init__(self, methodName):
        super(TestAuthorityStoreResponses, self).__init__(methodName)

    def populate_info(self):
        ip = info_populator.InfoPopulator(self.tbl_mgr, self.base_url)
        if not ip.insert_authority_store_info():
            self.fail("Could not insert test authority info into tables");

    def setUp(self):
        super(TestAuthorityStoreResponses, self).setUp()

        self.populate_info()

        print
        print "Done with setUp()"
        self.endOfSetUp = int(time.time() * 1000000)


    def tearDown(self):
        super(TestAuthorityStoreResponses, self).tearDown()

    def test_get_authority_info(self):
        url = self.base_url + "/info/authority/" + info_populator.InfoPopulator.AUTHORITY_ID
        json_dict = self.get_json_dictionary(url)

        desc = "authority %s info" % info_populator.InfoPopulator.AUTHORITY_URN

        self.assertIsNotNone(json_dict, "Error parsing return from %s" % url)
        self.check_json_dictionary_for_field(json_dict, "$schema", TestLocalResponses.BASE_SCHEMA + "authority#", desc)
        self.check_json_dictionary_for_field(json_dict, "selfRef", url, desc)
        self.check_json_dictionary_for_field(json_dict, "id", info_populator.InfoPopulator.AUTHORITY_ID, desc)
        self.check_json_dictionary_for_field(json_dict, "urn", info_populator.InfoPopulator.AUTHORITY_URN, desc)
        self.check_json_dictionary_for_field_presence(json_dict, "ts", desc)
        self.check_json_dictionary_for_field_presence(json_dict, "monitoring_version", desc)
        self.check_json_dictionary_for_field(json_dict, "populator_version", info_populator.InfoPopulator.POPULATOR_VERSION, desc)
        self.check_json_dictionary_for_field_presence(json_dict, "slices", desc)
        self.check_json_dictionary_for_field_presence(json_dict, "users", desc)

        for i in range(len(info_populator.InfoPopulator.AUTHORITY_SLICE_IDS)):
            self.find_urn_and_href_object_in_json_array(json_dict["slices"],
                                                        info_populator.InfoPopulator.AUTHORITY_SLICE_URNS[i],
                                                        "%s/info/slice/%s" % (self.base_url, info_populator.InfoPopulator.AUTHORITY_SLICE_IDS[i]),
                                                        "slice")
        for i in range(len(info_populator.InfoPopulator.AUTHORITY_USER_IDS)):
            self.find_urn_and_href_object_in_json_array(json_dict["users"],
                                                        info_populator.InfoPopulator.AUTHORITY_USER_URNS[i],
                                                        "%s/info/user/%s" % (self.base_url, info_populator.InfoPopulator.AUTHORITY_USER_IDS[i]),
                                                        "user")

    def test_get_wrong_authority_info(self):
        incorrect_authority_id = info_populator.InfoPopulator.AUTHORITY_ID + "_WRONG"
        url = self.base_url + "/info/authority/" + incorrect_authority_id
        self.check_error_response(url, ("authority not found: " + incorrect_authority_id))

    def test_get_user_info(self):
        for i in range(len(info_populator.InfoPopulator.AUTHORITY_USER_IDS)):
            url = self.base_url + "/info/user/" + info_populator.InfoPopulator.AUTHORITY_USER_IDS[i]
            json_dict = self.get_json_dictionary(url)

            desc = "user %s info" % info_populator.InfoPopulator.AUTHORITY_USER_IDS[i]

            self.assertIsNotNone(json_dict, "Error parsing return from %s" % url)
            self.check_json_dictionary_for_field(json_dict, "$schema", TestResponses.BASE_SCHEMA + "user#", desc)
            self.check_json_dictionary_for_field(json_dict, "selfRef", url, desc)
            self.check_json_dictionary_for_field(json_dict, "id", info_populator.InfoPopulator.AUTHORITY_USER_IDS[i], desc)
            self.check_json_dictionary_for_field(json_dict, "urn", info_populator.InfoPopulator.AUTHORITY_USER_URNS[i], desc)
            self.check_json_dictionary_for_field_presence(json_dict, "ts", desc)
            self.check_json_dictionary_for_field_presence(json_dict, "email", desc)
            self.check_json_dictionary_for_field_presence(json_dict, "fullname", desc)
            self.check_json_dictionary_for_field_presence(json_dict, "authority", desc)
            authority_obj = json_dict['authority']
            tmp_array = [authority_obj]
            self.find_urn_and_href_object_in_json_array(tmp_array,
                                                        info_populator.InfoPopulator.AUTHORITY_URN,
                                                        "%s/info/authority/%s" % (self.base_url, info_populator.InfoPopulator.AUTHORITY_ID),
                                                        "authority")

    def test_get_wrong_user_info(self):
        incorrect_user_id = info_populator.InfoPopulator.AUTHORITY_USER_IDS[0] + "_WRONG"
        url = self.base_url + "/info/user/" + incorrect_user_id
        self.check_error_response(url, ("user not found: " + incorrect_user_id))

    def test_get_slice_info(self):
        for i in range(len(info_populator.InfoPopulator.AUTHORITY_SLICE_IDS)):
            url = self.base_url + "/info/slice/" + info_populator.InfoPopulator.AUTHORITY_SLICE_IDS[i]
            json_dict = self.get_json_dictionary(url)

            desc = "slice %s info" % info_populator.InfoPopulator.AUTHORITY_SLICE_IDS[i]

            self.assertIsNotNone(json_dict, "Error parsing return from %s" % url)
            self.check_json_dictionary_for_field(json_dict, "$schema", TestResponses.BASE_SCHEMA + "slice#", desc)
            self.check_json_dictionary_for_field(json_dict, "selfRef", url, desc)
            self.check_json_dictionary_for_field(json_dict, "id", info_populator.InfoPopulator.AUTHORITY_SLICE_IDS[i], desc)
            self.check_json_dictionary_for_field(json_dict, "urn", info_populator.InfoPopulator.AUTHORITY_SLICE_URNS[i], desc)
            self.check_json_dictionary_for_field(json_dict, "uuid", info_populator.InfoPopulator.AUTHORITY_SLICE_UUIDS[i], desc)
            self.check_json_dictionary_for_field_presence(json_dict, "ts", desc)
            self.check_json_dictionary_for_field_presence(json_dict, "created", desc)
            self.check_json_dictionary_for_field_presence(json_dict, "expires", desc)
            self.check_json_dictionary_for_field_presence(json_dict, "members", desc)
            members_array = json_dict['members']
            total_mambers = 0
            for slice_user in info_populator.InfoPopulator.AUTHORITY_SLICE_USER_RELATION:
                if slice_user[0] == i:
                    expected_dict = dict()
                    expected_dict['urn'] = info_populator.InfoPopulator.AUTHORITY_USER_URNS[slice_user[1]]
                    expected_dict['href'] = "%s/info/user/%s" % (self.base_url, info_populator.InfoPopulator.AUTHORITY_USER_IDS[slice_user[1]])
                    expected_dict['role'] = slice_user[2]
                    self.find_keys_and_values_in_json_array(members_array, expected_dict, 'urn', "user")

    def test_get_wrong_slice_info(self):
        incorrect_slice_id = info_populator.InfoPopulator.AUTHORITY_SLICE_IDS[0] + "_WRONG"
        url = self.base_url + "/info/slice/" + incorrect_slice_id
        self.check_error_response(url, ("slice not found: " + incorrect_slice_id))


class TestExternalCheckStoreResponses(TestResponses):

    def __init__(self, methodName):
        super(TestExternalCheckStoreResponses, self).__init__(methodName)

    def populate_info(self):
        ip = info_populator.InfoPopulator(self.tbl_mgr, self.base_url)
        if not ip.insert_externalcheck_store():
            self.fail("Could not insert test external check info into tables");

    def setUp(self):
        super(TestExternalCheckStoreResponses, self).setUp()

        self.populate_info()

        print
        print "Done with setUp()"
        self.endOfSetUp = int(time.time() * 1000000)


    def tearDown(self):
        super(TestExternalCheckStoreResponses, self).tearDown()

    def test_get_externalcheck_info(self):
        url = self.base_url + "/info/externalcheck/" + info_populator.InfoPopulator.EXTCK_ID
        json_dict = self.get_json_dictionary(url)

        desc = "externalcheck %s info" % info_populator.InfoPopulator.EXTCK_ID

        self.assertIsNotNone(json_dict, "Error parsing return from %s" % url)
        self.check_json_dictionary_for_field(json_dict, "$schema", TestLocalResponses.BASE_SCHEMA + "externalcheck#", desc)
        self.check_json_dictionary_for_field(json_dict, "selfRef", url, desc)
        self.check_json_dictionary_for_field(json_dict, "id", info_populator.InfoPopulator.EXTCK_ID, desc)
        self.check_json_dictionary_for_field_presence(json_dict, "ts", desc)
        self.check_json_dictionary_for_field_presence(json_dict, "measRef", desc)
        self.check_json_dictionary_for_field_presence(json_dict, "monitoring_version", desc)
        self.check_json_dictionary_for_field(json_dict, "populator_version", info_populator.InfoPopulator.POPULATOR_VERSION, desc)
        self.check_json_dictionary_for_field_presence(json_dict, "experiments", desc)
        self.check_json_dictionary_for_field_presence(json_dict, "monitored_aggregates", desc)

        for i in range(len(info_populator.InfoPopulator.EXTCK_EXPERIMENT_IDS)):
            expected_dict = { "href" : "%s/info/experiment/%s" % (self.base_url, info_populator.InfoPopulator.EXTCK_EXPERIMENT_IDS[i])}
            self.find_keys_and_values_in_json_array(json_dict["experiments"],
                                                    expected_dict,
                                                    'href',
                                                    "experiment")
        for i in range(len(info_populator.InfoPopulator.EXTCK_MONITORED_AGG_IDS)):
            expected_dict = {'href': info_populator.InfoPopulator.EXTCK_MONITORED_AGG_URLS[i],
                             'id': info_populator.InfoPopulator.EXTCK_MONITORED_AGG_IDS[i]}
            self.find_keys_and_values_in_json_array(json_dict["monitored_aggregates"],
                                                    expected_dict,
                                                    'id',
                                                    "monitored aggregate")

    def test_get_wrong_externalcheck_info(self):
        incorrect_extck_id = info_populator.InfoPopulator.EXTCK_ID + "_WRONG"
        url = self.base_url + "/info/externalcheck/" + incorrect_extck_id
        self.check_error_response(url, ("external check store not found: " + incorrect_extck_id))

    def test_get_experiment_info(self):
        for i in range(len(info_populator.InfoPopulator.EXTCK_EXPERIMENT_IDS)):
            url = self.base_url + "/info/experiment/" + info_populator.InfoPopulator.EXTCK_EXPERIMENT_IDS[i]
            json_dict = self.get_json_dictionary(url)

            desc = "experiment %s info" % info_populator.InfoPopulator.EXTCK_EXPERIMENT_IDS[i]

            self.assertIsNotNone(json_dict, "Error parsing return from %s" % url)
            self.check_json_dictionary_for_field(json_dict, "$schema", TestResponses.BASE_SCHEMA + "experiment#", desc)
            self.check_json_dictionary_for_field(json_dict, "selfRef", url, desc)
            self.check_json_dictionary_for_field(json_dict, "id", info_populator.InfoPopulator.EXTCK_EXPERIMENT_IDS[i], desc)
            self.check_json_dictionary_for_field_presence(json_dict, "ts", desc)
            slice_idx = info_populator.InfoPopulator.EXTCK_EXPERIMENT_SLICE_RELATION[i]
            self.check_json_dictionary_for_field(json_dict, "slice_urn", info_populator.InfoPopulator.SLICE_URNS[slice_idx], desc)
            self.check_json_dictionary_for_field(json_dict, "slice_uuid", info_populator.InfoPopulator.SLICE_UUIDS[slice_idx], desc)
            self.check_json_dictionary_for_field_presence(json_dict, "source_aggregate", desc)
            self.check_json_dictionary_for_field_presence(json_dict, "destination_aggregate", desc)
            self.check_json_dictionary_for_field_presence(json_dict["source_aggregate"], "urn", desc)
            self.check_json_dictionary_for_field_presence(json_dict["source_aggregate"], "href", desc)
            self.check_json_dictionary_for_field_presence(json_dict["destination_aggregate"], "urn", desc)
            self.check_json_dictionary_for_field_presence(json_dict["destination_aggregate"], "href", desc)

    def test_get_wrong_experiment_info(self):
        incorrect_experiment_id = info_populator.InfoPopulator.EXTCK_EXPERIMENT_IDS[0] + "_WRONG"
        url = self.base_url + "/info/experiment/" + incorrect_experiment_id
        self.check_error_response(url, ("experiment not found: " + incorrect_experiment_id))

def main(argv):

    # Set up command-line options

    parser = OptionParser(usage="usage: %prog [options] ",
                          description="Launch the unit test checking on the local data store responses. "
                          "various unit tests are executed.")
    parser.add_option("-c", "--cert-path", dest="cert_path",
                      help="path to tool certificate file")
    parser.add_option("--xml", dest="xml_output",
#                       default=False, action="store_true",
                      help="path to the results output of the unit tests, which will happen in a JUnit XML format")

    (options, _args) = parser.parse_args()
    # Do some more checking on the options provided
    if options.cert_path:
        if not os.path.isfile(options.cert_path):
            print "cert-path %s is not a file" % (options.cert_path)
            return 1
        else:
            TestLocalResponses.CERT_PATH = options.cert_path

    print "using certificate:", TestLocalResponses.CERT_PATH
    if options.xml_output:
        # we want to output a JUnit style report
        if not os.path.isdir(options.xml_output):
            print "xml_output %s is not a folder" % (options.xml_output)
            return 1

        import xmlrunner
        # need to fake the arguments
        fake_args = [ sys.argv[0] ]
        return unittest.main(testRunner=xmlrunner.XMLTestRunner(output=options.xml_output), argv=fake_args)
    else:
        # we want the output on the console
#     unittest.main()
        suiteLocal = unittest.TestLoader().loadTestsFromTestCase(TestLocalResponses)
        suiteAuth = unittest.TestLoader().loadTestsFromTestCase(TestAuthorityStoreResponses)
        suiteExtck = unittest.TestLoader().loadTestsFromTestCase(TestExternalCheckStoreResponses)
        allTestsSuite = unittest.TestSuite([suiteLocal, suiteAuth, suiteExtck])
        return unittest.TextTestRunner(verbosity=2).run(allTestsSuite)

if __name__ == "__main__":
    main(sys.argv[1:])
