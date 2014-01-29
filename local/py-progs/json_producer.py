#!/usr/bin/python

# tutorial
# http://docs.python.org/2/library/json.html

import json
#import time

import sys
sys.path.append("../../config")
import db_schema_config

def psql_to_json_auto_schema(q_res, table_name):
    schema = db_schema_config.get_schema_for_type(table_name)
    num_cols = len(schema)
    num_rows = len(q_res)
    data = []
    
    for col_i in range(num_cols):
        data.append([])
        for row_i in range(num_rows):
            data[col_i].append(q_res[row_i][col_i])
    
    json_dict = {}
    json_dict['response_type'] = 'data_poll'
    json_dict['data_type'] = table_name
    json_dict['num_values'] = num_rows

    for col_i in range(num_cols):
        json_dict[schema[col_i][0]] = data[col_i][0:num_rows]
   
    return json.dumps(json_dict)
#
# TODO changes here required when schema update....hardcoded, :(
# I bet I could use the schema for automating this
#
def psql_to_json(q_res, table_name):
    
    num_values = len(q_res)

    aggregate_ids = []
    resource_ids = []
    values = []
    times = [] 
    
    for i in range(num_values): 
        aggregate_ids.append(q_res[i][0])
        resource_ids.append(q_res[i][1])
        times.append(q_res[i][2])
        values.append(q_res[i][3])

    j = json.dumps({'response_type': 'data_poll',
                    'data_type': table_name,
                    'num_values': num_values,
                    'aggregate_ids': (aggregate_ids[0:num_values]),
                    'resource_ids': (resource_ids[0:num_values]),
                    'values': (values[0:num_values]),
                    'times': (times[0:num_values])
                    })

    return j

if __name__ == "__main__":

    # appearance of result from query
    q_res = []
    row = ("404-ig","compute_node_1", 1390939480.1, 32.6)
    q_res.append(row)
    row = ("404-ig","compute_node_1", 1390939481.1, 42.5)
    q_res.append(row)
    row = ("404-ig","compute_node_1", 1390939482.1, 35.6)
    q_res.append(row)
    row = ("404-ig","compute_node_1", 1390939483.1, 32.1)
    q_res.append(row)
    row = ("404-ig","compute_node_1", 1390939484.1, 32.0)
    q_res.append(row)
    
    #print q_res
    j = psql_to_json(q_res,"memory_util")

    print "Old way=\n",j

    j_new = psql_to_json_auto_schema(q_res,"memory_util")    
    print "New way=\n", j_new
    
    
    #data = json.loads(j)
    #print data
    #get_values()
