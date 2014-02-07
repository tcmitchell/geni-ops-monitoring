#!flask/bin/python
from flask import Flask, request
import psycopg2
import json_producer
import query_handler
import time
import json
import sys
from pprint import pprint as pprint
sys.path.append("../common/db-tools")
import table_manager
app = Flask(__name__)

def extract_ts_filters(ts_filters):
    ts_lt = int(time.time()*1000000)
    ts_gte = 0

    for ts_filter in ts_filters:
        ts_typ = ts_filter.split('=')[0]
        ts_val = int(ts_filter.split('=')[1])
        if ts_typ == 'gte':
            ts_gte = ts_val 
        elif ts_typ == 'lt':
            ts_lt = ts_val
    
    return (ts_lt, ts_gte)

'''
# fix json import
@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify( { 'error': 'Not found' } ), 404)
'''

@app.route('/', methods = ['GET'])
def index():
    return "Hello, World!"

@app.route('/info', methods = ['GET'])
def info():
    return "info great"


@app.route('/info/aggregate/<agg_id>', methods = ['GET'])
def info_aggregate_args(agg_id): 
    print "info_agg_args(",agg_id,")"
    table_str = "aggregate"
    res_refs = []    
    slv_refs = []
    
    agg_info = query_handler.get_object_info(con, table_str, agg_id)
    if agg_info != None:

        resources = query_handler.get_agg_nodes(con, agg_id)
        for res_id in resources:
            res_refs.append(query_handler.get_refs(con, "resource", res_id))

        slivers = query_handler.get_agg_slivers(con, agg_id)
        print "slivers",slivers
        for slv_id in slivers:
            slv_refs.append(query_handler.get_refs(con, "sliver", slv_id))

        return jp.json_agg_info(table_str, agg_info, res_refs, slv_refs)

    else:
        return "aggregate not found"

@app.route('/info/node/<res_id>', methods = ['GET'])
def info_node_args(res_id): 
    print "info_node_args(",res_id,")"
    table_str = "resource"
    port_refs = []

    res_info = query_handler.get_object_info(con, table_str, res_id)
    if res_info != None:

        ports = query_handler.get_res_ports(con, res_id)
        for port_id in ports:
            port_refs.append(query_handler.get_refs(con, "port", port_id))

        return jp.json_res_info(table_str, res_info, port_refs)

    else:
        return "resource not found"
    
@app.route('/info/interface/<port_id>', methods = ['GET'])
def info_interface_args(port_id): # gets interface info
    print "info_interface_args(",port_id,")"
    table_str = "port"
    port_info = query_handler.get_object_info(con, table_str, port_id)

    if port_info != None:
        return jp.json_port_info(table_str, port_info)
    else:
        return "port not found"



@app.route('/data/', methods = ['GET'])
def data(): 

    # gets event type (i.e., memory_util)
    event_type = request.args.get('event_type', None)
    if event_type == None:
        return "provide an event_type"

    # get all timestamp filters
    ts = request.args.get('ts', 0)

    ts_filters = request.args.getlist('ts')

    (ts_lt, ts_gte) = extract_ts_filters(ts_filters)

    if ts_gte <= 0:
        print "get all " + event_type + ", recommended to use ?ts= filter next query"
    else:
        print "get", event_type, "between", ts_gte, "and", ts_lt

    where_filter = "where ts >= " + str(ts_gte) + " and ts < " + str(ts_lt)
    (r_stat, q_res) = query_handler.select_query(con,event_type,where_filter);

    print q_res
    if (r_stat == 0):
        # form json
        j = jp.psql_to_json(q_res, event_type)
        return j
    else:
        return str(r_stat) + ": " + q_res


if __name__ == '__main__':

    con = psycopg2.connect("dbname=local user=rirwin");
    

    # Dense lines to get schema_dict
    info_schema = json.load(open("../config/info_schema"))
    data_schema = json.load(open("../config/data_schema"))

    tm = table_manager.TableManager(con, info_schema, data_schema)
    jp = json_producer.JsonProducer(tm.schema_dict);

    app.run(debug = True)
