#!/usr/bin/python

import json


class JsonProducer:
    def __init__(self, schema_dict):
        self._schema_dict = schema_dict

    def psql_to_json(self, q_res, table_name):
        if (table_name == "info"): 
            json_dict = self.psql_to_json_info(q_res)
        else:
            json_dict = self.psql_to_json_data(q_res, table_name)
        return json_dict

    def psql_to_json_info(self, q_res):
        pass # not implemented yet

    def psql_to_json_data(self, q_res, table_name):

        schema = self._schema_dict[table_name]
        num_cols = len(schema)
        num_rows = len(q_res)

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

    # Dense lines to get schema_dict
    db_templates = json.load(open("../config/db_templates"))
    event_types = json.load(open("../config/event_types"))
    schema_dict = {}
    for ev_t in event_types.keys():
        schema_dict[ev_t] = db_templates[event_types[ev_t]["db_template"]] + [["v",event_types[ev_t]["v_col_type"]]]
    # end dense lines to get schema_dict


    jp = JsonProducer(schema_dict)
    print jp.psql_to_json(q_res, "memory_util")
