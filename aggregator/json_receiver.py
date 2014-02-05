#!/usr/bin/python

import json


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

        return (0, rows)
                            

def get_psql_entry(col_type, value):

    if col_type == 'varchar':
        entry = "'" + str(value) + "'"
    else: # TODO float, int if necessary
        entry = str(value)

    return entry



def main():
    json_text = '{"response_type": "data_poll", "data_type": "memory_util", "results": [{"resource_id": "compute_node_1", "measurements": [{"v": 37.8, "ts": 1391036714.17}, {"v": 37.8, "ts": 1391036818.49}, {"v": 37.8, "ts": 1391036818.71}], "aggregate_id": "404-ig"},{"resource_id": "compute_node_2", "measurements": [{"v": 37.8, "ts": 1391036714.17}, {"v": 37.8, "ts": 1391036818.49}, {"v": 37.8, "ts": 1391036818.71}], "aggregate_id": "404-ig"}]}'
    
    print json_text

    table_str = "memory_util"
    thread_name = "thread-test"

    # Dense lines to get schema_dict
    db_templates = json.load(open("../config/db_templates"))
    event_types = json.load(open("../config/event_types"))
    schema_dict = {}
    for ev_t in event_types.keys():
        schema_dict[ev_t] = db_templates[event_types[ev_t]["db_template"]] + [["v",event_types[ev_t]["v_col_type"]]]
    # end dense lines to get schema_dict


    jr = JsonReceiver(schema_dict)
    
    (r_code, rows) = jr.json_to_psql(json_text, table_str, thread_name)
    
    print r_code
    print 'all rows', len(rows)
    print rows
    print rows[0]
    print rows[1]
    
if __name__ == "__main__":
    main()
