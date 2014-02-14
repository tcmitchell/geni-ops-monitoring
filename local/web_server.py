#!flask/bin/python
from flask import Flask, request
import psycopg2
import rest_call_handler
import sys
import json
from pprint import pprint as pprint

config_path = "../config/"
common_path = "../common/"

sys.path.append(config_path)
sys.path.append(common_path)
import table_manager
import postgres_conf_loader

app = Flask(__name__)
       
@app.route('/info/aggregate/<agg_id>', methods = ['GET'])
def info_aggregate_args(agg_id): 
    return rest_call_handler.handle_agg_info_query(tm, agg_id, tm.schema_dict["aggregate"])

@app.route('/info/node/<node_id>', methods = ['GET'])
def info_node_args(node_id): 
    return rest_call_handler.handle_node_info_query(tm, node_id, tm.schema_dict["node"])

@app.route('/info/interface/<iface_id>', methods = ['GET'])
def info_interface_args(iface_id): 
    return rest_call_handler.handle_iface_info_query(tm, iface_id, tm.schema_dict["interface"])

@app.route('/data/', methods = ['GET'])
def data(): 
    # get everything to the right of ?q= as string from flask.request
    filters = request.args.get('q', None)
    return rest_call_handler.handle_ts_data_query(tm, filters, tm.schema_dict)

if __name__ == '__main__':

    [database_, username_, password_, host_, port_] = postgres_conf_loader.local(config_path)

    con = psycopg2.connect(database = database_, user = username_, password = password_, host = host_, port = port_)

    info_schema = json.load(open("../config/info_schema"))
    data_schema = json.load(open("../config/data_schema"))
    tm = table_manager.TableManager(con, data_schema, info_schema)
    app.run(debug = True)
