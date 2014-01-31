#!/usr/bin/python

# THIS FILE IS FOR TESTING A MANUAL QUERY AND INSERT
# NOT USED

import psycopg2
import json
import requests

from sys import path as sys_path 
sys_path.append("../config")
import schema_config

full_schema = schema_config.get_schema()


def json_receiver(json_text, con):
    cur = con.cursor()
    data = json.loads(json_text)

    if (data["response_type"] == "data_poll"):
        table_name = data["data_type"] 
        table_schema = full_schema[table_name]
        num_cols = len(table_schema)
        schema_str = "("
        for col_i in range(num_cols-1):
            schema_str = schema_str + table_schema[col_i][0] + " " + table_schema[col_i][1] + ", " 
        schema_str = schema_str + table_schema[-1][0] + " " + table_schema[-1][1] +  ")";
       
        cur.execute("CREATE TABLE IF NOT EXISTS " + table_name + schema_str + ";");
        con.commit()
        
        ins_str_base = "INSERT INTO " + table_name + " values "

        num_rows = data["num_values"];
        rows_str = ""

        col_types=[]
        
        for col_i in range(num_cols):
            col_types.append(table_schema[col_i][1])

        for row_i in range(num_rows):
            rows_str = rows_str + "("
            for col_i in range(num_cols-1): 
                # make the following a function
                if col_types[col_i] == 'varchar':
                    rows_str = rows_str + "'" + str(data[table_schema[col_i][0]][row_i]) + "', "
                else: # TODO float, int ...
                    rows_str = rows_str + str(data[table_schema[col_i][0]][row_i]) + ", "      
    
            # make the following a function
            if col_types[col_i] == 'varchar':
                rows_str = rows_str + "'" + str(data[table_schema[-1][0]][row_i]) + "')" 
            else: # TODO float, int ...
                rows_str = rows_str + str(data[table_schema[-1][0]][row_i]) + ")"

            if (row_i < num_rows - 1):
                rows_str = rows_str + ","

        cur.execute(ins_str_base + rows_str + ";");
        
        con.commit()
    cur.close()
            
def json_fetcher():

    payload = {'since':1390950580.92}
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
    print 'Count is', cur.fetchone()[0]



    cur.close();
    con.close();


if __name__ == "__main__":
    main()
