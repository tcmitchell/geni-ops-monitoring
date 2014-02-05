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

@app.route('/info/aggregate', methods = ['GET'])
def info_aggregate():  # gets all aggregates
    print "info_agg()"
 
    # query database for all aggregates and nodes gives agg info, node existence

    # form json response

    # already formed
    return json.dumps(json.load(open("../schema/examples/aggregate/agg_resp.json")))

@app.route('/info/aggregate/<agg_id>', methods = ['GET'])
def info_aggregate_args(agg_id): # gets
    print "info_agg_args(",agg_id,")"

    # query database for dom_id aggregate and nodes gives agg info, node existence

    # form json response

    # already formed
    
    return json.dumps(json.load(open("../schema/examples/aggregate/agg_resp.json")))

@app.route('/info/aggregate/<agg_id>/node', methods = ['GET'])
def info_node(agg_id):  # gets all nodes at aggregate
    print "info_node(",agg_id,")"
 
    # query database for all nodes at agg_id gives node info, port existence

    # form json response

    # already formed
    return json.dumps(json.load(open("../schema/examples/node/node_resp.json")))

@app.route('/info/aggregate/<agg_id>/<node_id>', methods = ['GET'])
def info_node_args(agg_id, node_id): 
    print "info_node_args(",agg_id,",",node_id,")"

    # query database for node_id at agg_id gives node info, port existence

    # form json response

    # already formed
    
    return json.dumps(json.load(open("../schema/examples/node/node_resp.json")))

@app.route('/info/aggregate/<agg_id>/<node_id>/<port>', methods = ['GET'])
def info_port_args(agg_id, node_id, port_id): 
    print "info_port_args(",agg_id,",",node_id,")"

    # query database for node_id at agg_id gives node info, port existence

    # form json response

    # already formed
    
    return json.dumps(json.load(open("../schema/examples/node/node_resp.json")))




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
    
    schema_file = "../config/test_schema_dict"
    json_data = open(schema_file)
    schema_dict = json.load(json_data)


    jp = json_producer.JsonProducer(schema_dict);
    

    app.run(debug = True)
