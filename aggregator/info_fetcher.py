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
import psycopg2
import sys
import requests
from pprint import pprint

common_path = "../common/"
sys.path.append(common_path)
import table_manager

# agg is for aggregator 
# aggregate is for aggregate manager 

# am_urls is a list of dictionaies with hrefs to reach the datastore of
# the am urn

# This program populates an "aggregator atlas" and sends the data to
# database tables.  The data_fetcher uses this to fetch tsdata about
# objects.  The aggregator apps (i.e., nagios) queries the tables
# for object existence instead of having an InfoFetcher instance.

class InfoFetcher:
    
    def __init__(self, tbl_mgr, am_urls_urns):
        self.tbl_mgr = tbl_mgr
        self.agg_atlas = {}
        self.agg_atlas["href"] = {}
        self.agg_atlas["href"]["aggregate"] = {}
        self.agg_atlas["href"]["resource"] = {}
        self.agg_atlas["href"]["node"] = {}
        self.agg_atlas["href"]["sliver"] = {}
        self.agg_atlas["href"]["interface"] = {}
        for am_i in am_urls_urns:
            self.agg_atlas["href"]["aggregate"][am_i["urn"]] = am_i["href"]
    
        self.agg_atlas["aggregate"] = []
        self.agg_atlas["sliver"]  = []        
        self.agg_atlas["node"]  = []        
        self.agg_atlas["interface"]  = []
        self.agg_atlas["aggregate_resource"] = {}
        self.agg_atlas["aggregate_sliver"] = {}
        self.agg_atlas["node_interface"] = {}


    # Get info about all aggregates with hrefs in the agg_atlas
    def poll_aggregate_info(self):
        self.agg_atlas["aggregate"] = []
        for am_urn in self.agg_atlas["href"]["aggregate"]:
            resp = requests.get(self.agg_atlas["href"]["aggregate"][am_urn])
            am_dict = json.loads(resp.content)
            am_i = {}
            for key in am_dict:
                if key == "resources":
                    for res_i in am_dict[key]:
                        self.agg_atlas["href"]["resource"][res_i["urn"]] = res_i["href"]                        
                elif key == "slivers":
                    for res_i in am_dict[key]:
                        self.agg_atlas["href"]["sliver"][res_i["urn"]] = res_i["href"]
                else:
                    am_i[key] = am_dict[key]
            self.agg_atlas["aggregate"].append(am_i)

    # Gets aggregate to resource mapping indepently of other polls
    def poll_aggregate_resource_info(self):
        self.agg_atlas["aggregate_resource"] = []
        for am_urn in self.agg_atlas["href"]["aggregate"]:
            resp = requests.get(self.agg_atlas["href"]["aggregate"][am_urn])
            am_dict = json.loads(resp.content)
            am_id = am_dict["id"]
            resources = am_dict["resources"]
            for res_i in resources:
                res_i_self_ref = res_i["href"]
                res_i_urn = res_i["urn"]
                
                # get resource id
                resp = requests.get(res_i_self_ref)
                res_i_dict = json.loads(resp.content)
                res_i_id = res_i_dict["id"]
                
                # temporary variables for readbility
                agg_res_list = [res_i_id, am_id, res_i_urn, res_i_self_ref];
                agg_res_dict = {"id":res_i_id, "aggregate_id":am_id, "urn":res_i_urn, "selfRef":res_i_self_ref}          
                
                # append to atlas
                self.agg_atlas["aggregate_resource"].append(agg_res_dict)
                # insert into aggregator db
                info_insert(self.tbl_mgr, "ops_aggregate_resource", agg_res_list)


    # Get info about resources with hrefs in the agg_atlas
    def poll_resource_info(self):
        self.agg_atlas["node"] = []    
        for res_urn in self.agg_atlas["href"]["resource"]:
            resp = requests.get(self.agg_atlas["href"]["resource"][res_urn])
            res_dict = json.loads(resp.content)
              
            if res_dict["$schema"].endswith("node#"):
                node_i = {}
                for key in res_dict:
                    if key == "ports":
                        for res_i in res_dict[key]:
                            self.agg_atlas["href"]["interface"][res_i["urn"]] = res_i["href"]
                    else:
                        node_i[key] = res_dict[key]
                self.agg_atlas["node"].append(node_i)

    # Gets node to interface mapping indepently of other polls
    # requires node list to exist in atlas
    # alternatively populate href with node hrefs
    def poll_node_interface_info(self):
        self.agg_atlas["node_interface"] = []

        for node_i in self.agg_atlas["node"]: 
            resp = requests.get(node_i["selfRef"])
            node_dict = json.loads(resp.content)
            node_id = node_dict["id"]
            interfaces = node_dict["ports"]
            for iface_i in interfaces:
                iface_i_self_ref = iface_i["href"]
                iface_i_urn = iface_i["urn"]
                
                # get resource id
                resp = requests.get(iface_i_self_ref)
                iface_i_dict = json.loads(resp.content)
                iface_i_id = iface_i_dict["id"]
                
                # temporary variables for readbility
                node_iface_list = [iface_i_id, node_id, iface_i_urn, iface_i_self_ref];
                node_iface_dict = {"id":iface_i_id, "node_id":node_id, "urn":iface_i_urn, "selfRef":iface_i_self_ref}          

                # append to atlas
                self.agg_atlas["node_interface"].append(node_iface_dict)
                # insert into aggregator db
                info_insert(self.tbl_mgr, "ops_node_interface", node_iface_list)

    def poll_aggregate_sliver_info(self):
        pass


    # Get info about interfaces with hrefs in the agg_atlas
    def poll_interface_info(self):
        self.agg_atlas["interface"] = []    
        for iface_urn in self.agg_atlas["href"]["interface"]:
            resp = requests.get(self.agg_atlas["href"]["interface"][iface_urn])
            iface_dict = json.loads(resp.content)
            iface_i = {}
            for key in iface_dict:
                iface_i[key] = iface_dict[key]
            self.agg_atlas["interface"].append(iface_i)
 
    # Get info about slivers with hrefs in the agg_atlas
    def poll_sliver_info(self):
        self.agg_atlas["sliver"] = []    
        for slv_urn in self.agg_atlas["href"]["sliver"]:
            resp = requests.get(self.agg_atlas["href"]["sliver"][slv_urn])
            slv_dict = json.loads(resp.content)
            slv_i = {}
            for key in slv_dict:
                slv_i[key] = slv_dict[key]
            self.agg_atlas["sliver"].append(slv_i)


    # Polls am hrefs, then drops/inserts aggregate table
    def refresh_aggregate_info(self):
        self.poll_aggregate_info()
        self.tbl_mgr.drop_table("ops_aggregate") 
        self.tbl_mgr.establish_table("ops_aggregate")

        schema = self.tbl_mgr.schema_dict["ops_aggregate"]

        for am_i in self.agg_atlas["aggregate"]:
            am_info_list = []
            for key in schema:  
                am_info_list.append(am_i[key[0]])
            info_insert(self.tbl_mgr, "ops_aggregate", am_info_list)

    # Polls res hrefs, then drops/inserts node table (and potentially
    # other types of resources tables)
    def refresh_resource_info(self):
        self.poll_resource_info()
        self.tbl_mgr.drop_table("ops_node") 
        self.tbl_mgr.establish_table("ops_node")

        schema = self.tbl_mgr.schema_dict["ops_node"]
        for node_i in self.agg_atlas["node"]:
            node_info_list = []            
            for key in schema:
                # extract parts of properties dictionary
                if key[0].startswith("properties$"): 
                    node_info_list.append(node_i["properties"]["ops_monitoring"][key[0].split('$')[1]])
                else:
                    node_info_list.append(node_i[key[0]])
            info_insert(self.tbl_mgr, "ops_node", node_info_list)

    # Polls interface hrefs, then drops/inserts interface table
    def refresh_interface_info(self):
        self.poll_interface_info()
        self.tbl_mgr.drop_table("ops_interface") 
        self.tbl_mgr.establish_table("ops_interface")

        schema = self.tbl_mgr.schema_dict["ops_interface"]

        for iface_i in self.agg_atlas["interface"]:
            iface_info_list = []
            for key in schema:  
                if key[0] == "address_type":
                    iface_info_list.append(iface_i["address"]["type"])
                elif key[0] == "address_address":
                    iface_info_list.append(iface_i["address"]["address"])
                else:
                    if key[0].startswith("properties$"): 
                        iface_info_list.append(iface_i["properties"]["ops_monitoring"][key[0].split('$')[1]])
                    else:
                        iface_info_list.append(iface_i[key[0]])

            info_insert(self.tbl_mgr, "ops_interface", iface_info_list)

    # Polls sliver hrefs
    def refresh_sliver_info(self):
        self.poll_sliver_info()
        self.tbl_mgr.drop_table("ops_sliver")
        self.tbl_mgr.establish_table("ops_sliver")

        schema = self.tbl_mgr.schema_dict["ops_sliver"]
        for sliver_i in self.agg_atlas["sliver"]:
            sliver_info_list = []
            for key in schema:
                if key[0] == "aggregate_urn":
                    sliver_info_list.append(sliver_i["aggregate"]["urn"])
                elif key[0] == "aggregate_href":
                    sliver_info_list.append(sliver_i["aggregate"]["href"])
                else:
                    sliver_info_list.append(sliver_i[key[0]])

            info_insert(self.tbl_mgr, "ops_sliver", sliver_info_list)

    # Polls aggregate info and then resource info to get resource ids
    def refresh_aggregate_resource_info(self):
        self.tbl_mgr.drop_table("ops_aggregate_resource") 
        self.tbl_mgr.establish_table("ops_aggregate_resource")
        self.poll_aggregate_resource_info()

    # Polls node info and then interface info to get interface ids
    def refresh_node_interface_info(self):
        self.tbl_mgr.drop_table("ops_node_interface") 
        self.tbl_mgr.establish_table("ops_node_interface")
        self.poll_node_interface_info()

    # refresh_aggregate_sliver
    def refresh_aggregate_sliver_info(self):
        self.tbl_mgr.drop_table("ops_aggregate_sliver") 
        self.tbl_mgr.establish_table("ops_aggregate_sliver")
        self.poll_aggregate_sliver_info()

    # refresh_sliver_resource

    # slices?

             
def info_insert(tbl_mgr, table_str, row_arr):
    val_str = "'"
    for val in row_arr:
        val_str += str(val) + "','" # join won't do this

    val_str = val_str[:-2] # remove last 2 of 3: ','
    
    tbl_mgr.insert_stmt(table_str, val_str)

def main():

    db_name = "aggregator"
    config_path = "../config/"

    tbl_mgr = table_manager.TableManager(db_name, config_path)

    am_urls_urns = []
    am_urls_urns.append({"href":"http://127.0.0.1:5000/info/aggregate/gpo-ig", "urn":"gpo-ig-urn"})
    if_ftr = InfoFetcher(tbl_mgr, am_urls_urns)    

    info_schema = json.load(open("../config/info_schema"))
    tbl_mgr.drop_tables(info_schema.keys())
    tbl_mgr.establish_tables(info_schema.keys())


    if_ftr.refresh_aggregate_info()
    if_ftr.refresh_resource_info()
    if_ftr.refresh_interface_info()
    if_ftr.refresh_sliver_info()


    
    if_ftr.refresh_aggregate_resource_info()
    if_ftr.refresh_node_interface_info()
    
    #pprint(if_ftr.agg_atlas)

if __name__ == "__main__":
    main()
