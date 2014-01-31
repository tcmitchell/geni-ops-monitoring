#!/usr/bin/python

import json

from sys import path as sys_path 
sys_path.append("../../config")
import schema_config


class JsonReceiver:
    def __init__(self, schema_dict):
        self.schema_dict = schema_dict

    def json_to_psql(self, json_text, table_str, thread_name):
        data = json.loads(json_text)
        if (data["response_type"] == "data_poll"):
            return self.json_to_psql_data(data, table_str)

    def json_to_psql_data(self, data, table_str):
        table_name = data["data_type"]
        
        if (table_name != table_str):
            error_str = "Table name returned " + table_name + " but asked for " + table_str
            return (-1, error_str, None)

        table_schema = self.schema_dict[table_name]
        num_cols = len(table_schema)
        rows = []
        # make this a function
        for res_item_i in range(len(data["results"])):
            item_dict = data["results"][res_item_i]
            num_cols_not_tv = len(item_dict) - 1
            row_base_str = "("
            for col_i in range(num_cols_not_tv): # base of values insert str
                if table_schema[col_i][1] == 'varchar':
                    row_base_str = row_base_str + "'" + item_dict[table_schema[col_i][0]] + "',"
                else:
                    row_base_str = row_base_str + item_dict[table_schema[col_i][0]] + ","

            for meas_i in item_dict["measurements"]:
                rows.append(row_base_str +str(meas_i[table_schema[-1][0]]) + ", " + str(meas_i[table_schema[-2][0]]) + ")")

        return (0, rows, 0)
                            

def get_psql_entry(col_type, value):

    if col_type == 'varchar':
        entry = "'" + str(value) + "'"
    else: # TODO float, int if necessary
        entry = str(value)

    return entry

# deprecated
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



def main():
    json_text = '{"response_type": "data_poll", "data_type": "memory_util", "results": [{"resource_id": "compute_node_1", "measurements": [{"value": 37.8, "time": 1391036714.17}, {"value": 37.8, "time": 1391036818.49}, {"value": 37.8, "time": 1391036818.71}], "aggregate_id": "404-ig"},{"resource_id": "compute_node_2", "measurements": [{"value": 37.8, "time": 1391036714.17}, {"value": 37.8, "time": 1391036818.49}, {"value": 37.8, "time": 1391036818.71}], "aggregate_id": "404-ig"}]}'
    
    print json_text

    table_str = "memory_util"
    thread_name = "thread-test"
    jr = JsonReceiver(schema_config.get_schema())
    
    (r_code, rows, latest_time) = jr.json_to_psql(json_text, table_str, thread_name)
    
    print r_code
    print 'all rows', len(rows)
    print rows
    print rows[0]
    print rows[1]
    print 'latest time =',latest_time
    
if __name__ == "__main__":
    main()
