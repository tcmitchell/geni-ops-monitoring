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
