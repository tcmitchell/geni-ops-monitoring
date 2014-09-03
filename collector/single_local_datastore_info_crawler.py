#!/usr/bin/env python
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

import json
import sys
import requests
import getopt
# from pprint import pprint

common_path = "../common/"
sys.path.append(common_path)
import table_manager
import logger

# am_urls is a list of dictionaies with hrefs to reach the datastore of
# the am urn

# This program populates the collector database on every fetch

def usage():
    usage = '''
    single_local_datastore_info_crawler.py performs information
    fetching. It puts data in the collector database.  It needs to be
    called with four arguments specifying a certificate, a base URL,
    either an aggregate id or an external check id and the list of object
    types to retrieve.

     -c or --certpath= <pathname> provides the path to your tool certificate
     -b or --baseurl= <local-store-info-base-url>
        This usually starts with "https://" and the convention is to end with "/info"
     -a or --aggregateid= <aggregate_id>
        This is the aggregate ID at the base URL (value of -b) data store (i.e., gpo-ig)
     -e or --extckid= <external_check_id>
        This is the external check store ID at the base URL (value of -b) data store (i.e., gpo)
     -o or --object-types= <objecttypes-of-interest>
        This is a list of letters of object types to get info on.
        If querying information on an aggregate store:
         - n: for node
         - i: for interface
         - s: for sliver
         - l: for link
         - v: for vlan
        If querying information on an external check store:
         - x: for experiments
         - e: for external checks
        So argument -o nislv will get information on all object types for an aggregate.
     -d or --debug will print what changes would be made to the collector database
        to the screen and does not modify the database
     -h or --help prints the usage information.
    '''
    print(usage)
    sys.exit(1)

def parse_args(argv):
    if argv == []:
        usage()

    base_url = ""
    aggregate_id = ""
    extck_id = ""
    object_types = ""
    cert_path = ""
    debug = False

    try:
        opts, _ = getopt.getopt(argv, "hb:a:e:c:o:d", ["help", "baseurl=", "aggregateid=", "extckid=", "certpath=", "objecttypes=", "debug"])
    except getopt.GetoptError:
        usage()

    for opt, arg in opts:
        if opt in("-h", "--help"):
            usage()
        elif opt in ("-b", "--baseurl"):
            base_url = arg
        elif opt in ("-a", "--aggregateid"):
            aggregate_id = arg
        elif opt in ("-e", "--extckid"):
            extck_id = arg
        elif opt in ("-c", "--certpath"):
            cert_path = arg
        elif opt in ("-o", "--objecttypes"):
            object_types = arg
        elif opt in ("-d", "--debug"):
            debug = True
        else:
            usage()

    return [base_url, aggregate_id, extck_id, object_types, cert_path, debug]

class SingleLocalDatastoreInfoCrawler:

    def __init__(self, tbl_mgr, info_url, aggregate_id, extck_id, cert_path, debug, config_path):
        self.tbl_mgr = tbl_mgr
        self.logger = logger.get_logger(config_path)
        # ensures tables exist in database
        if not self.tbl_mgr.establish_all_tables():
            self.logger.critical("Could not establish all the tables. Exiting")
            sys.exit(-1)

        if info_url[-1] == '/':
            info_url = info_url[:-1]
        self.info_url = info_url
        self.aggregate_id = aggregate_id
        self.extck_id = extck_id
        self.debug = debug

        # collector certificate path
        self.cert_path = cert_path

        self.am_dict = None
        self.extck_dict = None

    # Updates head aggregate information
    def refresh_aggregate_info(self):
        self.am_dict = handle_request(self.info_url + '/aggregate/' + self.aggregate_id, self.cert_path, self.logger)
        return self.refresh_specific_aggregate_info(self.am_dict)

    def refresh_specific_aggregate_info(self, agg_dict):
        """
        Method to insert aggregate information into the aggregate table given an aggregate dictionary
        :param agg_dict: the aggregate json dictionary object containing the information to insert or
          update into the database
        :return: True if the information was inserted or updated correctly, False otherwise
        """
        ok = True
        if agg_dict:
            schema = self.tbl_mgr.schema_dict["ops_aggregate"]
            am_info_list = []
            for key in schema:
                am_info_list.append(agg_dict[key[0]])
            if not info_update(self.tbl_mgr, "ops_aggregate", schema, am_info_list, \
                               self.tbl_mgr.get_column_from_schema(schema, "id"), self.debug, self.logger):
                ok = False
        else:
            ok = False
        return ok

    # Updates externalcheck information
    def refresh_externalcheck_info(self):
        ok = True
        self.extck_dict = handle_request(self.info_url + '/externalcheck/' + self.extck_id, self.cert_path, self.logger)
        if self.extck_dict:
            schema = self.tbl_mgr.schema_dict["ops_externalcheck"]
            extck_info_list = []
            for key in schema:
                extck_info_list.append(self.extck_dict[key[0]])
            if not info_update(self.tbl_mgr, "ops_externalcheck", schema, extck_info_list, \
                               self.tbl_mgr.get_column_from_schema(schema, "id"), self.debug, self.logger):
                ok = False
        return ok

    # Updates all the monitored aggregates
    def refresh_all_monitoredaggregates_info(self):
        ok = True
        if self.extck_dict:
            schema = self.tbl_mgr.schema_dict["ops_externalcheck_monitoredaggregate"]
#             mon_aggs = []
            for mon_agg in self.extck_dict["monitored_aggregates"]:
                # Check that monitored aggregate ID exists in ops_aggregates
                # if not, get the info from the href and insert it
                agg_id = mon_agg["id"]
                agg_url = mon_agg["href"]
                insert = True
                if not self.check_exists("ops_aggregate", "id", agg_id):
                    agg_dict = handle_request(agg_url, self.cert_path, self.logger)
                    if not self.refresh_specific_aggregate_info(agg_dict):
                        ok = False
                        insert = False
                if insert:
                    mon_agg_info = [agg_id, self.extck_dict["id"], agg_url]
                    if not info_update(self.tbl_mgr, "ops_externalcheck_monitoredaggregate", schema, mon_agg_info, \
                                       (self.tbl_mgr.get_column_from_schema(schema, "id"), self.tbl_mgr.get_column_from_schema(schema, "externalcheck_id")),
                                       self.debug, self.logger):
                        ok = False
        return ok

    def refresh_all_experiments_info(self):
        """
        Method to refresh the experiment information associated with an external check store
        :return: True if everything went fine, false otherwise.
        """
        ok = True
        if self.extck_dict:
            schema = self.tbl_mgr.schema_dict["ops_externalcheck_experiment"]
            exp_schema = self.tbl_mgr.schema_dict["ops_experiment"]

            for experiment in self.extck_dict["experiments"]:
                # Check that monitored aggregate ID exists in ops_aggregates
                # if not, get the info from the href and insert it
                experiment_url = experiment["href"]
                insert = True
                experiment_dict = handle_request(experiment_url, self.cert_path, self.logger)
                experiment_info_list = self.get_experiment_attributes(experiment_dict, exp_schema)
                if not info_update(self.tbl_mgr, "ops_experiment", exp_schema, experiment_info_list, \
                                   self.tbl_mgr.get_column_from_schema(exp_schema, "id"),
                                   self.debug, self.logger):
                        ok = False
                        insert = False
                if insert:
                    experiment_relation_info = [experiment_dict["id"], self.extck_dict["id"], experiment_url]
                    if not info_update(self.tbl_mgr, "ops_externalcheck_experiment", schema, experiment_relation_info, \
                                       (self.tbl_mgr.get_column_from_schema(schema, "id"), self.tbl_mgr.get_column_from_schema(schema, "externalcheck_id")),
                                       self.debug, self.logger):
                        ok = False
        return ok

    # Updates all nodes information
    def refresh_all_links_info(self):
        ok = True
        if self.am_dict:
            schema = self.tbl_mgr.schema_dict["ops_link"]
            res_schema = self.tbl_mgr.schema_dict["ops_aggregate_resource"]
            # Need to check because "resources" is optional
            if "resources" in self.am_dict:
                for res_i in self.am_dict["resources"]:
                    res_dict = handle_request(res_i["href"], self.cert_path, self.logger)
                    if res_dict:
                        if res_dict["$schema"].endswith("link#"):  # if a link
                            # get each attribute out of response into list
                            link_info_list = self.get_link_attributes(res_dict, schema)
                            if not info_update(self.tbl_mgr, "ops_link", schema, link_info_list, \
                                               self.tbl_mgr.get_column_from_schema(schema, "id"), self.debug, self.logger):
                                ok = False
                        agg_res_info_list = [res_dict["id"], self.am_dict["id"], res_dict["urn"], res_dict["selfRef"]]
                        if not info_update(self.tbl_mgr, "ops_aggregate_resource", res_schema, agg_res_info_list, \
                                           self.tbl_mgr.get_column_from_schema(res_schema, "id"), self.debug, self.logger):
                            ok = False
        return ok


    def refresh_all_slivers_info(self):
        ok = True
        if self.am_dict:
            schema = self.tbl_mgr.schema_dict["ops_sliver"]
            res_schema = self.tbl_mgr.schema_dict["ops_aggregate_sliver"]
            # Need to check because "slivers" is optional
            if "slivers" in self.am_dict:
                for slv_i in self.am_dict["slivers"]:
                    slv_dict = handle_request(slv_i["href"], self.cert_path, self.logger)
                    if slv_dict:
                        # get each attribute out of response into list
                        slv_info_list = self.get_sliver_attributes(slv_dict, schema)
                        if not info_update(self.tbl_mgr, "ops_sliver", schema, slv_info_list, \
                                           self.tbl_mgr.get_column_from_schema(schema, "id"), self.debug, self.logger):
                            ok = False
                        agg_slv_info_list = [slv_dict["id"], self.am_dict["id"], slv_dict["urn"], slv_dict["selfRef"]]
                        if not info_update(self.tbl_mgr, "ops_aggregate_sliver", res_schema, agg_slv_info_list, \
                                           self.tbl_mgr.get_column_from_schema(res_schema, "id"), self.debug, self.logger):
                            ok = False
        return ok


    def refresh_all_nodes_info(self):
        ok = True
        if self.am_dict:
            schema = self.tbl_mgr.schema_dict["ops_node"]
            res_schema = self.tbl_mgr.schema_dict["ops_aggregate_resource"]
            # Need to check because "resources" is optional
            if "resources" in self.am_dict:
                for res_i in self.am_dict["resources"]:
                    res_dict = handle_request(res_i["href"], self.cert_path, self.logger)
                    if res_dict:
                        if res_dict["$schema"].endswith("node#"):  # if a node
                            # get each attribute out of response into list
                            node_info_list = self.get_node_attributes(res_dict, schema)
                            if not info_update(self.tbl_mgr, "ops_node", schema, node_info_list, \
                                               self.tbl_mgr.get_column_from_schema(schema, "id"), self.debug, self.logger):
                                ok = False
                        agg_res_info_list = [res_dict["id"], self.am_dict["id"], res_dict["urn"], res_dict["selfRef"]]
                        if not info_update(self.tbl_mgr, "ops_aggregate_resource", res_schema, agg_res_info_list, \
                                           self.tbl_mgr.get_column_from_schema(res_schema, "id"), self.debug, self.logger):
                            ok = False
        return ok


    def refresh_all_interfacevlans_info(self):
        ok = True
        link_urls = self.get_all_links_of_aggregate()
        schema = self.tbl_mgr.schema_dict["ops_interfacevlan"]
        link_ifvlan_schema = self.tbl_mgr.schema_dict["ops_link_interfacevlan"]
        for link_url in link_urls:
            link_dict = handle_request(link_url, self.cert_path, self.logger)
            if link_dict:
                if "endpoints" in link_dict:
                    for endpt in link_dict["endpoints"]:
                        ifacevlan_dict = handle_request(endpt["href"], self.cert_path, self.logger)
                        if ifacevlan_dict:
                            # before updating the ifvlan info we need to make sure the if info exists
                            if not self.check_exists("ops_interface", "selfRef", ifacevlan_dict["interface"]["href"]):
                                interface_dict = handle_request(ifacevlan_dict["interface"]["href"], self.cert_path, self.logger)
                                if not self.refresh_interface_info(interface_dict):
                                    ok = False
                            ifacevlan_info_list = self.get_interfacevlan_attributes(ifacevlan_dict, schema)
                            if not info_update(self.tbl_mgr, "ops_interfacevlan", schema, ifacevlan_info_list, \
                                               self.tbl_mgr.get_column_from_schema(schema, "id"), self.debug, self.logger):
                                ok = False
                            link_ifacevlan_info_list = [ifacevlan_dict["id"], link_dict["id"]]
                            if not info_update(self.tbl_mgr, "ops_link_interfacevlan", link_ifvlan_schema, link_ifacevlan_info_list, \
                                               self.tbl_mgr.get_column_from_schema(link_ifvlan_schema, "id"), self.debug, self.logger):
                                ok = False
        return ok


    # Updates all interfaces information
    # First queries all nodes at aggregate and looks for their interfaces
    # Then, loops through each interface in the node_dict
    def refresh_all_interfaces_info(self):
        ok = True
        node_urls = self.get_all_nodes_of_aggregate()
        nodeif_schema = self.tbl_mgr.schema_dict["ops_node_interface"]
        for node_url in node_urls:
            node_dict = handle_request(node_url, self.cert_path, self.logger)
            if node_dict:
                if "interfaces" in node_dict:
                    for interface in node_dict["interfaces"]:
                        interface_dict = handle_request(interface["href"], self.cert_path, self.logger)
                        if interface_dict:
                            if not self.refresh_interface_info(interface_dict):
                                ok = False
                            node_interface_info_list = [interface_dict["id"], node_dict["id"], interface_dict["urn"], interface_dict["selfRef"]]
                            if not info_update(self.tbl_mgr, "ops_node_interface", nodeif_schema, node_interface_info_list, \
                                               self.tbl_mgr.get_column_from_schema(nodeif_schema, "id"), self.debug, self.logger):
                                ok = False
                            ifaddr_schema = self.tbl_mgr.schema_dict["ops_interface_addresses"]
                            interface_address_list = self.get_interface_addresses(interface_dict, ifaddr_schema)
                            primary_key_columns = [self.tbl_mgr.get_column_from_schema(ifaddr_schema, "interface_id"),
                                                   self.tbl_mgr.get_column_from_schema(ifaddr_schema, "address")]
                            for address in interface_address_list:
                                if not info_update(self.tbl_mgr, "ops_interface_addresses", ifaddr_schema, address,
                                                   primary_key_columns, self.debug, self.logger):
                                    ok = False
        return ok

    def refresh_interface_info(self, interface_dict):
        """
        Method to update one interface information at a time
        :param interface_dict: the json dictionary corresponding to the interface information
        :return: True if the update went well, False otherwise.
        """
        ok = True
        schema = self.tbl_mgr.schema_dict["ops_interface"]
        interface_info_list = self.get_interface_attributes(interface_dict, schema)
        if not info_update(self.tbl_mgr, "ops_interface", schema, interface_info_list, \
                           self.tbl_mgr.get_column_from_schema(schema, "id"), self.debug, self.logger):
            ok = False
        return ok

    def get_default_attribute_for_type(self, vartype):
        val = "";
        if vartype.startswith("int"):
            val = 0
        return val

    def get_node_attributes(self, res_dict, schema):
        node_info_list = []
        for key in schema:
            if key[0].startswith("properties$"):
                jsonkey = "ops_monitoring:" + key[0].split('$')[1]
            else:
                jsonkey = key[0];

            if jsonkey in res_dict:
                node_info_list.append(res_dict[jsonkey])
            else:
                if key[2]:
                    print("WARNING: value for required json node field " + jsonkey + " is missing. Replacing with default value...")
                    node_info_list.append(self.get_default_attribute_for_type(key[1]))
                else:
                    # This is OK. This was an optional field.
                    node_info_list.append(None)

        return node_info_list


    def get_link_attributes(self, res_dict, schema):
        link_info_list = []
        for key in schema:
            if key[0] in res_dict:
                link_info_list.append(res_dict[key[0]])
            else:
                if key[2]:
                    print("WARNING: value for required json link field " + key[0] + " is missing. Replacing with default value...")
                    link_info_list.append(self.get_default_attribute_for_type(key[1]))
                else:
                    # This is OK. This was an optional field.
                    link_info_list.append(None)

        return link_info_list


    def get_sliver_attributes(self, slv_dict, schema):
        slv_info_list = []
        for key in schema:
            noval = False
            if key[0] == "aggregate_href":
                if "aggregate" in slv_dict:
                    if "href" in slv_dict["aggregate"]:
                        slv_info_list.append(slv_dict["aggregate"]["href"])
                    else:
                        noval = True
                else:
                    noval = True
                if noval:
                    if key[2]:
                        print("WARNING: value for required json sliver field [\"aggregate\"][\"href\"] is missing. Replacing with empty string...")
                        slv_info_list.append("")
                    else:
                        slv_info_list.append(None)
            elif key[0] == "aggregate_urn":
                if "aggregate" in slv_dict:
                    if "urn" in slv_dict["aggregate"]:
                        slv_info_list.append(slv_dict["aggregate"]["urn"])
                    else:
                        noval = True
                else:
                    noval = True
                if noval:
                    if key[2]:
                        print("WARNING: value for required json sliver field [\"aggregate\"][\"urn\"] is missing. Replacing with empty string...")
                        slv_info_list.append("")
                    else:
                        slv_info_list.append(None)
            elif key[0] == "node_id":
                if ("resource" in slv_dict and
                    "resource_type" in slv_dict["resource"] and
                    slv_dict["resource"]["resource_type"] == "node" and
                    "urn" in slv_dict["resource"]) :

                    node_urn = slv_dict["resource"]["urn"]
                    node_id = self.get_id_from_urn("ops_node", node_urn)
                    slv_info_list.append(node_id)
                else:
                    if key[2]:
                        print("WARNING: value for required json sliver field " + key[0] + " is missing. Replacing with default value...")
                        slv_info_list.append(self.get_default_attribute_for_type(key[1]))
                    else:
                        # This is OK. This was an optional field.
                        slv_info_list.append(None)
            elif key[0] == "link_id":
                if ("resource" in slv_dict and
                    "resource_type" in slv_dict["resource"] and
                    slv_dict["resource"]["resource_type"] == "link" and
                    "urn" in slv_dict["resource"]) :

                    link_urn = slv_dict["resource"]["urn"]
                    link_id = self.get_id_from_urn("ops_link", link_urn)
                    slv_info_list.append(link_id)
                else:
                    if key[2]:
                        print("WARNING: value for required json sliver field " + key[0] + " is missing. Replacing with default value...")
                        slv_info_list.append(self.get_default_attribute_for_type(key[1]))
                    else:
                        # This is OK. This was an optional field.
                        slv_info_list.append(None)
            else:
                if key[0] in slv_dict:
                    slv_info_list.append(slv_dict[key[0]])
                else:
                    if key[2]:
                        print("WARNING: value for required json sliver field " + key[0] + " is missing. Replacing with default value...")
                        slv_info_list.append(self.get_default_attribute_for_type(key[1]))
                    else:
                        # This is OK. This was an optional field.
                        slv_info_list.append(None)

        return slv_info_list


    def get_interfacevlan_attributes(self, ifv_dict, schema):
        ifv_info_list = []
        for key in schema:
            noval = False
            if key[0] == "interface_href":
                if "interface" in ifv_dict:
                    if "href" in ifv_dict["interface"]:
                        ifv_info_list.append(ifv_dict["interface"]["href"])
                    else:
                        noval = True
                else:
                    noval = True
                if noval:
                    if key[2]:
                        print("WARNING: value for required json interface-vlan field [\"interface\"][\"href\"] is missing. Replacing with empty string...")
                        ifv_info_list.append("")
                    else:
                        ifv_info_list.append(None)
            elif key[0] == "interface_urn":
                if "interface" in ifv_dict:
                    if "urn" in ifv_dict["interface"]:
                        ifv_info_list.append(ifv_dict["interface"]["urn"])
                    else:
                        noval = True
                else:
                    noval = True
                if noval:
                    if key[2]:
                        print("WARNING: value for required json interface-vlan field [\"interface\"][\"urn\"] is missing. Replacing with empty string...")
                        ifv_info_list.append("")
                    else:
                        ifv_info_list.append(None)
            else:
                if key[0] in ifv_dict:
                    ifv_info_list.append(ifv_dict[key[0]])
                else:
                    if key[2]:
                        print("WARNING: value for required json interface-vlan field " + key[0] + " is missing. Replacing with default value...")
                        ifv_info_list.append(self.get_default_attribute_for_type(key[1]))
                    else:
                        # This is OK. This was an optional field.
                        ifv_info_list.append(None)

        return ifv_info_list


    def get_interface_attributes(self, interface_dict, schema):
        # get each attribute out of response into list
        interface_info_list = []
        for key in schema:
            if key[0].startswith("properties$"):
                jsonkey = "ops_monitoring:" + key[0].split('$')[1]
            else:
                jsonkey = key[0]
            if jsonkey in interface_dict:
                interface_info_list.append(interface_dict[jsonkey])
            else:
                if key[2]:
                    print("WARNING: value for required json interface field " + jsonkey + " is missing. Replacing with default value...")
                    interface_info_list.append(self.get_default_attribute_for_type(key[1]))
                else:
                    # This is OK. This was an optional field.
                    interface_info_list.append(None)

        return interface_info_list


    def get_experiment_attributes(self, experiment_dict, schema):
        """
        """
        # get each attribute out of response into list
        experiment_info_list = []
        for key in schema:
            if key[0] in experiment_dict:
                experiment_info_list.append(experiment_dict[key[0]])
            else:
                if key[2]:
                    print("WARNING: value for required json interface field " + key[0] + " is missing. Replacing with default value...")
                    experiment_info_list.append(self.get_default_attribute_for_type(key[1]))
                else:
                    # This is OK. This was an optional field.
                    experiment_info_list.append(None)

        return experiment_info_list


    def get_interface_addresses(self, interface_dict, schema):
        """
        Extract addresses from an interface dictionary.
        :param interface_dict: the interface to extract addresses from
        :param schema: database schema for the ops_interface_addresses table
        :return: a list of lists, where each of the inner lists contains
                 a row of values representing one address
        """
        address_list = []
        if "addresses" in interface_dict:
            for json_address in interface_dict["addresses"]:
                oneaddr_row = []
                for key in schema:
                    jsonkey = key[0]
                    if jsonkey == "interface_id":
                        oneaddr_row.append(interface_dict["id"])
                    elif jsonkey in json_address:
                        oneaddr_row.append(json_address[jsonkey])
                    else:
                        if key[2]:
                            print("WARNING: value for required json interface field " + jsonkey + " is missing. Replacing with default value...")
                            oneaddr_row.append(self.get_default_attribute_for_type(key[1]))
                        else:
                            # This is OK. This was an optional field.
                            oneaddr_row.append(None)
                if len(oneaddr_row) > 0:
                    address_list.append(oneaddr_row)

        return address_list


    def get_all_nodes_of_aggregate(self):
        tbl_mgr = self.tbl_mgr
        aggregate_id = self.aggregate_id

        q_res = tbl_mgr.query("select " + tbl_mgr.get_column_name("selfRef") + " from ops_node where id in (select id from ops_aggregate_resource where aggregate_id = '" + aggregate_id + "')")
        res = [];
        if q_res is not None:
            for res_i in range(len(q_res)):
                res.append(q_res[res_i][0])  # gets first of single tuple

        return res


    def get_all_interfaces_of_aggregate(self):
        tbl_mgr = self.tbl_mgr
        aggregate_id = self.aggregate_id

        q_res = tbl_mgr.query("select id from ops_node_interface where node_id in (select id from ops_node where id in (select id from ops_aggregate_resource where aggregate_id = '" + aggregate_id + "'))")
        res = [];
        if q_res is not None:
            for res_i in range(len(q_res)):
                res.append(q_res[res_i][0])  # gets first of single tuple

        return res


    def get_all_links_of_aggregate(self):
        tbl_mgr = self.tbl_mgr
        aggregate_id = self.aggregate_id

        q_res = tbl_mgr.query("select " + tbl_mgr.get_column_name("selfRef") + " from ops_link where id in (select id from ops_aggregate_resource where aggregate_id = '" + aggregate_id + "')")
        res = [];
        if q_res is not None:
            for res_i in range(len(q_res)):
                res.append(q_res[res_i][0])  # gets first of single tuple

        return res

    def get_meas_ref(self):
        tbl_mgr = self.tbl_mgr
        object_id = self.aggregate_id
        meas_ref = None

        q_res = tbl_mgr.query("select " + tbl_mgr.get_column_name("measRef") + " from ops_aggregate where id = '" + object_id + "' limit 1")
        if q_res is not None:
            meas_ref = q_res[0][0]  # gets first of single tuple

        return meas_ref

    def check_exists(self, table_name, fieldname, value):
        """
        Method to check if data exists in a given table that has a certain value for a given field name.
        :param table_name: the name of the table
        :param fieldname: the name of the field
        :param value: the value for the field
        :return: True if such data exists, False otherwise.
        """
        exists = False
        if value is None:
            valuestr = "NULL"
        else:
            valuestr = "'" + value + "'"
        q_res = self.tbl_mgr.query("select " + self.tbl_mgr.get_column_name(fieldname) + " from " + table_name + " where " \
                                   + self.tbl_mgr.get_column_name(fieldname) + " = " + valuestr + " limit 1")
        if q_res is not None:
            if len(q_res) > 0:
                exists = True
        return exists


    def get_id_from_urn(self, table_name, urn):
        """
        Given a urn and a table name, find its id.

        :param table_name: database table name to search
        :param urn: urn to look for
        :return: the id that goes with urn, or None if not found
        """
        tbl_mgr = self.tbl_mgr
        objid = None

        q_res = tbl_mgr.query("select " + tbl_mgr.get_column_name("id") +
                              " from " + table_name + " where urn = '" + urn +
                              "' limit 1")
        if q_res is not None:
            objid = q_res[0][0]  # gets first of single tuple

        return objid


def handle_request(url, cert_path, logger):

    resp = None

    try:
        resp = requests.get(url, verify=False, cert=cert_path)
    except requests.exceptions.RequestException, e:
        logger.warning("No response from local datastore at: " + url)
        logger.warning(e)

    if resp:
        if (resp.status_code == requests.codes.ok):
            try:
                json_dict = json.loads(resp.content)
                return json_dict
            except ValueError, e:
                logger.warning("Could not load into JSON with response from " + url)
                logger.warning("response = \n" + resp.content)
                logger.warning(e)
        else:
            logger.warning("Response from " + url + " is invalid, code = " + str(resp.status_code))

    return None


def info_update(tbl_mgr, table_str, table_schema, row_arr, id_columns, debug, logger):
    """
    Function to update the information about an object.
    :param tbl_mgr: an instance of TableManager that will be used to execute the SQL statements.
    :param table_str: the name of the table to operate on.
    :param obj_id: the id of the object
    :param row_arr: a list of values for the object to be updated with.
    :param debug: boolean to decide whether to truly update the information (False) or
        just print statements of what would be executed (True)
    :param logger: the logger instance.
    :return: True if the update happened with any issue, False otherwise.
    """
    ok = True
    if debug:
        # Convert id_columns to a list if it is not one already.
        try:
            _ = iter(id_columns)  # attempt to access it as an iterable
        except TypeError:
            id_columns = [id_columns]

        # Create a list of NAME=VALUE, for all of the id_columns
        name_value_pairs = ""
        for col in id_columns:
            name_value_pairs += table_schema[col][0] + "=" + str(row_arr[col]) + ", "
        logger.info("<print only> updating or inserting " + name_value_pairs + "in table " + table_str)
    else:
        if not tbl_mgr.upsert(table_str, table_schema, row_arr, id_columns):
            ok = False

    return ok


def main(argv):
    ok = True
    [info_url, aggregate_id, extck_id, objecttypes, cert_path, debug] = parse_args(argv)

    if info_url == "" or cert_path == "" or (extck_id == "" and aggregate_id == ""):
        usage()

    db_type = "collector"
    config_path = "../config/"
    # If in debug mode, make sure to overwrite the logging configuration to print out what we want,
    if debug:
        logger.configure_logger_for_debug_info(config_path)


    tbl_mgr = table_manager.TableManager(db_type, config_path)
    tbl_mgr.poll_config_store()
    crawler = SingleLocalDatastoreInfoCrawler(tbl_mgr, info_url, aggregate_id, extck_id, cert_path, debug, config_path)

    # Only do head aggregate info query if nodes, sliver, interface, vlan objects are in objecttypes
    if 'n' in objecttypes or 'l' in objecttypes or 's' in objecttypes or 'v' in objecttypes or 'i' in objecttypes:
        if not crawler.refresh_aggregate_info():
            ok = False

    if 'x' in objecttypes or 'e' in objecttypes:
        if not crawler.refresh_externalcheck_info():
            ok = False

    # depending on what is in the objecttypes string, get other object
    # info.  Order of these should stay as is (v after l, i after n).
    if 'n' in objecttypes:
        if not crawler.refresh_all_nodes_info():
            ok = False
    if 'l' in objecttypes:
        if not crawler.refresh_all_links_info():
            ok = False
    if 's' in objecttypes:
        if not crawler.refresh_all_slivers_info():
            ok = False
    if 'i' in objecttypes:
        if not crawler.refresh_all_interfaces_info():
            ok = False
    if 'v' in objecttypes:
        if not crawler.refresh_all_interfacevlans_info():
            ok = False
    if 'e' in objecttypes:
        if not crawler.refresh_all_monitoredaggregates_info():
            ok = False
    if 'x' in objecttypes:
        if not crawler.refresh_all_experiments_info():
            ok = False
    if not ok:
        sys.stderr.write("Error while crawling data store...\n")
        sys.exit(-1)

if __name__ == "__main__":
    main(sys.argv[1:])

