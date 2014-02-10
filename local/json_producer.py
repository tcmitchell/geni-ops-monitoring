#!/usr/bin/python

import json
from pprint import pprint as pprint

class JsonProducer:
    def __init__(self, schema_dict):
        self._schema_dict = schema_dict

    def psql_to_json(self, q_res, table_str):
        json_dict = self.psql_to_json_data(q_res, table_str)
        return json_dict

    def json_agg_info(self, agg_id, info_row, res_refs =[], slv_refs = []):

        schema = self._schema_dict["aggregate"]
        json_dict = {}
        for col_i in range(len(schema)):
            json_dict[schema[col_i][0]] = info_row[col_i]
            
        if len(res_refs) > 0 and res_refs[0] != None:
            json_dict["resources"] = []
            for res_ref in res_refs:
                json_dict["resources"].append({"href":res_ref[0],"urn":res_ref[1]})

        if len(slv_refs) > 0 and slv_refs[0] != None:
            json_dict["slivers"] = []
            for slv_ref in slv_refs:
                json_dict["slivers"].append({"href":slv_ref[0],"urn":slv_ref[1]})  
        return json.dumps(json_dict)
   

    # TODO merge with above if possible
    def json_res_info(self, resource_id, info_row, port_refs =[]):

        schema = self._schema_dict["resource"]
        json_dict = {}
        for col_i in range(len(schema)):
            json_dict[schema[col_i][0]] = info_row[col_i]
            
        if len(port_refs) > 0 and port_refs[0] != None:
            json_dict["ports"] = []
            for port_ref in port_refs:
                json_dict["ports"].append({"href":port_ref[0],"urn":port_ref[1]})

        return json.dumps(json_dict)
   
    # TODO merge with above if possible (probably not because of address)
    def json_port_info(self, port_id, info_row):

        schema = self._schema_dict["port"]
        json_dict = {}
        for col_i in range(len(schema)):
            if schema[col_i][0] == "address_address":
                addr = info_row[col_i]
            elif schema[col_i][0] == "address_type":
                addr_type = info_row[col_i]
            else:
                json_dict[schema[col_i][0]] = info_row[col_i]
    
        json_dict["address"] = {"address":addr,"type":addr_type}

        return json.dumps(json_dict)


    def event_resource_data_to_json(self, tsdata, event_type, res_id):

        schema = self._schema_dict[event_type]

        json_dict = {}
        json_dict["$schema"] = "http://www.gpolab.bbn.com/monitoring/schema/20140131/data#"
        json_dict["id"] = res_id + ":" + event_type
        json_dict["subject"] = res_id # TODO add selfref
        json_dict["eventType"] = event_type
        json_dict["units"] = "units" # TODO get units
        json_dict["tsdata"] = tsdata

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
    event_types = json.load(open("../config/event_types"))
    schema_dict = {}
    for ev_t in event_types.keys():
        schema_dict[ev_t] = db_templates[event_types[ev_t]["db_template"]] + [["v",event_types[ev_t]["v_col_type"]]]
    # end dense lines to get schema_dict


    jp = JsonProducer(schema_dict)
    print jp.psql_to_json(q_res, "memory_util")
