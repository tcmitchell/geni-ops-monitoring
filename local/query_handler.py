#!/usr/bin/python

import psycopg2

def query(con, table, where_filter):
    cur = con.cursor()
    q_res = None;
    r_stat = None;

    try:
        cur.execute("select * from " + table + " where " + where_filter + " + LIMIT 10000;")
        q_res = cur.fetchall()
        r_stat = 0
    except Exception, e:
        q_res = e.pgerror
        r_stat = 500
        pass

    return (r_stat, q_res)

def main():
    con = psycopg2.connect("dbname=local user=rirwin");
    print query(con, "memory_util", "time > 1")

if __name__ == "__main__":
    main()
