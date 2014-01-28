#!/usr/bin/python

import psycopg2

def query(con, table, where_filter):
    cur = con.cursor()
    cur.execute("select * from " + table + " where " + where_filter + ";")
    return cur.fetchall()

def main():
    con = psycopg2.connect("dbname=local user=rirwin");
    query(con, "memory_util", "time > 1")

if __name__ == "__main__":
    main()
