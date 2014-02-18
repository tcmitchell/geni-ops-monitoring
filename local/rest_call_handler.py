#!/usr/bin/python
import json

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

# Main handle for data queries
def handle_ts_data_query(tm, filters):
    schema_dict = tm.schema_dict
    try:
        q_dict = eval(filters) # try to make a dictionary

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
            ts_arr = get_tsdata(tm, event_type, obj_type, obj_id, ts_where_str)
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
 
# forms interface info dictionary (to be made to JSON)
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

# Main handle interface queries
def handle_iface_info_query(tm, iface_id):
    table_str = "interface"
    iface_schema = tm.schema_dict[table_str]
    con = tm.con

    iface_info = get_object_info(tm, table_str, iface_id)

    if iface_info != None:
        return json.dumps(get_interface_info_dict(iface_schema, iface_info))
    else:
        return "port not found"

# Forms node info dictionary (to be made to JSON)
def get_node_info_dict(schema, info_row, port_refs =[]):

    json_dict = {}
    for col_i in range(len(schema)):
        json_dict[schema[col_i][0]] = info_row[col_i]
            
    if len(port_refs) > 0 and port_refs[0] != None:
        json_dict["ports"] = []
        for port_ref in port_refs:
            json_dict["ports"].append({"href":port_ref[0],"urn":port_ref[1]})
            
    return json_dict

# Main handle for node queries
def handle_node_info_query(tm, node_id):
    table_str = "node"
    node_schema = tm.schema_dict[table_str]
    con = tm.con

    iface_refs = []

    node_info = get_object_info(tm, table_str, node_id)

    if node_info != None:

        ifaces = get_node_interfaces(tm, node_id)
        for iface_id in ifaces:
            iface_refs.append(get_refs(tm, "interface", iface_id))

        return json.dumps(get_node_info_dict(node_schema, node_info, iface_refs))

    else:
        return "resource not found"



# Forms sliver info dictionary (to be made to JSON)
def get_sliver_info_dict(schema, info_row, res_refs =[]):

    json_dict = {}
    for col_i in range(len(schema)):
        if schema[col_i][0] == "aggregate_urn":
            agg_urn = info_row[col_i]
        elif schema[col_i][0] == "aggregate_href":
            agg_href = info_row[col_i]
        else:
            json_dict[schema[col_i][0]] = info_row[col_i]
            
    json_dict["aggregate"] = {"urn":agg_urn,"href":agg_href}

            
    if len(res_refs) > 0 and res_refs[0] != None:
        json_dict["resources"] = []
        for res_ref in res_refs:
            json_dict["resources"].append({"href":res_ref[0],"urn":res_ref[1]})
            
    return json_dict

# Main handle for sliver queries
def handle_sliver_info_query(tm, sliver_id):
    table_str = "sliver"
    sliver_schema = tm.schema_dict[table_str]
    con = tm.con

    res_refs = []

    sliver_info = get_object_info(tm, table_str, sliver_id)

    if sliver_info != None:

        resources = get_sliver_nodes(tm, sliver_id)
        for res_id in resources:
            res_refs.append(get_refs(tm, "node", res_id))

        return json.dumps(get_sliver_info_dict(sliver_schema, sliver_info, res_refs))

    else:
        return "resource not found"

# Forms aggregate info dictionary (to be made to JSON)
def get_aggregate_info_dict(schema, info_row, res_refs =[], slv_refs = []):

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


# Main handle aggregate for info queries
def handle_aggregate_info_query(tm, agg_id):
    table_str = "aggregate"
    agg_schema = tm.schema_dict[table_str]
    con = tm.con

    res_refs = []    
    slv_refs = []

    agg_info = get_object_info(tm, table_str, agg_id)
    if agg_info != None:

        resources = get_aggregate_nodes(tm, agg_id)
        for res_id in resources:
            res_refs.append(get_refs(tm, "node", res_id))

        slivers = get_aggregate_slivers(tm, agg_id)
        print "slivers",slivers
        for slv_id in slivers:
            slv_refs.append(get_refs(tm, "sliver", slv_id))

        return json.dumps(get_aggregate_info_dict(agg_schema, agg_info, res_refs, slv_refs))

    else:
        return "aggregate not found"

# Gets an aggregates nodes from aggregate_resource table
def get_aggregate_nodes(tm, agg_id_str):
    cur = tm.con.cursor()
    res = [];

    try:
        tm.db_lock.acquire()
        cur.execute("select distinct id from aggregate_resource where aggregate_id = '" + agg_id_str + "'") 
        q_res = cur.fetchall()
        tm.db_lock.release()
        q_res = q_res[0] # removes outer garbage
        for res_i in range(len(q_res)):
            res.append(q_res[res_i])

    except Exception, e:
        print e

    cur.close()

    return res

# Gets an slivers nodes from aggregate_resource table
def get_sliver_nodes(tm, slv_id_str):
    cur = tm.con.cursor()
    res = [];

    try:
        tm.db_lock.acquire()
        cur.execute("select distinct id from sliver_resource where sliver_id = '" + slv_id_str + "'") 
        q_res = cur.fetchall()
        tm.db_lock.release()
        q_res = q_res[0] # removes outer garbage
        for res_i in range(len(q_res)):
            res.append(q_res[res_i])

    except Exception, e:
        print e

    cur.close()

    return res

# Gets an aggregate's slivers from aggregate_sliver table
def get_aggregate_slivers(tm, agg_id_str):
    cur = tm.con.cursor()
    res = [];

    try:
        tm.db_lock.acquire()
        cur.execute("select distinct id from aggregate_sliver where aggregate_id = '" + agg_id_str + "'") 
        q_res = cur.fetchall()
        tm.db_lock.release()
        q_res = q_res[0] # removes outer garbage
        for res_i in range(len(q_res)):
            res.append(q_res[res_i])

    except Exception, e:
        print e

    cur.close()

    return res

# Gets node interfaces from node_interface table
def get_node_interfaces(tm, node_id_str):
    cur = tm.con.cursor()
    res = [];

    try:
        tm.db_lock.acquire()
        cur.execute("select distinct id from node_interface where node_id = '" + node_id_str + "'")
        q_res = cur.fetchall()
        tm.db_lock.release()
        q_res = q_res[0] # removes outer garbage
        for res_i in range(len(q_res)):
            res.append(q_res[res_i])

    except Exception, e:
        print e

    cur.close()

    return res

# Gets object info where an object can be anything (node, aggregate,
# interface, sliver
def get_object_info(tm, table_str, obj_id):
    cur = tm.con.cursor()
    res = None;

    try:
        tm.db_lock.acquire()
        cur.execute("select * from " + table_str + " where id = '" + obj_id + "' order by ts desc limit 1")
        res = cur.fetchone()
        tm.db_lock.release()
    except Exception, e:
        print e
    
    cur.close()

    return res

# Get references of resources
def get_refs(tm, table_str, resource_id):
    cur = tm.con.cursor()
    refs = None;

    try:
        # two queries avoids regex split with ,
        tm.db_lock.acquire()
        cur.execute("select \"selfRef\" from " + table_str + " where id = '" + resource_id + "' order by ts desc limit 1")
        q_res = cur.fetchone()

        self_ref = q_res[0] # removes outer garbage

        cur.execute("select \"urn\" from " + table_str + " where id = '" + resource_id + "' order by ts desc limit 1")
        q_res = cur.fetchone()
        tm.db_lock.release()
        urn = q_res[0] # removes outer garbage
        refs = [self_ref, urn] 

    except Exception, e:
        print e
    
    cur.close()

    return refs

# builds timestamp filter as a where clause for SQL statement
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

def get_tsdata(tm, event_type, obj_type, obj_id, ts_where_str):
    cur = tm.con.cursor()
    res = None
    try:
        tm.db_lock.acquire()

        # assumes an id for obj_id in table event_type 
        cur.execute("select (ts,v) from " + event_type + " where id = '" + obj_id + "' and " + ts_where_str)
        q_res = cur.fetchall()
        tm.db_lock.release()

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
    print "no unit test"

if __name__ == "__main__":
    main()
