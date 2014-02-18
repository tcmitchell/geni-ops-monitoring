#!flask/bin/python
from flask import Flask, request

import rest_call_handler
import sys

common_path = "../common/"
sys.path.append(common_path)
import table_manager

app = Flask(__name__)
       
@app.route('/info/aggregate/<agg_id>', methods = ['GET'])
def info_aggregate_args(agg_id): 
    return rest_call_handler.handle_aggregate_info_query(tm, agg_id)

@app.route('/info/node/<node_id>', methods = ['GET'])
def info_node_args(node_id): 
    return rest_call_handler.handle_node_info_query(tm, node_id)

@app.route('/info/interface/<iface_id>', methods = ['GET'])
def info_interface_args(iface_id): 
    return rest_call_handler.handle_iface_info_query(tm, iface_id)

@app.route('/info/sliver/<sliver_id>', methods = ['GET'])
def info_sliver_args(sliver_id): 
    return rest_call_handler.handle_sliver_info_query(tm, sliver_id)

@app.route('/info/slice/<slice_id>', methods = ['GET'])
def info_slice_args(slice_id): 
    return rest_call_handler.handle_slice_info_query(tm, slice_id)

@app.route('/info/user/<user_id>', methods = ['GET'])
def info_user_args(user_id): 
    return rest_call_handler.handle_user_info_query(tm, user_id)

@app.route('/info/authority/<authority_id>', methods = ['GET'])
def info_authority_args(authority_id): 
    return rest_call_handler.handle_authority_info_query(tm, authority_id)

@app.route('/info/opsconfig/<opsconfig_id>', methods = ['GET'])
def info_sliver_args(opsconfg_id): 
    return rest_call_handler.handle_opsconfig_info_query(tm, opsconfig_id)

@app.route('/data/', methods = ['GET'])
def data(): 
    # get everything to the right of ?q= as string from flask.request
    filters = request.args.get('q', None)
    return rest_call_handler.handle_ts_data_query(tm, filters)

if __name__ == '__main__':

    db_name = "local"
    config_path = "../config/"
    tm = table_manager.TableManager(db_name, config_path)

    app.run(debug = True)
