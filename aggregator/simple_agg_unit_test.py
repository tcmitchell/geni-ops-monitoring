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
