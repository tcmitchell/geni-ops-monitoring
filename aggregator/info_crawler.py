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
from pprint import pprint

common_path = "../common/"
sys.path.append(common_path)
import table_manager

# agg is for aggregator 
# aggregate is for aggregate manager 

# am_urls is a list of dictionaies with hrefs to reach the datastore of
# the am urn

# This program populates the aggregator database on every fetch

class InfoCrawler:
    
    def __init__(self, tbl_mgr, local_datastore, aggregate_id):
        self.tbl_mgr = tbl_mgr

        if local_datastore[-1] == '/':
            local_datastore = local_datastore[:-1]
        self.local_datastore = local_datastore
        self.aggregate_id = aggregate_id

    # Updates head aggregate information
    def refresh_aggregate_info(self):
        
        am_dict = handle_request(self.local_datastore + '/aggregate/' + self.aggregate_id)            
        if am_dict:
            self.tbl_mgr.establish_table("ops_aggregate")
            schema = self.tbl_mgr.schema_dict["ops_aggregate"]
            am_info_list = []
            for key in schema:
                am_info_list.append(am_dict[key[0]])
            info_update(self.tbl_mgr, "ops_aggregate", am_dict["id"], am_info_list)
        

        
    # Updates all nodes information
    def refresh_all_nodes_info(self):

        am_dict = handle_request(self.local_datastore + '/aggregate/' + self.aggregate_id)
        if am_dict:
            schema = self.tbl_mgr.schema_dict["ops_node"]

            for res_i in am_dict["resources"]:
                res_dict = handle_request(res_i["href"])
                if res_dict["$schema"].endswith("node#"): # if a node
                    
                    # get each attribute out of response into list
                    node_info_list = []
                    for key in schema: 
                        # ugly parsing of properties dictionary and schema
                        if key[0].startswith("properties$"): 
                            if "ops_monitoring" in res_dict["properties"]:
                                if key[0].split('$')[1] in res_dict["properties"]["ops_monitoring"]:
                                    node_info_list.append(res_dict["properties"]["ops_monitoring"][key[0].split('$')[1]])
                        else:
                            node_info_list.append(res_dict[key[0]])
                    # add/update ops_node table
                    info_update(self.tbl_mgr, "ops_node", res_dict["id"], node_info_list) 
                # add/update aggregate resource table
                agg_res_info_list = [res_dict["id"], am_dict["id"], res_dict["urn"], res_dict["selfRef"]]
                info_update(self.tbl_mgr, "ops_aggregate_resource", res_dict["id"], agg_res_info_list)

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
    val_str = "'"
    for val in row_arr:
        val_str += str(val) + "','" # join won't do this
    val_str = val_str[:-2] # remove last 2 of 3: ','
    tbl_mgr.insert_stmt(table_str, val_str)

def main():

    db_name = "aggregator"
    config_path = "../config/"

    tbl_mgr = table_manager.TableManager(db_name, config_path)

    datastore_url = "http://127.0.0.1:5000/info/"
    aggregate_id = "gpo-ig"

    #am_urls_urns.append({"href":"http://aj-dev6.grnoc.iu.edu/geni-local-datastore/info/aggregate/ion.internet2.edu", "urn":"urn:publicid:IDN+ion.internet2.edu+authority+cm"})
    ic = InfoCrawler(tbl_mgr, datastore_url, aggregate_id)    

    info_schema = json.load(open("../config/info_schema"))
    #tbl_mgr.drop_tables(info_schema.keys())
    tbl_mgr.establish_tables(info_schema.keys())

    ic.refresh_aggregate_info()
    ic.refresh_all_nodes_info()

if __name__ == "__main__":
    main()

