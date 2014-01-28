#!/usr/bin/python

import json

#
# Again this is very hard coded... :( need to load the schema into here for automatic decoding
# it can be done
#
def json_receiver(json_text, table_str, thread_name):
    
    data = json.loads(json_text)
    
    rows = [];
    if (data["response_type"] == "data_poll"):
        
        if (data["data_type"] != table_str):
            error_str = thread_name + " received data from " + data["aggregate_id"] + " about " + data["data_type"] + " when this thread cares about " + table_str
            return (1,error_str)
        else:
            num_values = data["num_values"]
            for i in range(num_values):
                row = "('" + data["aggregate_ids"][i] + "','" + data["resource_ids"][i] + "'," + str(data["times"][i]) + ", " + str(data["values"][i]) + ")"
                rows.append(row)
            return (0,rows)
            

def main():
    json_text = '{"data_type": "memory_util", "num_values": 5, "times": [1390939480.98, 1390939481.08, 1390939481.19, 1390939481.29, 1390939481.39], "values": [32.6, 32.6, 32.6, 32.6, 32.6], "response_type": "data_poll", "aggregate_ids": ["404-ig", "404-ig", "404-ig", "404-ig", "404-ig"], "resource_ids": ["compute_node_1", "compute_node_1", "compute_node_1", "compute_node_1", "compute_node_1"]}'
    #print json_text

    table_str = "memory_util"
    thread_name = "thread-test"
    
    (r_code, rows) = json_receiver(json_text, table_str, thread_name)
    print r_code,"\n"
    print rows[0],"\n"
    print rows[1]
    
if __name__ == "__main__":
    main()
