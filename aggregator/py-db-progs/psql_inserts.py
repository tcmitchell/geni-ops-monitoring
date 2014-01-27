#!/usr/bin/python

import psycopg2
import dummy_json_fetcher
from time import sleep
import json


db_schema = {}
db_schema["memory_util"] = "(agg_id varchar, time float8, value float4)"

# all in one function for now, simple and updates are contained in
# here as compared to alternatives (returning a struct that matches
# schema)
def json_receiver(json_text, con):
    cur = con.cursor()
    data = json.loads(json_text)

    if (data["response_type"] == "data_poll"):
        table_name = data["data_type"] # good practice?    
        cur.execute("CREATE TABLE IF NOT EXISTS " + table_name + db_schema[table_name]);
        con.commit()

        print "Data from", data["aggregate_name"]

        ins_str_base = "INSERT INTO " + table_name + " values ('" + data["aggregate_id"] + "',"

        num_values = data["num_values"];
        for i in range(num_values):
            cur.execute(ins_str_base + str(data["times"][i]) + ", " + str(data["values"][i]) + ");")
        
        con.commit()
            


def main():

    con = psycopg2.connect("dbname=rirwin user=rirwin");
    cur = con.cursor();

    cur.execute("drop table if exists memory_util;");
    con.commit(); 

    djf = dummy_json_fetcher.get_values();
    
    json_receiver(djf,con)


    cur.execute("select count(*) from memory_util;");
    print cur.fetchone()[0]



    cur.close();
    con.close();


if __name__ == "__main__":
    main()
