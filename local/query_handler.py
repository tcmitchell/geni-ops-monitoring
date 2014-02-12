#!/usr/bin/python
from pprint import pprint as pprint
import json
import psycopg2

    # remove this comment once documented on wiki
    # Valid call
    #{"filters":{"eventType": ["mem_used","cpu_util"],"ts":{"gte":3,"lt":5},"obj":{"type":"node","id":["404-ig-pc1","404-ig-pc2"]}}}

def check_data_query_keys(q_dict):

    if "filters" not in q_dict:
        return (False, "query: " + str(q_dict) + "<br><br>has dictionary error.  It is missing filters key")
        
    missing_keys = []
    if "ts" not in q_dict["filters"]:
        missing_keys.append("ts")
    if "eventType" not in q_dict["filters"]:
        missing_keys.append("eventType")
    if "obj" not in q_dict["filters"]:
        missing_keys.append("obj")

    if len(missing_keys) > 0:
        return (False, "query: " + str(q_dict) + "<br><br>has dictionary error.  It is missing keys: " + str(missing_keys))

    return (True, None)

def handle_ts_data_query(con, filters, schema_dict):

    # try to make a dictionary
    try:
        q_dict = eval(filters) 

    except Exception, e:
        return "query: " + filters + "<br><br>had error: " + str(e) + "<br><br> failed to evaluate as dictionary"

    # check for necessary keys
    (ok, fail_str) = check_data_query_keys(q_dict)
    if ok == True:
        ts_filters = q_dict["filters"]["ts"]
        event_types = q_dict["filters"]["eventType"]
        objects = q_dict["filters"]["obj"]
    else:
        return fail_str # returns why filters failed

    ts_where_str = build_ts_where_str(ts_filters)
    resp_arr = []    
    
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
                resp_arr.append(resp_i)

    return json.dumps(resp_arr)
 
def get_interface_info_dict(schema, info_row):

    json_dict = {}
    for col_i in range(len(schema)):
        if schema[col_i][0] == "address_address":
            addr = info_row[col_i]
        elif schema[col_i][0] == "address_type":
            addr_type = info_row[col_i]
        else:
            json_dict[schema[col_i][0]] = info_row[col_i]
            
    json_dict["address"] = {"address":addr,"type":addr_type}

    return json_dict


def handle_iface_info_query(con, iface_id, iface_schema):
    table_str = "interface"
    iface_info = get_object_info(con, table_str, iface_id)

    if iface_info != None:
        return json.dumps(get_interface_info_dict(iface_schema, iface_info))
    else:
        return "port not found"


def get_node_info_dict(node_id, schema, info_row, port_refs =[]):

    json_dict = {}
    for col_i in range(len(schema)):
        json_dict[schema[col_i][0]] = info_row[col_i]
            
    if len(port_refs) > 0 and port_refs[0] != None:
        json_dict["ports"] = []
        for port_ref in port_refs:
            json_dict["ports"].append({"href":port_ref[0],"urn":port_ref[1]})
            
    return json_dict

def handle_node_info_query(con, node_id, node_schema):
    
    table_str = "node"
    iface_refs = []

    node_info = get_object_info(con, table_str, node_id)

    if node_info != None:

        ifaces = get_node_interfaces(con, node_id)
        for iface_id in ifaces:
            iface_refs.append(get_refs(con, "interface", iface_id))

        return json.dumps(get_node_info_dict(node_id, node_schema, node_info, iface_refs))

    else:
        return "resource not found"


def get_agg_info_dict(agg_id, info_row, schema, res_refs =[], slv_refs = []):

    json_dict = {}
    for col_i in range(len(schema)):
        json_dict[schema[col_i][0]] = info_row[col_i]
            
    if len(res_refs) > 0 and res_refs[0] != None:
        json_dict["resources"] = []
        for res_ref in res_refs:
            json_dict["resources"].append({"href":res_ref[0],"urn":res_ref[1]})

    if len(slv_refs) > 0 and slv_refs[0] != None:
        json_dict["slivers"] = []
        for slv_ref in slv_refs:
            json_dict["slivers"].append({"href":slv_ref[0],"urn":slv_ref[1]})  
    return json_dict


def handle_agg_info_query(con, agg_id, agg_schema):
    table_str = "aggregate"
    res_refs = []    
    slv_refs = []

    agg_info = get_object_info(con, table_str, agg_id)
    if agg_info != None:

        resources = get_agg_nodes(con, agg_id)
        for res_id in resources:
            res_refs.append(get_refs(con, "resource", res_id))

        slivers = get_agg_slivers(con, agg_id)
        print "slivers",slivers
        for slv_id in slivers:
            slv_refs.append(get_refs(con, "sliver", slv_id))

        return json.dumps(get_agg_info_dict(agg_id, agg_info, agg_schema, res_refs, slv_refs))

    else:
        return "aggregate not found"

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
