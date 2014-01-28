#!flask/bin/python
from flask import Flask, request
import psycopg2
import json_producer
import psql_query

app = Flask(__name__)

# lock for database

# conn of database
con = None

'''
# fix json import
@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify( { 'error': 'Not found' } ), 404)
'''

@app.route('/', methods = ['GET'])
def index():
    return "Hello, World!"


@app.route('/memory_util/', methods = ['GET'])
def memory_util():

    # TODO numeric and "" checking and exception handling
    since = request.args.get('since', 0)
    
    if since <= 0:
        print "get all memory_util, recommended to use ?since= filter next query"
    else:
        print "get memory since", since

    # query local store for memory util
    q_res = psql_query.query(con,"memory_util","time > " + str(since));
    
    # form json
    j = json_producer.psql_to_json(q_res, "memory_util")

    return j



if __name__ == '__main__':
    con = psycopg2.connect("dbname=local user=rirwin");
    app.run(debug = True)
