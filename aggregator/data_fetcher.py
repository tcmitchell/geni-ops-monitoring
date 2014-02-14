import json
import psycopg2
import sys
import requests
from pprint import pprint

config_path = "../config/"
common_path = "../common/"

sys.path.append(config_path)
sys.path.append(common_path)
import table_manager
import postgres_conf_loader
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
    cur = tbl_mgr.con.cursor()
    tbl_mgr.db_lock.acquire()
    cur.execute("insert into " + table_str + " values (" + val_str + ")")
    tbl_mgr.con.commit()
    tbl_mgr.db_lock.release()
    cur.close()  

def main():

    [database_, username_, password_, host_, port_] = postgres_conf_loader.aggregator(config_path)

    con = psycopg2.connect(database = database_, user = username_, password = password_, host = host_, port = port_)

    info_schema = json.load(open("../config/info_schema"))
    data_schema = json.load(open("../config/data_schema"))
    tbl_mgr = table_manager.TableManager(con, data_schema, info_schema)

    tbl_mgr.drop_tables(info_schema.keys())
    tbl_mgr.establish_tables(info_schema.keys())

    tbl_mgr.drop_tables(data_schema.keys())
    tbl_mgr.establish_tables(data_schema.keys())

    am_urls_urns = []
    am_urls_urns.append({"href":"http://127.0.0.1:5000/info/aggregate/404-ig", "urn":"404-ig-urn"})
    
    info_fetcher = InfoFetcher(tbl_mgr, am_urls_urns)
    
    info_fetcher.refresh_am_info()
    info_fetcher.refresh_res_info()
    info_fetcher.refresh_iface_info()
        
    pprint(info_fetcher.agg_atlas)

    data_fetcher = DataFetcher(info_fetcher)



if __name__ == "__main__":
    main()
