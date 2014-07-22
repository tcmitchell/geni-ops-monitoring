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
import opsconfig_loader
import logger

# am_urls is a list of dictionaies with hrefs to reach the datastore of
# the am urn

# This program populates the collector database on every fetch

def usage():
    print('single_local_datastore_info_crawler.py -d -b <local-store-info-base-url> -a <aggregate-id> -e <extck-id> -c </cert/path/cert.pem> -o <objecttypes-of-interest (ex: -o nislv gets info on nodes, interfaces, slivers, links, vlans or -o xe for eXperiments, Externalchecks)>')
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
        self.tbl_mgr.establish_all_tables()

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
        if self.am_dict:
            self.tbl_mgr.establish_table("ops_aggregate")
            schema = self.tbl_mgr.schema_dict["ops_aggregate"]
            am_info_list = []
            for key in schema:
                am_info_list.append(self.am_dict[key[0]])
            info_update(self.tbl_mgr, "ops_aggregate", self.am_dict["id"], am_info_list, self.debug, self.logger)

    # Updates externalcheck information
    def refresh_externalcheck_info(self):

        self.extck_dict = handle_request(self.info_url + '/externalcheck/' + self.extck_id, self.cert_path, self.logger)
        if self.extck_dict:
            self.tbl_mgr.establish_table("ops_externalcheck")
            schema = self.tbl_mgr.schema_dict["ops_externalcheck"]
            extck_info_list = []
            for key in schema:
                extck_info_list.append(self.extck_dict[key[0]])
            info_update(self.tbl_mgr, "ops_externalcheck", self.extck_dict["id"], extck_info_list, self.debug, self.logger)

    # Updates all the monitored aggregates
    def refresh_all_monitoredaggregates_info(self):

        if self.extck_dict:
            self.tbl_mgr.establish_table("ops_externalcheck_monitoredaggregate")
#             schema = self.tbl_mgr.schema_dict["ops_externalcheck_monitoredaggregate"]
#             mon_aggs = []
            for mon_agg in self.extck_dict["monitored_aggregates"]:
                mon_agg_info = [mon_agg["id"], self.extck_dict["id"], mon_agg["href"]]
                info_update(self.tbl_mgr, "ops_externalcheck_monitoredaggregate", mon_agg["id"], mon_agg_info, self.debug, self.logger)

    # Updates all nodes information
    def refresh_all_links_info(self):

        if self.am_dict:
            schema = self.tbl_mgr.schema_dict["ops_link"]
            # Need to check because "resources" is optional
            if "resources" in self.am_dict:
                for res_i in self.am_dict["resources"]:
                    res_dict = handle_request(res_i["href"], self.cert_path, self.logger)
                    if res_dict:
                        if res_dict["$schema"].endswith("link#"):  # if a link
                            # get each attribute out of response into list
                            link_info_list = self.get_link_attributes(res_dict, schema)
                            info_update(self.tbl_mgr, "ops_link", res_dict["id"], link_info_list, self.debug, self.logger)
                        agg_res_info_list = [res_dict["id"], self.am_dict["id"], res_dict["urn"], res_dict["selfRef"]]
                        info_update(self.tbl_mgr, "ops_aggregate_resource", res_dict["id"], agg_res_info_list, self.debug, self.logger)


    def refresh_all_slivers_info(self):

        if self.am_dict:
            schema = self.tbl_mgr.schema_dict["ops_sliver"]
            # Need to check because "slivers" is optional
            if "slivers" in self.am_dict:
                for slv_i in self.am_dict["slivers"]:
                    slv_dict = handle_request(slv_i["href"], self.cert_path, self.logger)
                    if slv_dict:
                        # get each attribute out of response into list
                        slv_info_list = self.get_sliver_attributes(slv_dict, schema)
                        info_update(self.tbl_mgr, "ops_sliver", slv_dict["id"], slv_info_list, self.debug, self.logger)
                        agg_slv_info_list = [slv_dict["id"], self.am_dict["id"], slv_dict["urn"], slv_dict["selfRef"]]
                        info_update(self.tbl_mgr, "ops_aggregate_sliver", slv_dict["id"], agg_slv_info_list, self.debug, self.logger)


    def refresh_all_nodes_info(self):

        if self.am_dict:
            schema = self.tbl_mgr.schema_dict["ops_node"]
            # Need to check because "resources" is optional
            if "resources" in self.am_dict:
                for res_i in self.am_dict["resources"]:
                    res_dict = handle_request(res_i["href"], self.cert_path, self.logger)
                    if res_dict:
                        if res_dict["$schema"].endswith("node#"):  # if a node
                            # get each attribute out of response into list
                            node_info_list = self.get_node_attributes(res_dict, schema)
                            info_update(self.tbl_mgr, "ops_node", res_dict["id"], node_info_list, self.debug, self.logger)
                        agg_res_info_list = [res_dict["id"], self.am_dict["id"], res_dict["urn"], res_dict["selfRef"]]
                        info_update(self.tbl_mgr, "ops_aggregate_resource", res_dict["id"], agg_res_info_list, self.debug, self.logger)


    def refresh_all_interfacevlans_info(self):

        link_urls = self.get_all_links_of_aggregate()
        schema = self.tbl_mgr.schema_dict["ops_interfacevlan"]
        for link_url in link_urls:
            link_dict = handle_request(link_url, self.cert_path, self.logger)
            if link_dict:
                if "endpoints" in link_dict:
                    for endpt in link_dict["endpoints"]:
                        ifacevlan_dict = handle_request(endpt["href"], self.cert_path, self.logger)
                        if ifacevlan_dict:
                            ifacevlan_info_list = self.get_interfacevlan_attributes(ifacevlan_dict, schema)
                            info_update(self.tbl_mgr, "ops_interfacevlan", ifacevlan_dict["id"], ifacevlan_info_list, self.debug, self.logger)
                            link_ifacevlan_info_list = [ifacevlan_dict["id"], link_dict["id"], ifacevlan_dict["urn"], ifacevlan_dict["selfRef"]]
                            info_update(self.tbl_mgr, "ops_link_interfacevlan", ifacevlan_dict["id"], link_ifacevlan_info_list, self.debug, self.logger)



    # Updates all interfaces information
    # First queries all nodes at aggregate and looks for their ports
    # Then, loops through each port in the node_dict
    def refresh_all_interfaces_info(self):

        node_urls = self.get_all_nodes_of_aggregate()
        schema = self.tbl_mgr.schema_dict["ops_interface"]
        for node_url in node_urls:
            node_dict = handle_request(node_url, self.cert_path, self.logger)
            if node_dict:
                if "ports" in node_dict:
                    for port in node_dict["ports"]:
                        interface_dict = handle_request(port["href"], self.cert_path, self.logger)
                        if interface_dict:
                            interface_info_list = self.get_interface_attributes(interface_dict, schema)
                            info_update(self.tbl_mgr, "ops_interface", interface_dict["id"], interface_info_list, self.debug, self.logger)
                            node_interface_info_list = [interface_dict["id"], node_dict["id"], interface_dict["urn"], interface_dict["selfRef"]]
                            info_update(self.tbl_mgr, "ops_node_interface", interface_dict["id"], node_interface_info_list, self.debug, self.logger)

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
                        print("WARNING: value for required json sliver field [\"aggregate\"][\"href\"] is missing. Replacing with empty string...")
                        slv_info_list.append("")
                    else:
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
                if "port" in ifv_dict:
                    if "href" in ifv_dict["port"]:
                        ifv_info_list.append(ifv_dict["port"]["href"])
                    else:
                        noval = True
                else:
                    noval = True
                if noval:
                    if key[2]:
                        print("WARNING: value for required json interface-vlan field [\"port\"][\"href\"] is missing. Replacing with empty string...")
                        ifv_info_list.append("")
                    else:
                        ifv_info_list.append(None)
            elif key[0] == "interface_urn":
                if "port" in ifv_dict:
                    if "urn" in ifv_dict["port"]:
                        ifv_info_list.append(ifv_dict["port"]["urn"])
                    else:
                        noval = True
                else:
                    noval = True
                if noval:
                    if key[2]:
                        print("WARNING: value for required json interface-vlan field [\"port\"][\"urn\"] is missing. Replacing with empty string...")
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
            noval = False
            if key[0] == "address_type":
                if "address" in interface_dict:
                    if "type" in interface_dict["address"]:
                        interface_info_list.append(interface_dict["address"]["type"])
                    else:
                        noval = True
                else:
                    noval = True
                if noval:
                    if key[2]:
                        print("WARNING: value for required json interface field [\"address\"][\"type\"] is missing. Replacing with empty string...")
                        interface_info_list.append("")
                    else:
                        interface_info_list.append(None)

            elif key[0] == "address_address":
                if "address" in interface_dict:
                    if "address" in interface_dict["address"]:
                        interface_info_list.append(interface_dict["address"]["address"])
                    else:
                        noval = True
                else:
                    noval = True
                if noval:
                    if key[2]:
                        print("WARNING: value for required json interface field [\"address\"][\"address\"] is missing. Replacing with empty string...")
                        interface_info_list.append("")
                    else:
                        interface_info_list.append(None)
            else:
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


def info_update(tbl_mgr, table_str, obj_id, row_arr, debug, logger):
    if debug:
        logger.info("<print only> delete " + obj_id + " from " + table_str)
    else:
        tbl_mgr.delete_stmt(table_str, obj_id)

    val_str = "("
    for val in row_arr:
        if val is None:
            val_str += "NULL, "
        else:
            val_str += "'" + str(val) + "', "  # join won't do this
    val_str = val_str[:-2] + ")"  # remove last 2 of 3: ', ' add ')'

    if debug:
        logger.info("<print only> insert " + table_str + " values: " + val_str)
    else:
        tbl_mgr.insert_stmt(table_str, val_str)


def main(argv):

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

    ocl = opsconfig_loader.OpsconfigLoader(config_path)
    info_schema = ocl.get_info_schema()

    # ensures tables exist in database
    tbl_mgr.establish_tables(info_schema.keys())

    # Only do head aggregate info query if nodes, sliver, interface, vlan objects are in objecttypes
    if 'n' in objecttypes or 'l' in objecttypes or 's' in objecttypes or 'v' in objecttypes or 'i' in objecttypes:
        crawler.refresh_aggregate_info()

    if 'x' in objecttypes or 'e' in objecttypes:
        crawler.refresh_externalcheck_info()

    # depending on what is in the objecttypes string, get other object
    # info.  Order of these should stay as is (v after l, i after n).
    if 'n' in objecttypes:
        crawler.refresh_all_nodes_info()
    if 'l' in objecttypes:
        crawler.refresh_all_links_info()
    if 's' in objecttypes:
        crawler.refresh_all_slivers_info()
    if 'i' in objecttypes:
        crawler.refresh_all_interfaces_info()
    if 'v' in objecttypes:
        crawler.refresh_all_interfacevlans_info()
    if 'e' in objecttypes:
        crawler.refresh_all_monitoredaggregates_info()
    if 'x' in objecttypes:
        crawler.refresh_all_experiments_info()

if __name__ == "__main__":
    main(sys.argv[1:])

