#!/usr/bin/python

import psycopg2
from time import sleep


conn = psycopg2.connect("dbname=aggregator user=rirwin");
cur = conn.cursor();

check_size_pretty_db_str = "select * from pg_size_pretty(pg_database_size('agg-db'))"
check_size_db_str = "select * from pg_database_size('agg-db')"


# function for checking size of database

cur.execute(check_size_pretty_db_str);
conn.commit(); # must call or blocks others
size = cur.fetchone()[0]
print size

#if (True): # too big condition
#    delete_str = "delete from agg-table where id in (select if from agg-table order by id limit " + str(10) + ");"; # math for deletion
#
# counter for vacuuming
#
# end


cur.close();
conn.close();
