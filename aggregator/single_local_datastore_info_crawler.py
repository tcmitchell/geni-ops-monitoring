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
from pprint import pprint

common_path = "../common/"
sys.path.append(common_path)
import table_manager

# agg is for aggregator 
# aggregate is for aggregate manager 

# am_urls is a list of dictionaies with hrefs to reach the datastore of
# the am urn

# This program populates the aggregator database on every fetch

def usage():
    print('single_local_datastore_info_crawler.py -b <local-store-info-base-url> -a <aggregate-id> -o <objecttypess-of-interest (ex: -o nislv gets info on nodes, interfaces, slivers, links, vlans)>')
    sys.exit(1)

def parse_args(argv):
    if argv == []:
        usage()

    base_url = ""
    aggregate_id = ""
    objecttypes = ""

    try:
        opts, args = getopt.getopt(argv,"hb:a:o:",["baseurl=","aggregateid=","object-types="])
    except getopt.GetoptError:
        usage()

    for opt, arg in opts:
        if opt == '-h':
            usage()
        elif opt in ("-b", "--baseurl"):
            base_url = arg
        elif opt in ("-a", "--aggregateid"):
            aggregate_id = arg
        elif opt in ("-o", "--object-types"):
            objecttypes = arg
        else:
            usage()

    return [base_url, aggregate_id, objecttypes]

class SingleLocalDatastoreInfoCrawler:
    
    def __init__(self, tbl_mgr, info_url, aggregate_id):
        self.tbl_mgr = tbl_mgr
        self.tbl_mgr.establish_all_tables()

        if info_url[-1] == '/':
            info_url = info_url[:-1]
        self.info_url = info_url
        self.aggregate_id = aggregate_id

    # Updates head aggregate information
    def refresh_aggregate_info(self):
        
        am_dict = handle_request(self.info_url + '/aggregate/' + self.aggregate_id)            
        if am_dict:
            self.tbl_mgr.establish_table("ops_aggregate")
            schema = self.tbl_mgr.schema_dict["ops_aggregate"]
            am_info_list = []
            for key in schema:
                am_info_list.append(am_dict[key[0]])
            info_update(self.tbl_mgr, "ops_aggregate", am_dict["id"], am_info_list)


    # Updates all nodes information
    def refresh_all_links_info(self):

        am_dict = handle_request(self.info_url + '/aggregate/' + self.aggregate_id)
        if am_dict:
            schema = self.tbl_mgr.schema_dict["ops_link"]

            for res_i in am_dict["resources"]:
                res_dict = handle_request(res_i["href"])
                if res_dict["$schema"].endswith("link#"): # if a link
                    
                    # get each attribute out of response into list
                    link_info_list = self.get_link_attributes(res_dict, schema)
                    info_update(self.tbl_mgr, "ops_link", res_dict["id"], link_info_list) 
                agg_res_info_list = [res_dict["id"], am_dict["id"], res_dict["urn"], res_dict["selfRef"]]
                info_update(self.tbl_mgr, "ops_aggregate_resource", res_dict["id"], agg_res_info_list)
        

    def refresh_all_slivers_info(self):

        am_dict = handle_request(self.info_url + '/aggregate/' + self.aggregate_id)
        if am_dict:
            schema = self.tbl_mgr.schema_dict["ops_sliver"]

            for slv_i in am_dict["slivers"]:
                slv_dict = handle_request(slv_i["href"])
                
                # get each attribute out of response into list
                slv_info_list = self.get_sliver_attributes(slv_dict, schema)
                info_update(self.tbl_mgr, "ops_sliver", slv_dict["id"], slv_info_list) 
                agg_slv_info_list = [slv_dict["id"], am_dict["id"], slv_dict["urn"], slv_dict["selfRef"]]
                info_update(self.tbl_mgr, "ops_aggregate_sliver", slv_dict["id"], agg_slv_info_list)


    def refresh_all_nodes_info(self):
        am_dict = handle_request(self.info_url + '/aggregate/' + self.aggregate_id)
        if am_dict:
            schema = self.tbl_mgr.schema_dict["ops_node"]

            for res_i in am_dict["resources"]:
                res_dict = handle_request(res_i["href"])
                if res_dict["$schema"].endswith("node#"): # if a node
                    
                    # get each attribute out of response into list
                    node_info_list = self.get_node_attributes(res_dict, schema)
                    info_update(self.tbl_mgr, "ops_node", res_dict["id"], node_info_list) 
                agg_res_info_list = [res_dict["id"], am_dict["id"], res_dict["urn"], res_dict["selfRef"]]
                info_update(self.tbl_mgr, "ops_aggregate_resource", res_dict["id"], agg_res_info_list)


    def refresh_all_interfacevlans_info(self):

        link_ids = self.get_all_links_of_aggregate()
        schema = self.tbl_mgr.schema_dict["ops_interfacevlan"]
        for link_id in link_ids:
            link_dict = handle_request(self.info_url + '/link/' + link_id)
            if "endpoints" in link_dict:
                for endpt in link_dict["endpoints"]:
                    ifacevlan_dict = handle_request(endpt["href"])
                    ifacevlan_info_list = self.get_interfacevlan_attributes(ifacevlan_dict, schema)
                    info_update(self.tbl_mgr, "ops_interfacevlan", ifacevlan_dict["id"], ifacevlan_info_list) 
                    link_ifacevlan_info_list = [ifacevlan_dict["id"], link_dict["id"], ifacevlan_dict["urn"], ifacevlan_dict["selfRef"]]
                    info_update(self.tbl_mgr, "ops_link_interfacevlan", ifacevlan_dict["id"], link_ifacevlan_info_list)
        


    # Updates all interfaces information
    # First queries all nodes at aggregate and looks for their ports
    # Then, loops through each port in the node_dict
    def refresh_all_interfaces_info(self):

         node_ids = self.get_all_nodes_of_aggregate()
         schema = self.tbl_mgr.schema_dict["ops_interface"]
         for node_id in node_ids:
             node_dict = handle_request(self.info_url + '/node/' + node_id)
             if "ports" in node_dict:
                 for port in node_dict["ports"]:
                     interface_dict = handle_request(port["href"])
                     interface_info_list = self.get_interface_attributes(interface_dict, schema)
                     info_update(self.tbl_mgr, "ops_interface", interface_dict["id"], interface_info_list) 
                     node_interface_info_list = [interface_dict["id"], node_dict["id"], interface_dict["urn"], interface_dict["selfRef"]]
                     info_update(self.tbl_mgr, "ops_node_interface", interface_dict["id"], node_interface_info_list)


    def get_node_attributes(self, res_dict, schema):
        node_info_list = []
        for key in schema: 
            # ugly parsing of properties dictionary and schema
            if key[0].startswith("properties$"): 
                if "ops_monitoring" in res_dict["properties"]:
                    if key[0].split('$')[1] in res_dict["properties"]["ops_monitoring"]:
                        node_info_list.append(res_dict["properties"]["ops_monitoring"][key[0].split('$')[1]])
            else:
                node_info_list.append(res_dict[key[0]])

        return node_info_list


    def get_link_attributes(self, res_dict, schema):
        link_info_list = []
        for key in schema: 
            link_info_list.append(res_dict[key[0]])
        return link_info_list


    def get_sliver_attributes(self, slv_dict, schema):
        slv_info_list = []
        for key in schema: 
            if key[0] == "aggregate_href":
                slv_info_list.append(slv_dict["aggregate"]["href"])
            elif key[0] == "aggregate_urn":
                slv_info_list.append(slv_dict["aggregate"]["urn"])
            else:
                slv_info_list.append(slv_dict[key[0]])
        return slv_info_list


    def get_interfacevlan_attributes(self, ifv_dict, schema):
        ifv_info_list = []
        for key in schema: 
            if key[0] == "interface_href":
                ifv_info_list.append(ifv_dict["port"]["href"])
            elif key[0] == "interface_urn":
                ifv_info_list.append(ifv_dict["port"]["urn"])
            else:
                ifv_info_list.append(ifv_dict[key[0]])
        return ifv_info_list


    def get_interface_attributes(self, interface_dict, schema):
        # get each attribute out of response into list
        interface_info_list = []
        for key in schema: 
            # ugly parsing of properties dictionary and schema
            if key[0].startswith("properties$"): 
                if "ops_monitoring" in interface_dict["properties"]:
                    if key[0].split('$')[1] in interface_dict["properties"]["ops_monitoring"]:
                        interface_info_list.append(interface_dict["properties"]["ops_monitoring"][key[0].split('$')[1]])
                        
            elif key[0] == "address_type":
                interface_info_list.append(interface_dict["address"]["type"])
            elif key[0] == "address_address":
                interface_info_list.append(interface_dict["address"]["address"])
            else:
                interface_info_list.append(interface_dict[key[0]])

        return interface_info_list


    def get_all_nodes_of_aggregate(self):
        tbl_mgr = self.tbl_mgr
        aggregate_id = self.aggregate_id

        cur = tbl_mgr.con.cursor()
        res = [];
        tbl_mgr.db_lock.acquire()
        try:
            cur.execute("select id from ops_node where id in (select id from ops_aggregate_resource where aggregate_id = '" + aggregate_id + "');")
            q_res = cur.fetchall()

            tbl_mgr.con.commit()
            for res_i in range(len(q_res)):
                res.append(q_res[res_i][0]) # gets first of single tuple
            
        except Exception, e:
            print e
            tbl_mgr.con.commit()
        
        cur.close()
        tbl_mgr.db_lock.release()
        
        return res


    def get_all_interfaces_of_aggregate(self):
        tbl_mgr = self.tbl_mgr
        aggregate_id = self.aggregate_id

        cur = tbl_mgr.con.cursor()
        res = [];
        tbl_mgr.db_lock.acquire()
        try:
            cur.execute("select id from ops_node_interface where node_id in (select id from ops_node where id in (select id from ops_aggregate_resource where aggregate_id = '" + aggregate_id + "'));")

            q_res = cur.fetchall()
            tbl_mgr.con.commit()
            for res_i in range(len(q_res)):
                res.append(q_res[res_i][0]) # gets first of single tuple
            
        except Exception, e:
            print e
            tbl_mgr.con.commit()
        
        cur.close()
        tbl_mgr.db_lock.release()
        
        return res


    def get_all_links_of_aggregate(self):
        tbl_mgr = self.tbl_mgr
        aggregate_id = self.aggregate_id

        cur = tbl_mgr.con.cursor()
        res = [];
        tbl_mgr.db_lock.acquire()
        try:
            cur.execute("select id from ops_link where id in (select id from ops_aggregate_resource where aggregate_id = '" + aggregate_id + "');")
            q_res = cur.fetchall()
            
            tbl_mgr.con.commit()
            for res_i in range(len(q_res)):
                res.append(q_res[res_i][0]) # gets first of single tuple
            
        except Exception, e:
            print e
            tbl_mgr.con.commit()
        
        cur.close()
        tbl_mgr.db_lock.release()
        
        return res

    def get_meas_ref(self):
        tbl_mgr = self.tbl_mgr
        object_id = self.aggregate_id
        cur = tbl_mgr.con.cursor()
        res = []
        meas_ref = None
        tbl_mgr.db_lock.acquire()
        try:

            # two queries avoids regex split with ,
            if tbl_mgr.database_program == "postgres":
                cur.execute("select \"measRef\" from ops_aggregate where id = '" + object_id + "' limit 1")
            elif tbl_mgr.database_program == "mysql":
                cur.execute("select measRef from ops_aggregate where id = '" + object_id + "' limit 1")
            q_res = cur.fetchone()
            tbl_mgr.con.commit()
            if q_res is not None:
                meas_ref = q_res[0] # gets first of single tuple
            
        except Exception, e:
            print e
            tbl_mgr.con.commit()
        
        cur.close()
        tbl_mgr.db_lock.release()
        
        return meas_ref


def handle_request(url):

    resp = None

    try:
        resp = requests.get(url)
    except Exception, e:
        print "No response from local datastore at: " + url
        print e
        return None

    if resp:
        try:
            json_dict = json.loads(resp.content)
        except Exception, e:
            print "Could not load into JSON"
            print e
            return None

        return json_dict
    else:
        return None


def info_update(tbl_mgr, table_str, obj_id, row_arr):
    tbl_mgr.delete_stmt(table_str, obj_id)
    val_str = "('"
    for val in row_arr:
        val_str += str(val) + "','" # join won't do this
    val_str = val_str[:-2] + ")" # remove last 2 of 3: ',' add )
    tbl_mgr.insert_stmt(table_str, val_str)


def main(argv): 

    [info_url, aggregate_id, objecttypes] = parse_args(argv)

    if info_url == "" or aggregate_id == "":
        usage()

    db_type = "aggregator"
    config_path = "../config/"
    info_schema = json.load(open("../config/info_schema"))

    tbl_mgr = table_manager.TableManager(db_type, config_path)
    crawler = SingleLocalDatastoreInfoCrawler(tbl_mgr, info_url, aggregate_id)

    # ensures tables exist in database
    tbl_mgr.establish_tables(info_schema.keys())

    # Always do the head aggregate info query
    crawler.refresh_aggregate_info()

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


if __name__ == "__main__":
    main(sys.argv[1:])

