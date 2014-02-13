#!/usr/bin/python

import psycopg2
import time
import psutil
import sys
import json
from pprint import pprint as pprint

sys.path.append("../common/")
import table_manager

class LocalDatastorePopulator:
    def __init__(self, con, table_manager):
        self.con = con
        self.tbl_mgr = table_manager       

def main():

    db_con_str = "dbname=local user=rirwin";
    con = psycopg2.connect(db_con_str);
    data_schema = json.load(open("../config/data_schema"))
    info_schema = json.load(open("../config/info_schema"))
    
    tm = table_manager.TableManager(con, data_schema, info_schema)

    ldp = LocalDatastorePopulator(con, tm)
    

if __name__ == "__main__":
    main()
