#!/usr/bin/python

import psycopg2
import time
import psutil
import sys

sys.path.append("../../config")
import db_schema_config

# TODO add locking from threading in case multiple LocalStorePopulators

# TODO make class LocalStorePopulator for this class to inherit
# Intent is for each table to have its own object getting data
class LocalStoreMemoryPopulator:
    def __init__(self, con, aggregate_id, resource_id, num_inserts, sleep_period_sec, table_str):
        self.con = con
        self.aggregate_id = aggregate_id
        self.resource_id = resource_id
        self.num_inserts = num_inserts
        self.sleep_period_sec = sleep_period_sec
        self.table_str = table_str
        self.table_schema = db_schema_config.get_schema_for_type(table_str)

    def translate_psql_table_schema(self):
        
        schema_str = "("
        for col_i in range(len(self.table_schema)):
            schema_str = schema_str + self.table_schema[col_i][0] + " " + self.table_schema[col_i][1] + "," 
        
        # remove , and add ), makes a smug face [:-1]
        return schema_str[:-1] + ")"

    def run_inserts(self):

        for i in range(self.num_inserts):

            time_sec_epoch = time.time()
            percent_mem_used = self.get_mem_util_percent()

            ins_str = "INSERT INTO memory_util VALUES ('" + self.aggregate_id + "', '" + self.resource_id + "'," + str(time_sec_epoch) + "," + str(percent_mem_used) + ");" 
            cur = self.con.cursor()            
            cur.execute(ins_str)
            self.con.commit()
            cur.close()

            time.sleep(self.sleep_period_sec)    

    def establish_table(self):
        
        # class functions should not be called in constructor
        table_schema_str = self.translate_psql_table_schema();

        # should this be in try catch?
        cur = self.con.cursor()
        
        try:
            cur.execute("create table if not exists " + self.table_str + " " + table_schema_str);
            self.con.commit(); 
        except psycopg2.Error as e:
            print e
        
        cur = self.con.cursor()

    def get_mem_util_percent(self):
        # despite being called virtual, this is physical memory
        mem = psutil.virtual_memory() 
        return mem.percent

def arg_parser(argv):
    if (len(argv) != 3):
        print "Provide exactly two args: (1) for num inserts, (2) for period between inserts in seconds"
        sys.exit(1)

    num_ins = 0

    try:
        num_ins = int(argv[1])
    except ValueError:
        print "Not a postive int. Provide number of inserts for run of program."
        sys.exit(1)

    per_sec = 0

    try:
        per_sec = float(argv[2])
    except ValueError:
        print "Not a postive float. Provide period of time in seconds between inserts."
        sys.exit(1)

    if (per_sec < 0 or num_ins < 0):
        print "Both numeric args should be positive"
        sys.exit(1)

    return num_ins, per_sec

def main():

    # 404 is not found and the area code in atlanta #TheGoalIsGEC19
    aggregate_id="404-ig" 
    resource_id="compute_node_1"
    table_name = "memory_util"

    (num_ins, per_sec) = arg_parser(sys.argv)

    con = psycopg2.connect("dbname=local user=rirwin");

    lsmp = LocalStoreMemoryPopulator(con, aggregate_id, resource_id, num_ins, per_sec, table_name)
    lsmp.establish_table()
    lsmp.run_inserts()
        

    cur = con.cursor();
    cur.execute("select count(*) from memory_util;");
    print "num entries", cur.fetchone()[0]

    cur.close();
    con.close();

if __name__ == "__main__":
    main()
