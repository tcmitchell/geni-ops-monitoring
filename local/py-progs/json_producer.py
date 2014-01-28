#!/usr/bin/python

# tutorial
# http://docs.python.org/2/library/json.html

import json
#import time

#
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
    
    print q_res
    #psql_to_json(q_res,"memory_util")

    #get_values()
