#!flask/bin/python
from flask import Flask, request
import psycopg2
import json_producer
import query_handler
import time
import json

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
def info_aggregate_args(agg_id): # gets aggregate info
    print "info_agg_args(",agg_id,")"

    # query database for dom_id aggregate and nodes gives agg info, node existence

    # form json response

    # already formed
    
    return json.dumps(json.load(open("../schema/examples/aggregate/agg_resp.json")))


@app.route('/info/aggregate/<agg_id>/<node_id>', methods = ['GET'])
def info_node_args(agg_id, node_id): # gets node info
    print "info_node_args(",agg_id,",",node_id,")"

    # query database for node_id at agg_id gives node info, interface existence

    # form json response

    # already formed
    
    return json.dumps(json.load(open("../schema/examples/node/node_resp.json")))


@app.route('/info/aggregate/<agg_id>/<node_id>/<interface_id>', methods = ['GET'])
def info_interface_args(agg_id, node_id, interface_id): # gets interface info
    print "info_interface_args(",agg_id,",",interface_id,")"

    # query database for port_id at node_id gives node info

    # form json response

    # already formed
    
    return json.dumps(json.load(open("../schema/examples/interface/iface_resp1.json")))




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
        print "get all memory_util, recommended to use ?ts= filter next query"
    else:
        print "get", event_type, "between", ts_gte, "and", ts_lt

    where_params = "ts >= " + str(ts_gte) + " and ts < " + str(ts_lt)
    (r_stat, q_res) = query_handler.query(con,event_type,where_params);

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
    db_templates = json.load(open("../config/db_templates"))
    event_types = json.load(open("../config/event_types"))
    schema_dict = {}
    for ev_t in event_types.keys():
        schema_dict[ev_t] = db_templates[event_types[ev_t]["db_template"]] + [["v",event_types[ev_t]["v_col_type"]]]
    # end dense lines to get schema_dict

    jp = json_producer.JsonProducer(schema_dict);
    

    app.run(debug = True)
