#----------------------------------------------------------------------
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
import info_fetcher

class DataFetcher:
    
    def __init__(self, info_fetcher):
        self.info_fetcher = info_fetcher

    def get_nodes_at_am(self, am_id):
        pass
                       
def info_insert(tbl_mgr, table_str, row_arr):
    val_str = "'"
    for val in row_arr:
        val_str += str(val) + "','" # join won't do this

    val_str = val_str[:-2] # remove last 2 of ','
    tbl_mgr.ins_stmt(table_str, val_str)


def main():

    db_name = "aggregator"
    config_path = "../config/"

    tbl_mgr = table_manager.TableManager(db_name, config_path)
    am_urls_urns = []
    am_urls_urns.append({"href":"http://127.0.0.1:5000/info/aggregate/404-ig", "urn":"404-ig-urn"})
    if_ftr = InfoFetcher(tbl_mgr, am_urls_urns)    

    info_schema = json.load(open("../config/info_schema"))
    tbl_mgr.drop_tables(info_schema.keys())
    tbl_mgr.establish_tables(info_schema.keys())
    
    if_ftr.refresh_am_info()
    if_ftr.refresh_res_info()
    if_ftr.refresh_iface_info()
    if_ftr.refresh_aggregate_resource_info()
    if_ftr.refresh_node_interface_info()
    
    pprint(if_ftr.agg_atlas)

    dt_ftr = DataFetcher(if_ftr)



if __name__ == "__main__":
    main()
