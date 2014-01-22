#!/usr/bin/python

import psycopg2
from time import sleep
 

conn = psycopg2.connect("dbname=agg-db user=rirwin");
cur = conn.cursor();
#insert_str = "INSERT INTO agg-table (";
# function for inserts

cur.execute();
conn.commit(); # must call or blocks others

sleep(1);



cur.close();
conn.close();
