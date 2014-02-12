#!/usr/bin/python
from pprint import pprint as pprint
import json
import psycopg2

def select_distinct_query(con, table, distinct_filter = "",  where_filter=""):
    cur = con.cursor()
    print "cursor open"
    q_res = None;
    r_stat = None;
    try:
        cur.execute("select " + distinct_filter + " from " + table + " " + where_filter);
        q_res = cur.fetchone()
        r_stat = 0
    except Exception, e:
        q_res = e
        r_stat = 500

    cur.close()
    print "cursor closed"

    return (r_stat, q_res)

def get_agg_nodes(con, agg_id_str):
    cur = con.cursor()
    print "cursor open"
    res = [];

    try:
        cur.execute("select distinct id from aggregate_resource where aggregate_id = '" + agg_id_str + "'") 
        q_res = cur.fetchall()
        q_res = q_res[0] # removes outer garbage
        for res_i in range(len(q_res)):
            res.append(q_res[res_i])

    except Exception, e:
        print e

    cur.close()
    print "cursor closed"

    return res

def get_agg_slivers(con, agg_id_str):
    cur = con.cursor()
    print "cursor open"
    res = [];

    try:
        cur.execute("select distinct id from aggregate_sliver where aggregate_id = '" + agg_id_str + "'") 
        q_res = cur.fetchall()
        q_res = q_res[0] # removes outer garbage
        for res_i in range(len(q_res)):
            res.append(q_res[res_i])

    except Exception, e:
        print e


    cur.close()
    print "cursor closed"

    return res

def get_node_interfaces(con, node_id_str):
    cur = con.cursor()
    print "cursor open"
    res = [];

    try:
        cur.execute("select distinct id from node_interface where node_id = '" + node_id_str + "'")
        q_res = cur.fetchall()
        q_res = q_res[0] # removes outer garbage
        for res_i in range(len(q_res)):
            res.append(q_res[res_i])

    except Exception, e:
        print e

    cur.close()
    print "cursor closed"

    return res

def get_object_info(con, table_str, obj_id):
    cur = con.cursor()
    print "cursor open"
    res = None;

    try:
        cur.execute("select * from " + table_str + " where id = '" + obj_id + "' order by ts desc limit 1")
        res = cur.fetchone()
       
    except Exception, e:
        print e
    
    cur.close()
    print "cursor closed"

    return res

def get_refs(con, table_str, resource_id):
    cur = con.cursor()
    print "cursor open"
    refs = None;

    try:
        cur.execute("select \"selfRef\" from " + table_str + " where id = '" + resource_id + "' order by ts desc limit 1")
        q_res = cur.fetchone()

        self_ref = q_res[0] # removes outer garbage

        cur.execute("select \"urn\" from " + table_str + " where id = '" + resource_id + "' order by ts desc limit 1")
        q_res = cur.fetchone()

        urn = q_res[0] # removes outer garbage
        refs = [self_ref, urn] # two queries avoids regex split with ,

    except Exception, e:
        print e
    
    cur.close()
    print "cursor closed"

    return refs

def build_ts_where_str(ts_dict):
    ts_where_str = ""

    try:
        for ts_k in ts_dict:
            ts_v = ts_dict[ts_k]
            if ts_k == 'gte':
                ts_where_str += "ts >= " + str(ts_v) + " "
            elif ts_k == 'gt':
                ts_where_str += "ts > " + str(ts_v) + " "
            elif ts_k == 'lte':
                ts_where_str += "ts <= " + str(ts_v) + " "
            elif ts_k == 'lt':
                ts_where_str += "ts < " + str(ts_v) + " "
    except Exception, e:
        print str(e), "ts filters has invalid key or value:"

    return ts_where_str

# handles query and json response
def handle_data_query(con, event_types, objects, ts_filters, schema_dict):
    resp_arr = []
    
    ts_where_str = build_ts_where_str(ts_filters)
    
    for event_type in event_types:
        obj_type = objects["type"]
        for obj_id in objects["id"]:
            resp_i = {}
            ts_arr = get_tsdata(con, event_type, obj_type, obj_id, ts_where_str)
            if (ts_arr != None):
                resp_i["$schema"] = "http://www.gpolab.bbn.com/monitoring/schema/20140131/data#"
                resp_i["id"] = obj_id + ":" + event_type
                resp_i["subject"] = obj_id
                resp_i["eventType"] = event_type
                resp_i["description"] = event_type + " for " + obj_id + " of type " + obj_type
                resp_i["units"] = schema_dict["units"][event_type]
                resp_i["tsdata"] = ts_arr
                #pprint(resp_i)
                resp_arr.append(resp_i)

    return json.dumps(resp_arr)


def get_tsdata(con, event_type, obj_type, obj_id, ts_where_str):
    cur = con.cursor()
    res = None
    try:
        # assumes an id for obj_id in table event_type 
        cur.execute("select (ts,v) from " + event_type + " where id = '" + obj_id + "' and " + ts_where_str)
        q_res = cur.fetchall()
        if len(q_res) > 0:
            res = []
            for q_res_i in xrange(len(q_res)): # parsing result "(<ts>,<v>)"
                q_res_i = q_res[q_res_i][0][1:-1].split(',')
                res.append({"ts":q_res_i[0],"v":q_res_i[1]})
        
    except Exception, e:
        print "query failed: select (ts,v) from " + event_type + " where id = '" + obj_id + "' and " + ts_where_str
        print e

    cur.close()
    return res


def main():
    con = psycopg2.connect("dbname=local user=rirwin");
    print query(con, "memory_util", "time > 1")

if __name__ == "__main__":
    main()
