#!/usr/bin/python

import psycopg2

# TODO find cursor not closed.  probably in exceptions

def select_distinct_query(con, table, distinct_filter = "",  where_filter=""):
    cur = con.cursor()
    q_res = None;
    r_stat = None;
    try:
        cur.execute("select " + distinct_filter + " from " + table + " " + where_filter);
        q_res = cur.fetchone()
        r_stat = 0
    except Exception, e:
        q_res = e.pgerror
        r_stat = 500

    cur.close()

    return (r_stat, q_res)

def get_agg_nodes(con, agg_id_str):
    cur = con.cursor()
    res = [];

    try:
        cur.execute("select distinct nodes from aggregate  where id = '" + agg_id_str + "'")
        q_res = cur.fetchall()
        q_res = q_res[0] # removes outer garbage
        for res_i in range(len(q_res)):
            res.append(q_res[res_i])

    except Exception, e:
        print e.pgerror

    cur.close()

    return res

def get_node_ifaces(con, node_id_str):
    cur = con.cursor()
    res = [];

    try:
        cur.execute("select distinct interfaces from node  where id = '" + node_id_str + "'")
        q_res = cur.fetchall()
        q_res = q_res[0] # removes outer garbage
        for res_i in range(len(q_res)):
            res.append(q_res[res_i])

    except Exception, e:
        print e.pgerror

    cur.close()

    return res

def get_object_info(con, table_str, obj_id):
    cur = con.cursor()
    res = None;

    try:
        cur.execute("select * from " + table_str + " where id = '" + obj_id + "' order by ts desc limit 1")
        res = cur.fetchone()
       
    except Exception, e:
        print e.pgerror
    
    cur.close()

    return res

def get_self_ref(con, table_str, resource_id):
    cur = con.cursor()
    res = None;

    try:
        print "select \"selfRef\" from " + table_str + " where id = '" + resource_id + "' order by ts desc limit 1"
        cur.execute("select \"selfRef\" from " + table_str + " where id = '" + resource_id + "' order by ts desc limit 1")
        q_res = cur.fetchone()
        res = q_res[0] # removes outer garbage

    except Exception, e:
        print e.pgerror
    
    cur.close()

    return res

def select_query(con, table, where_filter="", order_by_filter = "", limit_filter = "LIMIT 10000"):
    cur = con.cursor()
    q_res = None;
    r_stat = None;

    try:
        cur.execute("select * from " + table + " " + where_filter + " " + order_by_filter + " " + limit_filter)
        q_res = cur.fetchall()
        r_stat = 0
    except Exception, e:
        q_res = e.pgerror
        r_stat = 500
    
    cur.close()

    return (r_stat, q_res)

def main():
    con = psycopg2.connect("dbname=local user=rirwin");
    print query(con, "memory_util", "time > 1")

if __name__ == "__main__":
    main()
