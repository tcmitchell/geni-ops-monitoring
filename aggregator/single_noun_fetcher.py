 #!/usr/bin/python

import psycopg2
import threading
import time 
import json
import json_receiver
import sys
import requests


# schema only used for unit test
from sys import path as sys_path 
sys_path.append("../common/db-tools/")
import table_manager as TableManager

class SingleNounFetcherThread(threading.Thread):

    def __init__(self, con, threadID, thread_name, local_url_noun, table_str, initial_time, sleep_period_sec, schema_dict, psql_lock):
        threading.Thread.__init__(self)
        self.con = con 
        self.threadID = threadID
        self.thread_name = thread_name
        self.schema_dict = schema_dict
        self.local_url_noun = local_url_noun
        self.insert_base_str = "INSERT INTO " + table_str + " VALUES"
        self.sleep_period_sec = sleep_period_sec
        self.table_str = table_str
        self.psql_lock = psql_lock
        self.counter = 0
        self.time_of_last_update = int(initial_time)

        self.table_manager = TableManager.TableManager(self.con, schema_dict)
        self.table_manager.establish_table(table_str)

        self.json_receiver = json_receiver.JsonReceiver(schema_dict)


    def run(self):

        print "Starting " + self.name

        thread_main(self)

        print "Exiting " + self.name

    def poll_datastore(self):
        
        req_time = int(time.time()*1000000)
        payload = {'event_type':self.table_str,
                   'ts':'gte='+str(self.time_of_last_update)}
        resp = requests.get(self.local_url_noun,params=payload)
        
        if resp:
            self.time_of_last_update = req_time
        
        # need to handle response codes
        return resp.content

    def insert_query(self, rows):
        num_rows = len(rows)
        ins_str = self.insert_base_str

        for i in range(num_rows-1):
            ins_str = ins_str + rows[i]
            ins_str = ins_str + ","
        ins_str = ins_str + rows[num_rows-1] + ";"
         
        print "Insert Query = ", ins_str

        self.psql_lock.acquire()

        cur = self.con.cursor()
        cur.execute(ins_str) # todo try execption block
        self.con.commit() 
        cur.close()

        self.psql_lock.release()

        print "Committed"

    def thread_sleep(self):
        time.sleep(self.sleep_period_sec)

# thread main outside of thread class, is this a good idea? 
def thread_main(snft): # snft = SingleNounFetcherThread
    
    while (True): 

        # poll datastore
        json_text = snft.poll_datastore()

        # convert response to json
        (r_code, rows) = snft.json_receiver.json_to_psql(json_text, snft.table_str, snft.thread_name)

        print "Received " + str(len(rows)) + " updates"

        if len(rows) > 0:
            
            # insert into database
            snft.insert_query(rows)

        snft.counter = snft.counter + 1
    
        if(snft.counter) > 3:
            break; # Exits loop and thread_main()
        else: 
            snft.thread_sleep();
        
def main(): 

    con = psycopg2.connect("dbname=aggregator user=rirwin")
    table_str = "memory_util"
    thread_type_index = 0
    total_thread_index = 0
    thread_str = table_str + str(thread_type_index)
    url_noun="http://127.0.0.1:5000/data/"
    sleep_period_sec = 1

    micro_sec_epoch = 0 
    #micro_sec_epoch = int(time.time()*1000000)

    # Dense lines to get schema_dict
    db_templates = json.load(open("../config/db_templates"))
    event_types = json.load(open("../config/event_types"))
    schema_dict = {}
    for ev_t in event_types.keys():
        schema_dict[ev_t] = db_templates[event_types[ev_t]["db_template"]] + [["v",event_types[ev_t]["v_col_type"]]]
    # end dense lines to get schema_dict

    # lock of the conn and cur usage by this program
    # psql has locks for what would be concurrent psql accesses
    # from other program
    psql_lock = threading.Lock() 

    threads = {}
    threads[table_str] = SingleNounFetcherThread(con, total_thread_index, thread_str, url_noun, table_str, micro_sec_epoch, sleep_period_sec, schema_dict, psql_lock)

    threads[table_str].start()

    print "Exiting main thread"


if __name__ == "__main__":
    main()
