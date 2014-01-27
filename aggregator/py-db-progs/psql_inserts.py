#!/usr/bin/python

import psycopg2
import dummy_json_fetcher
from time import sleep
import json



def json_receiver(json_text):
    data = json.loads(json_text)
    print data
    print data["response-type"]
    print data["aggregate-name"]
    print data["aggregate-id"]
    print data["data-type"]
    print data["num-values"]
    num_values = data["num-values"];
    for i in range(num_values):
        print data["values"][i], "at", data["times"][i]

    return data

def main():
    conn = psycopg2.connect("dbname=agg_db user=rirwin");
    cur = conn.cursor();
    #insert_str = "INSERT INTO agg-table (";
    # function for inserts

    cur.execute("drop table if exists agg_table_mem;");
    conn.commit(); 
    cur.execute("create table agg_table_mem(urn_id int8, time float8, value float4);");
    conn.commit(); 
    


    djf = dummy_json_fetcher.get_values();
    
    json_receiver(djf)


    cur.execute("select count(*) from agg_table_mem;");
    print cur.fetchone()[0]

    #sleep(1);



    cur.close();
    conn.close();


if __name__ == "__main__":
    main()
