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

import sys
import json

common_path = "../../common/"

sys.path.append(common_path)
import table_manager

def load_data_schema(config_store_url):
    # hard code until we get the schema online
    opsconfig_file = config_store_url
    opsconfig = json.load(open(opsconfig_file))
    
    data_schema = {}
    
    # node event types
    for ev_i in opsconfig["events"]["node"]:
        data_schema["ops_"+ev_i["name"]] = [["id",ev_i["id"]],["ts",ev_i["ts"]],["v",ev_i["v"]],["units",ev_i["units"]]]
        
    # interface event types
    for ev_i in opsconfig["events"]["interface"]:
        data_schema["ops_"+ev_i["name"]] = [["id",ev_i["id"]],["ts",ev_i["ts"]],["v",ev_i["v"]],["units",ev_i["units"]]]
        
    return data_schema

def main():

    db_type = "collector"
    config_path = "../../config/"
    config_store_url = "../../schema/examples/opsconfig/geni-prod.json"
    debug = True
    tbl_mgr = table_manager.TableManager(db_type, config_path, config_store_url, debug)

    info_schema = json.load(open(config_path + "info_schema"))
    data_schema = load_data_schema(config_store_url)

    table_str_arr = info_schema.keys() + data_schema.keys()

    tbl_mgr.drop_tables(table_str_arr)
    tbl_mgr.establish_tables(table_str_arr)
   
    tbl_mgr.con.close()

if __name__ == "__main__":
    main()
