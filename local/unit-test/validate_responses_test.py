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
import os
import urllib2
from pprint import pprint as pprint


def properties_dict(props_schema, props_dict):

    return True


def has_keys_values(schema, a_dict):
    
    keys = schema.keys()
    values = schema.values()

    for i in xrange (len(keys)):
        if keys[i] not in a_dict:
            return False

        if values[i] == 'schema:string':
            if not isinstance(a_dict[keys[i]], unicode):
                return False
        elif values[i] == 'schema:integer':
            if not isinstance(a_dict[keys[i]], int):
                return False
        elif values[i] == 'schema:float':
            if not isinstance(a_dict[keys[i]], float):
                return False

    return True


def check_list(schema, resp):
    del schema["schema:type"]
    for obj_i in resp:
        if not has_keys_values(schema, obj_i):
            return False
    return True

def check_dict(schema, resp):
    del schema["schema:type"]

    return has_keys_values(resp, schema)


def validate_response(schema, resp):

    for k in resp.keys():

        if isinstance(schema[k], dict):
            if schema[k]["schema:type"] == "schema:list":
                if isinstance(resp[k], list):
                    if not check_list(dict(schema[k]), resp[k]):
                        return (False, str(resp[k]) + " list did not match the schema")
                else:
                    return (False, str(resp[k]) + " is not a list")
            elif schema[k]["schema:type"] == "schema:dict":
                if isinstance(resp[k], dict):
                    if not check_dict(dict(schema[k]), resp[k]):
                        return (False, str(resp[k]) + " dict did not match the schema")
                else:
                    return (False, str(resp[k]) + " is not a dict")
        elif isinstance(schema[k], list):
            print k, "schema is a list"
        elif schema[k] == 'schema:string':
            if not isinstance(resp[k], unicode):
                return (False, schema[k] + " is not a string")
        elif schema[k] == 'schema:integer':
            if not isinstance(resp[k], int):
                return (False, schema[k] + " is not an integer")
        elif schema[k] == 'schema:float': 
            if not isinstance(resp[k], float):
                return (False, schema[k] + " is not a float")
        else:
            "no match in type"

    return True


# refresh database at local store
#os.system("python local_restart_node_interface_stats.py")

json_schema_path = "./"
json_schema = json.load(open(json_schema_path + "json_schema"))
pprint(json_schema)
base_url = "http://127.0.0.1:5000/"


opsconfig = base_url + "info/opsconfig/geni-prod"

resp = json.load(urllib2.urlopen(opsconfig))
schema = json_schema["opsconfig"]

print validate_response(schema, resp)


interface = base_url + "info/interface/instageni.gpolab.bbn.com_interface_pc1:eth0"

resp = json.load(urllib2.urlopen(interface))
schema = json_schema["interface"]

print validate_response(schema, resp)




