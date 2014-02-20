#!/usr/bin/python
#----------------------------------------------------------------------
# Copyright (c) 2014 Raytheon BBN Technologies
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and/or hardware specification (the "Work") to
# deal in the Work without restriction, including without limitation the
# rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Work, and to permit persons to whom the Work
# is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Work.
#
# THE WORK IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
# OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE WORK OR THE USE OR OTHER DEALINGS
# IN THE WORK.
#----------------------------------------------------------------------

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
