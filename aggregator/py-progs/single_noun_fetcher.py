 #!/usr/bin/python

import psycopg2
import threading
import time 
import json_receiver
import sys
import requests

# lock of the conn and cur usage by this program
# psql has locks for what would be concurrent psql accesses
# from other program
psql_lock = threading.Lock() 

sys.path.append("../../config")
import db_schema_config
db_schema = db_schema_config.get_schema_dict()

class SingleNounFetcherThread(threading.Thread):

    def __init__(self, con, threadID, thread_name, local_url_noun, table_str, initial_time, sleep_period_sec):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.thread_name = thread_name
  
        self.local_url_noun = local_url_noun
        self.insert_base_str = "INSERT INTO " + table_str + " VALUES"
        self.sleep_period_sec = sleep_period_sec
        self.table_str = table_str
        self.counter = 0
        self.time_of_last_update = initial_time
        self.schema = db_schema[table_str]
        self.con = con

    def run(self):

        print "Starting " + self.name

        thread_main(self)

        print "Exiting " + self.name

    def poll_datastore(self):

        payload = {'since':self.time_of_last_update}
        resp = requests.get(self.local_url_noun,params=payload)
        
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

        psql_lock.acquire()

        cur = self.con.cursor()
        cur.execute(ins_str) # todo try execption block
        self.con.commit() 
        cur.close()

        psql_lock.release()

        print "Committed"

    def thread_sleep(self):
        time.sleep(self.sleep_period_sec)

# thread main outside of thread class, is this a good idea? 
def thread_main(snft): # snft = SingleNounFetcherThread
    
    while (True): 

        # poll datastore
        json_text = snft.poll_datastore()

        # convert response to json
        (r_code, rows, time) = json_receiver.json_to_psql(json_text, snft.table_str, snft.thread_name)

        print "Received " + str(len(rows)) + " updates"

        if len(rows) > 0:
            # if any new values update latest time
            snft.time_of_last_update = time

            # insert into database
            snft.insert_query(rows)

        snft.counter = snft.counter + 1
    
        if(snft.counter) > 100:
            break; # Exits loop and thread_main()
        else: 
            snft.thread_sleep();
        
       
# how to unit test this? 
def main(): 

    # should all threads share a connection, I think not
    con = psycopg2.connect("dbname=aggregator user=rirwin")
    table_str = "memory_util"
    thread_type_index = 0
    total_thread_index = 0
    thread_str = table_str + str(thread_type_index)
    url_noun="http://127.0.0.1:5000/" + table_str + "/"
    sleep_period_sec = 3

    create_table(con, table_str);
    now_sec_epoch = time.time()/2 # need to handle null results
    
    threads = {}
    threads[table_str] = SingleNounFetcherThread(con, total_thread_index, thread_str, url_noun, table_str, now_sec_epoch, sleep_period_sec)


    threads[table_str].start()

    print "Exiting main thread"



def create_table(con, table_str):
    
    cur = con.cursor()
    cur.execute("DROP TABLE IF EXISTS " + table_str + ";")
    cur.execute("CREATE TABLE " + table_str + db_schema[table_str]);
    con.commit() 

    cur.close()

if __name__ == "__main__":
    main()
