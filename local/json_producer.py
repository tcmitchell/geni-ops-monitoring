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
   

    def json_node_info(self, node_id, info_row, port_refs =[]):

        schema = self._schema_dict["node"]
        json_dict = {}
        for col_i in range(len(schema)):
            json_dict[schema[col_i][0]] = info_row[col_i]
            
        if len(port_refs) > 0 and port_refs[0] != None:
            json_dict["ports"] = []
            for port_ref in port_refs:
                json_dict["ports"].append({"href":port_ref[0],"urn":port_ref[1]})

        return json.dumps(json_dict)
 
    def json_interface_info(self, info_row):

        schema = self._schema_dict["interface"]
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


    def event_data_to_json(self, tsdata, event_type, obj_id):

        schema = self._schema_dict[event_type]
        units = self._schema_dict["units"]
        json_dict = {}
        json_dict["$schema"] = "http://www.gpolab.bbn.com/monitoring/schema/20140131/data#"
        json_dict["id"] = obj_id + ":" + event_type # TODO unique id
        json_dict["subject"] = obj_id # TODO add selfref
        json_dict["eventType"] = event_type
        json_dict["units"] = units
        json_dict["tsdata"] = tsdata

        return json.dumps(json_dict)

if __name__ == "__main__":

    print "no main, removed old unit-test"
