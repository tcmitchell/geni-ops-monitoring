#!/usr/bin/python

import json

import sys
sys.path.append("../../config")
import db_schema_config
full_schema = db_schema_config.get_schema()

def get_psql_entry(col_type, value):

    if col_type == 'varchar':
        entry = "'" + str(value) + "'"
    else: # TODO float, int if necessary
        entry = str(value)

    return entry

def json_to_psql_auto_schema(json_text, table_str, thread_name):
   
    data = json.loads(json_text)
    latest_time = 0
    rows = []

    if (data["response_type"] == "data_poll"):
        table_name = data["data_type"]
 
        if (table_name != table_str):
            error_str = "Table name returned " + table_name + " but asked for " + table_str
            return (-1, error_str, None)

        table_schema = full_schema[table_name]
        num_cols = len(table_schema)
       
        num_rows = data["num_values"];

        col_types=[]
        
        for col_i in range(num_cols):
            col_types.append(table_schema[col_i][1])

        for row_i in range(num_rows):
            
            #row_string for eventual psql insert
            row_str = "("
            for col_i in range(num_cols): 
                
                row_str = row_str + get_psql_entry(col_types[col_i], data[table_schema[col_i][0]][row_i]) + ","

                if table_schema[col_i][0] == 'time':
                    if data['time'][row_i] > latest_time:
                        latest_time = data['time'][row_i]

            # remove last comma, add parens
            row_str = row_str[:-1] + ")"

            # append to rows array
            rows.append(row_str)
    
    
    return (0,rows,latest_time)

#
# Again this is very hard coded... :( need to load the schema into here for automatic decoding
# it can be done
#
def json_to_psql(json_text, table_str, thread_name):
    
    data = json.loads(json_text)
    rows = [];
    latest_time = 0;
    if (data["response_type"] == "data_poll"):
        
        if (data["data_type"] != table_str):
            error_str = thread_name + " received data from " + data["aggregate_id"] + " about " + data["data_type"] + " when this thread cares about " + table_str
            return (1,error_str)
        else:
            num_values = data["num_values"]
            for i in range(num_values):
                row = "('" + data["aggregate_id"][i] + "','" + data["resource_id"][i] + "'," + str(data["time"][i]) + ", " + str(data["value"][i]) + ")"
                rows.append(row)
                if data["time"][i] > latest_time:
                    latest_time = data["time"][i]

            return (0,rows,latest_time)
            

def main():
    json_text = '{"data_type": "memory_util", "num_values": 5, "time": [1390939480.98, 1390939481.08, 1390939481.19, 1390939481.29, 1390939481.39], "value": [32.6, 32.6, 32.6, 32.6, 32.6], "response_type": "data_poll", "aggregate_id": ["404-ig", "404-ig", "404-ig", "404-ig", "404-ig"], "resource_id": ["compute_node_1", "compute_node_1", "compute_node_1", "compute_node_1", "compute_node_1"]}'
    #print json_text

    table_str = "memory_util"
    thread_name = "thread-test"
    
    (r_code, rows, latest_time) = json_to_psql_auto_schema(json_text, table_str, thread_name)
    print r_code
    print 'all rows', rows
    print rows[0]
    print rows[1]
    print 'latest time =',latest_time
    
if __name__ == "__main__":
    main()
