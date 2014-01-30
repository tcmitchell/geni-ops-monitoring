#!/usr/bin/python

# tutorial
# http://docs.python.org/2/library/json.html

import json
#import time

import sys
sys.path.append("../../config")
import db_schema_config

'''
{
"response_type": "data_poll",
"data_type": "memory_util", 
"results": 
  [ 
   {
   "aggregate_id": "404-ig",
   "resource_id": "compute_node_1", 
   "measurements": [{"timestamp": 1391036714.17,
                                "value": 37.8},
                               {"timestamp": 1391036818.49,
                                "value": 37.8},
                               {"timestamp": 1391036818.71,
                                "value": 37.8}]
   },
   {
   "aggregate_id": "404-ig",
   "resource_id": "compute_node_2", 
   "measurements": [{"timestamp": 1391036715.32,
                                "value": 58.8},
                               {"timestamp": 1391036819.28,
                                "value": 58.3}]
   }
  ]
}
 schema["memory_util"] = [("aggregate_id","varchar"),("resource_id","varchar"), ("time", "float8"), ("value", "float8")]

'''

class JsonProducer:
    def __init__(self, schema_dict):
        self.schema_dict = schema_dict

    def psql_to_json(self, q_res, table_name):
        if (table_name == "info"): 
            json_dict = self.psql_to_json_info(q_res)
        else:
            json_dict = self.psql_to_json_data(q_res, table_name)
        return json_dict

    def psql_to_json_info(self, q_res):
        pass # not implemented yet


    def psql_to_json_data(self, q_res, table_name):

        schema = self.schema_dict[table_name]
        num_cols = len(schema)
        num_rows = len(q_res)
        print schema


        # enumerate columns
        key_cols = self.get_data_groupings(schema)
        items_dict = {}
        num_cols_not_tv = len(key_cols[0])

        # pass through results to pick up items
        for row_i in range(num_rows):
            row = q_res[row_i]
            group_key =  repr(row[0:num_cols_not_tv])
            if group_key not in items_dict:
                items_dict[group_key] = {}
                for col_i in range (num_cols-2): # last 2 are time & value
                    items_dict[group_key][schema[col_i][0]] = row[col_i]
                items_dict[group_key]["measurements"] = []
            items_dict[group_key]["measurements"].append({schema[-1][0]:row[-1],schema[-2][0]:row[-2]})
        
        json_dict = {}
        json_dict["response_type"] = "data_poll"
        json_dict["data_type"] = table_name
        json_dict["results"] = []

        for item in items_dict:
            json_dict["results"].append(items_dict[item])
        return json.dumps(json_dict)
            
    # gets every combination of columns that are not 'time' or 'value'
    def get_data_groupings(self, schema):
        num_cols = len(schema)
        keys = []

        for i in range(num_cols):
            for j in range(i+1,num_cols):
                if (schema[i][0] == "time" or schema[i][0] == "value" or schema[j][0] == "time" or schema[j][0] == "value") == False:
                    keys.append([schema[i][0], schema[j][0]])

        return keys

# function version, to be removed
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


if __name__ == "__main__":

    # appearance of result from query
    q_res = []
    row = ("404-ig","compute_node_1", 1390939480.1, 32.6)
    q_res.append(row)
    row = ("404-ig","compute_node_2", 1390939481.1, 42.5)
    q_res.append(row)
    row = ("404-ig","compute_node_2", 1390939482.1, 35.6)
    q_res.append(row)
    row = ("404-ig","compute_node_1", 1390939483.1, 32.1)
    q_res.append(row)
    row = ("404-ig","compute_node_1", 1390939484.1, 32.0)
    q_res.append(row)
    
   
    jp = JsonProducer(db_schema_config.get_schema())
    print jp.psql_to_json(q_res, "memory_util")
    

    #j_new = psql_to_json_auto_schema(q_res,"memory_util")    
    #print "New way=\n", j_new
    
    
    #data = json.loads(j)
    #print data
    #get_values()
