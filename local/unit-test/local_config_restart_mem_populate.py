import sys
import json
import psycopg2

sys.path.append("../../common/")
import table_manager
sys.path.append("../")
import local_datastore_populator

info_schema = json.load(open("../../config/info_schema"))
data_schema = json.load(open("../../config/data_schema"))

table_str_arr = info_schema.keys() + data_schema.keys()

db_con_str = "dbname=local user=rirwin"
con = psycopg2.connect(db_con_str);
 
tm = table_manager.TableManager(con, data_schema, info_schema)

tm.drop_tables(table_str_arr)
tm.establish_tables(table_str_arr)

sys.argv.append(10)
sys.argv.append(0.2)

local_datastore_populator.generate_and_insert_config_data(data_schema, info_schema)   

# 404 is not found and the area code in atlanta #TheGoalIsGEC19
aggregate_id="404-ig" 
node_id="404-ig-pc1"
table_str = "mem_used"    
data_table_str_arr = [table_str]
info_table_str_arr = ["aggregate","node","interface"]
num_ins = 10
per_sec = 0.2
ldp = local_datastore_populator.LocalDatastorePopulator(con, aggregate_id, node_id, num_ins, per_sec, tm, data_table_str_arr, info_table_str_arr)

ldp.run_node_inserts("mem_used")
