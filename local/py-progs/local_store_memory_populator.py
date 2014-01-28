#!/usr/bin/python

import psycopg2
import time
import psutil
import sys

sys.path.append("../../config")
import db_schema_config

db_schema = db_schema_config.get_schema_dict()
# 404 is not found and the area code in atlanta #TheGoalIsGEC19
aggregate_id="404-ig" 
resource_id="compute_node_1"


def get_mem_util_percent():
    # despite being called virtual, this is physical memory
    mem = psutil.virtual_memory() 
    return mem.percent

def run_inserts(con, num_ins, per_sec):
    
    cur = con.cursor()
    
    for i in range(num_ins):

        time_sec_epoch = time.time()
        percent_mem_used = get_mem_util_percent()

        ins_str = "INSERT INTO memory_util VALUES ('" + aggregate_id + "', '" + resource_id + "'," + str(time_sec_epoch) + "," + str(percent_mem_used) + ");" 

        cur.execute(ins_str)
        con.commit()

        time.sleep(per_sec)    

    cur.close()


def main():
    if (len(sys.argv) != 3):
        print "Provide exactly two args: (1) for num inserts, (2) for period between inserts in seconds"
        sys.exit(1)

    num_ins = 0

    try:
        num_ins = int(sys.argv[1])
    except ValueError:
        print "Not a postive int. Provide number of inserts for run of program."
        sys.exit(1)


    per_sec = 0

    try:
        per_sec = float(sys.argv[2])
    except ValueError:
        print "Not a postive float. Provide period of time in seconds between inserts."
        sys.exit(1)

    if (per_sec < 0 or num_ins < 0):
        print "Both numeric args should be positive"
        sys.exit(1)

    con = psycopg2.connect("dbname=local user=rirwin");
    cur = con.cursor();
    table_name = "memory_util"

    cur.execute("drop table if exists " + table_name + ";");
    con.commit(); 
   
    cur.execute("create table if not exists " + table_name + db_schema[table_name]);
    con.commit(); 

    run_inserts(con, num_ins, per_sec)

    cur.execute("select count(*) from memory_util;");
    print cur.fetchone()[0]

    cur.close();
    con.close();

if __name__ == "__main__":
    main()
