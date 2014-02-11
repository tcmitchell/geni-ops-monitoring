import sys
import json
import psycopg2
import threading

sys.path.append("../../common/")
import table_manager
sys.path.append("../")
import local_datastore_populator
import info_populator
import stats_populator

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
    interface_id = "404-ig-pc1:eth0"
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
    node_event_str_arr = []
    node_event_str_arr.append("mem_used")
    node_event_str_arr.append("cpu_util")
    node_event_str_arr.append("disk_part_max_used")
    node_event_str_arr.append("swap_free")

    interface_event_str_arr = []
    interface_event_str_arr.append("ctrl_net_rx_bytes")
    interface_event_str_arr.append("ctrl_net_tx_bytes")

    print node_event_str_arr + interface_event_str_arr

    node_sp = stats_populator.StatsPopulator(ldph, node_id, num_ins, per_sec, node_event_str_arr)

    node_sp.run_stats_main()

    interface_sp = stats_populator.StatsPopulator(ldph, interface_id, num_ins, per_sec, interface_event_str_arr)

    interface_sp.run_stats_main()



    for ev in (node_event_str_arr + interface_event_str_arr):
        cur.execute("select * from " + ev + " limit 1");
        print ev, "has this entry:\n", cur.fetchone()

    cur.close()
    con.close()

if __name__ == "__main__":
    main()
