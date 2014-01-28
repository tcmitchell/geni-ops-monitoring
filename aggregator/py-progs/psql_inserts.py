#!/usr/bin/python

import psycopg2
import json
import requests

db_schema = {}
db_schema["memory_util"] = "(aggregate_id varchar, time float8, value float8)"

# all in one function for now, simple and updates are contained in
# here as compared to alternatives (returning a struct that matches
# schema)
def json_receiver(json_text, con):
    cur = con.cursor()
    data = json.loads(json_text)

    if (data["response_type"] == "data_poll"):
        table_name = data["data_type"] 
        cur.execute("CREATE TABLE IF NOT EXISTS " + table_name + db_schema[table_name]);
        con.commit()

        print "Data from", data["aggregate_name"]

        ins_str_base = "INSERT INTO " + table_name + " values ('" + data["aggregate_id"] + "',"

        num_values = data["num_values"];
        for i in range(num_values):
            cur.execute(ins_str_base + str(data["times"][i]) + ", " + str(data["values"][i]) + ");")
         
        con.commit()
            
def json_fetcher():

    payload = {'since':2}
    r = requests.get('http://127.0.0.1:5000/memory_util/',params=payload)
    return r.content

def main():

    con = psycopg2.connect("dbname=aggregator user=rirwin");
    cur = con.cursor();

    cur.execute("drop table if exists memory_util;");
    con.commit(); 

    response = json_fetcher()
    json_receiver(response, con)


    cur.execute("select count(*) from memory_util;");
    print cur.fetchone()[0]



    cur.close();
    con.close();


if __name__ == "__main__":
    main()
