import sys
import json
import psycopg2
import threading

sys.path.append("../../common/")
import table_manager
sys.path.append("../")
import local_datastore_populator
import info_populator
import node_stats_populator

def main():
    info_schema = json.load(open("../../config/info_schema"))
    data_schema = json.load(open("../../config/data_schema"))

    table_str_arr = info_schema.keys() + data_schema.keys()

    db_con_str = "dbname=local user=rirwin"
    con = psycopg2.connect(db_con_str);
    
    tbl_mgr = table_manager.TableManager(con, data_schema, info_schema)

    tbl_mgr.drop_tables(table_str_arr)
    tbl_mgr.establish_tables(table_str_arr)
    node_id = "404-ig-pc1"
    
    num_ins = 10
    per_sec = 0.2

    psql_lock = threading.Lock()

    # local datastore populator helper
    ldph = local_datastore_populator.LocalDatastorePopulator(con, psql_lock, tbl_mgr)

    # info population
    ip = info_populator.InfoPopulator(ldph)

    ip.ins_fake_info()
       
    cur = con.cursor();
    cur.execute("select count(*) from aggregate");
    print "Aggregate has entries", cur.fetchone()[0], "entries"
    
    # data population
    event_str_arr = []
    #event_str_arr = data_schema.keys()

    event_str_arr.append("mem_used")
    
    nsp = node_stats_populator.NodeStatsPopulator(ldph, node_id, num_ins, per_sec, event_str_arr)

    nsp.run_node_stats_main()

    for ev in event_str_arr:
        cur.execute("select count(*) from " + ev);
        print ev, "has", cur.fetchone()[0], "entries"

    cur.close()
    con.close()

if __name__ == "__main__":
    main()
