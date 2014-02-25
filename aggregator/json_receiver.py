#!/usr/bin/python
#----------------------------------------------------------------------
# Copyright (c) 2014 Raytheon BBN Technologies
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and/or hardware specification (the "Work") to
# deal in the Work without restriction, including without limitation the
# rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Work, and to permit persons to whom the Work
# is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Work.
#
# THE WORK IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
# OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE WORK OR THE USE OR OTHER DEALINGS
# IN THE WORK.
#----------------------------------------------------------------------

import json


class JsonReceiver:
    def __init__(self, schema_dict):
        self.schema_dict = schema_dict

    def json_to_psql(self, json_text, table_str, thread_name, obj_id):
        data = json.loads(json_text)
        if "tsdata" in data:
            # check if obj_id == data id?
            return self.tsdata_to_rows(data["tsdata"], table_str, obj_id)
        else:
            return None

    def tsdata_to_rows(self, tsdata, table_str, obj_id):
        rows = []
        
        #for i in tsdata:
            #rows.append("insert into " + table_str + " values('" +obj_id + "'" + obj)
        print tsdata
        return rows

    # deprecated    
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
    
    
if __name__ == "__main__":
    main()
