 #!/usr/bin/python

#import psycopg2
import threading
import time 

# lock of the conn and cur usage by this program
# psql has locks for what would be concurrent psql accesses
# from other program
psql_lock = threading.Lock() 
conn = None
cur = None

class DataFetcherThread(threading.Thread):

    def __init__(self, threadID, name, datastore_url, sleep_period_sec):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.counter = 0
        self.datastore_url = datastore_url
        self.insert_base_str = "INSERT INTO TABLE "
        self.sleep_period_sec = sleep_period_sec
        self.schema = ""; # read from config file containing json-schema?

    def run(self):
        print "Starting " + self.name

        thread_main(self)
        
        print "Exiting " + self.name

    def poll_datastore(self):
        self.counter = self.counter + 1
        response = "response = " + self.name + " " + str(self.counter)
        return response

    def transform_response(self, response):
        values = "(transformed to values from " + self.datastore_url + " " + response + ")"
        return values

    def insert_query(self, query_str):

        psql_lock.acquire()

        print "INSERT_QUERY " + query_str
        #cur.execute(Above)
        #conn.commit()
        time.sleep(1) # simulating delay, test locking
        print "Committed"

        psql_lock.release()
        
def thread_main(dft): # dft = DataFetcher
    
    while True: 

        # poll datastore
        response = dft.poll_datastore()
        values = dft.transform_response(response)
        insert_str = dft.insert_base_str + values + ";"
            
        dft.insert_query(insert_str)
            
        if(dft.counter) > 5:
            break; # Exits loop and thread_main
        else: 
            time.sleep(dft.sleep_period_sec);
        
def main(): # args

    # some config file?

    #[conn, cur] = init_conn("rirwin","rirwin") # args
    #create_table(conn, cur, "test_py");

    thread1 = DataFetcherThread(1, "Thread-1", "datastore_one_url", 0.5)
    thread2 = DataFetcherThread(2, "Thread-2", "datastore_two_url", 0.5)

    thread1.start()
    thread2.start()

    print "Exiting main thread"

    #cur.close()
    #conn.close()


def init_conn(dbname, username):
    conn = psycopg2.connect("dbname=rirwin user=rirwin")
    cur = conn.cursor()
    
    return (conn, cur)

def create_table(conn, cur, tablename):
    cur.execute("DROP TABLE IF EXISTS test_py;")
    cur.execute(create_schema_str);
    cur.execute(insert_packet_str);
    conn.commit(); # must have commit, otw others cannot query

if __name__ == "__main__":
    main()
