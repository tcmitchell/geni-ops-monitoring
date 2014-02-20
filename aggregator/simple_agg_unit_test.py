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
import json

# Dense lines to get schema_dict
db_templates = json.load(open("../config/db_templates"))
event_types = json.load(open("../config/event_types"))
schema_dict = {}
for ev_t in event_types.keys():
    schema_dict[ev_t] = db_templates[event_types[ev_t]["db_template"]] + [["v",event_types[ev_t]["v_col_type"]]]
# end dense lines to get schema_dict



table_str = "memory_util"
table_schema = schema_dict[table_str]

con = psycopg2.connect("dbname=aggregator user=rirwin");
cur = con.cursor()

schema_str = "("
for col_i in range(len(table_schema)):
    schema_str = schema_str + table_schema[col_i][0] + " " + table_schema[col_i][1] + "," 
        
# remove , and add ), makes a smug face [:-1]
schema_str = schema_str[:-1] + ")"

cur.execute("create table if not exists " + table_str + schema_str);
con.commit()

cur.execute("INSERT INTO " + table_str + " VALUES('404-ig','compute_node_1',1390939481.08,32.6),('404-ig','compute_node_1',1390939481.08,32.6);")
con.commit()

cur.execute("select count(*) from " + table_str + ";");
print "num entries", cur.fetchone()[0]

cur.close()
con.close()
