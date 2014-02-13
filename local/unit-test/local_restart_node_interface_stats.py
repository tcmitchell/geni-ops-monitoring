import sys
import json
import psycopg2

local_path = "../"
config_path = "../../config/"
common_path = "../../common/"

sys.path.append(local_path)
sys.path.append(config_path)
sys.path.append(common_path)
import table_manager
import info_populator
import stats_populator
import postgres_conf_loader

def main():
    info_schema = json.load(open(config_path + "info_schema"))
    data_schema = json.load(open(config_path + "data_schema"))

    table_str_arr = info_schema.keys() + data_schema.keys()
    
    [database_, username_, password_, host_, port_] = postgres_conf_loader.main(config_path)

    con = psycopg2.connect(database = database_, user = username_, password = password_, host = host_, port = port_)

    tbl_mgr = table_manager.TableManager(con, data_schema, info_schema)

    #tbl_mgr.drop_db(database_)
    #tbl_mgr.establish_db(database_)
    tbl_mgr.drop_tables(table_str_arr)
    tbl_mgr.establish_tables(table_str_arr)
    node_id = "404-ig-pc1"
    interface_id = "404-ig-pc1:eth0"
    num_ins = 10
    per_sec = 0.2


    # info population
    ip = info_populator.InfoPopulator(tbl_mgr)

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
    

    node_sp = stats_populator.StatsPopulator(tbl_mgr, node_id, num_ins, per_sec, node_event_str_arr)


    interface_sp = stats_populator.StatsPopulator(tbl_mgr, interface_id, num_ins, per_sec, interface_event_str_arr)

    # start threads
    node_sp.start()
    interface_sp.start()

    threads = []
    threads.append(node_sp)
    threads.append(interface_sp)

    # join all threads
    for t in threads:
        t.join()

    for ev in (node_event_str_arr + interface_event_str_arr):
        cur.execute("select * from " + ev + " limit 1");
        print ev, "has this entry:\n", cur.fetchone()

    cur.close()
    con.close()

if __name__ == "__main__":
    main()
