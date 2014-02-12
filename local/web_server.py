#!flask/bin/python
from flask import Flask, request
import psycopg2
import json_producer
import query_handler
import time
import json
import sys
from pprint import pprint as pprint
sys.path.append("../common")
import table_manager
app = Flask(__name__)

def check_data_query_keys(q_dict):
    missing_keys = []

    if "filters" not in q_dict:
        missing_keys.append("filter")
    if "ts" not in q_dict["filters"]:
        missing_keys.append("ts")
    if "eventType" not in q_dict["filters"]:
        missing_keys.append("eventType")
    if "obj" not in q_dict["filters"]:
        missing_keys.append("obj")
    if len(missing_keys) > 0:
        return (False, "query: " + str(q_dict) + "<br><br>has dictionary error.  It is missing keys: " + str(missing_keys))
    
    return (True, None)
        
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
    
    return (str(ts_lt), str(ts_gte))

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

@app.route('/info/node/<node_id>', methods = ['GET'])
def info_node_args(node_id): 
    print "info_node_args(",node_id,")"
    table_str = "node"
    iface_refs = []

    node_info = query_handler.get_object_info(con, table_str, node_id)
    if node_info != None:

        ifaces = query_handler.get_node_interfaces(con, node_id)
        for iface_id in ifaces:
            iface_refs.append(query_handler.get_refs(con, "interface", iface_id))

        return jp.json_node_info(table_str, node_info, iface_refs)

    else:
        return "resource not found"
    
@app.route('/info/interface/<iface_id>', methods = ['GET'])
def info_interface_args(iface_id): # gets interface info
    print "info_interface_args(",iface_id,")"
    table_str = "interface"
    iface_info = query_handler.get_object_info(con, table_str, iface_id)

    if iface_info != None:
        return jp.json_interface_info(iface_info)
    else:
        return "port not found"


@app.route('/data/v2/', methods = ['GET'])
def data_v2(): 
    # get everything to the right of ?q= as string from Flask
    # then stop using Flask
    #
    # Valid call
    #
    #{"filters":{"eventType": ["mem_used","cpu_util"],"ts":{"gte":3,"lt":5},"obj":{"type":"node","id":["404-ig-pc1","404-ig-pc2"]}}}
    q = request.args.get('q', None)
    ret_str = ""
    try:
        q_dict = eval(q)
        
        (ok, fail_str) = check_data_query_keys(q_dict)

        if ok == True:
            ts_filters = q_dict["filters"]["ts"]
            ev_t_filters = q_dict["filters"]["eventType"]
            obj_filters = q_dict["filters"]["obj"]
        
            pprint(ts_filters)
            pprint(ev_t_filters)
            pprint(obj_filters)
        else:
            return fail_str

    except Exception, e:
        return "query: " + q + "<br><br>had error: " + str(e) + "<br><br> failed to evaluate as dictionary"       

    ## do query handling
    


    return "/data/v2/" + q + "<br>" + ret_str

@app.route('/data/', methods = ['GET'])
def data(): 

    # gets event type (i.e., memory_util)
    event_type = request.args.get('eventType', None)
    if event_type == None:
        return "provide an eventType"
   
    # get all timestamp filters
    ts = request.args.get('ts', 0)
    ts_filters = request.args.getlist('ts')
    (ts_lt, ts_gte) = extract_ts_filters(ts_filters)

    # handle if 
    obj_id = request.args.get('obj_id', 0)

    if ts_gte <= 0:
        print "get all " + event_type + ", recommended to use ?ts= filter next query"
    else:
        print "get", event_type, "between", ts_gte, "and", ts_lt

    if (obj_id != None):
        tsdata = query_handler.get_event_data(con, event_type, ts_gte, ts_lt, obj_id);


    if (tsdata):
        # form json
        j = jp.event_data_to_json(tsdata, event_type, obj_id)
        return j
    else:
        return "No results for " + str(obj_id) + " of eventType " + str(event_type)


if __name__ == '__main__':

    con = psycopg2.connect("dbname=local user=rirwin");

    # Dense lines to get schema_dict
    info_schema = json.load(open("../config/info_schema"))
    data_schema = json.load(open("../config/data_schema"))

    tm = table_manager.TableManager(con, data_schema, info_schema)
    jp = json_producer.JsonProducer(tm.schema_dict);

    app.run(debug = True)
