#!/usr/bin/python

import psycopg2
import time
import psutil
import sys
import json
import threading
from pprint import pprint as pprint

sys.path.append("../common/")
import table_manager

class LocalDatastorePopulator:
    def __init__(self, con, psql_lock,  table_manager):
        self.con = con
        self.psql_lock = psql_lock
        self.table_manager = table_manager
       

def main():

    db_con_str = "dbname=local user=rirwin";
    con = psycopg2.connect(db_con_str);
    data_schema = json.load(open("../config/data_schema"))
    info_schema = json.load(open("../config/info_schema"))
    
    psql_lock = threading.Lock() 

    # TODO consider passing psql_lock to table_manager
    tm = table_manager.TableManager(con, data_schema, info_schema)

    ldp = LocalDatastorePopulator(con, psql_lock, tm)
    
    cur.close();
    con.close();

if __name__ == "__main__":
    main()
