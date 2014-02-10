#!/usr/bin/python

import psycopg2

# TODO find cursor not closed.  probably in exceptions

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

def get_res_ports(con, res_id_str):
    cur = con.cursor()
    print "cursor open"
    res = [];

    try:
        cur.execute("select distinct id from resource_port  where resource_id = '" + res_id_str + "'")
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

def select_query(con, table, where_filter="", order_by_filter = "", limit_filter = "LIMIT 10000"):
    cur = con.cursor()
    print "cursor open"
    q_res = None;
    r_stat = None;

    try:
        cur.execute("select * from " + table + " " + where_filter + " " + order_by_filter + " " + limit_filter)
        q_res = cur.fetchall()
        r_stat = 0
    except Exception, e:
        q_res = e
        r_stat = 500
    
    cur.close()
    print "cursor closed"

    return (r_stat, q_res)

def main():
    con = psycopg2.connect("dbname=local user=rirwin");
    print query(con, "memory_util", "time > 1")

if __name__ == "__main__":
    main()
