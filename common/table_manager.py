#!/usr/bin/python

import psycopg2
import json
import sys
import threading
from pprint import pprint as pprint

class TableManager:

    def __init__(self, db_name, config_path):
        self.con = self.init_conn(db_name, config_path)
        self.db_lock = threading.Lock()

        info_schema = json.load(open(config_path + "info_schema"))
        data_schema = json.load(open(config_path + "data_schema"))
        self.schema_dict = self.create_schema_dict(data_schema, info_schema)

        print "Schema loaded with keys:" 
        print self.schema_dict.keys() 
        print ""

    def init_conn(self, db_name, config_path):

        # load a 2-function package for reading database config
        sys.path.append(config_path)
        import postgres_conf_loader

        if db_name == "local":
            [database_, username_, password_, host_, port_] = postgres_conf_loader.local(config_path)
        elif db_name == "aggregator":
            [database_, username_, password_, host_, port_] = postgres_conf_loader.aggregator(config_path)
        else:
            print "No aggregator or local database selected.  Exiting\n"
            sys.exit(1)

        try:
            con = psycopg2.connect(database = database_, user = username_, password = password_, host = host_, port = port_)
        except Exception, e:
            print e, "\nCannot open a connection to database " + database_ + ". \n Exiting."
            sys.exit(1)

        return con

    def create_schema_dict(self, data_schema, info_schema):
        schema_dict = {}
        schema_dict["units"] = {}
        if (len(dict(data_schema.items() + info_schema.items())) != len(data_schema) + len(info_schema)):
            print "Error: table namespace collision"
            return None

        for ds_k in data_schema.keys():
            # last of list is units
            # 2nd of tuple is a string of what unit type is (i.e., percent)
            schema_dict[ds_k] = data_schema[ds_k][:-1] 
            schema_dict["units"][ds_k] = data_schema[ds_k][-1][1] 

        for is_k in info_schema.keys():
            schema_dict[is_k] = info_schema[is_k]

        return schema_dict

    # inserts done here to handle cursor write locking
    def insert_stmt(self, table_name, val_str):

        self.db_lock.acquire()

        try:
            cur = self.con.cursor()            
            ins_str = "insert into " + table_name + " values (" + val_str + ");";
            print ins_str
            cur.execute(ins_str);
            self.con.commit() 
            cur.close()
        except Exception, e:
            print "Trouble inserting data to " + table_name + "."
            print "val str " + val_str
            print e

        self.db_lock.release()

    def close_con(self):
        try:
            self.con.close()
        except Exception, e:
            print e, "\nCannot close connection to database."

    '''
    Not allowed in a transaction block, connection implies a database 
    TODO drop database
    def drop_database(self, dbname_str): 
        try:
            cur = self.con.cursor()
            cur.execute("drop database if exists " + dbname_str)
            self.con.commit()
            print "Dropping database", dbname_str
            cur.close()
        except Exception, e:
            print e

    def create_database(self, dbname_str):
        try:
            cur = self.con.cursor()
            cur.execute("create database " + dbname_str)
            self.con.commit()
            print "Creating database", dbname_str
            cur.close()
        except Exception, e:
            print e
    '''

    def table_exists(self, table_str):
        exists = False
        self.db_lock.acquire()
        try:
            cur = self.con.cursor()

            cur.execute("select exists(select relname from pg_class where relname='" + table_str + "')")
            exists = cur.fetchone()[0]
            cur.close()
        except Exception, e:
            print e
        self.db_lock.release()

        return exists
    
    def get_table_col_names(self, table_str):

        self.db_lock.acquire()
        col_names = []
        try:
            cur = self.con.cursor()
            cur.execute("select * from " + table_str + " LIMIT 0")
            col_names = [desc[0] for desc in cur.description]
            cur.close()
        except Exception, e:
            print e

        self.db_lock.release()
            
        return col_names

    def establish_tables(self, table_str_arr):
        for table_str in table_str_arr:
            self.establish_table(table_str)

    def establish_table(self, table_str):

        schema_str = translate_table_schema_to_schema_str(self.schema_dict[table_str], table_str)
        
        if self.table_exists(table_str):
            print "\nINFO: table " + table_str + " already exists with schema:"
            print self.get_table_col_names(table_str)
            print "Current schema_str " + schema_str
            print "Skipping creation of " + table_str + "\n"
            
        else:
            self.db_lock.acquire()
        
            try:
                cur = self.con.cursor()
                print "create table " + table_str + schema_str
                cur.execute("create table " + table_str + schema_str)
                self.con.commit()

                cur.close()
            except Exception, e:
                print e
            
            self.db_lock.release()

    def drop_tables(self, table_str_arr):
        for table_str in table_str_arr:
            self.drop_table(table_str)

    def drop_table(self, table_str):

        self.db_lock.acquire()        

        try:
            cur = self.con.cursor() 
            print "drop table if exists " + table_str
            cur.execute("drop table if exists " + table_str)
            self.con.commit()

            print "Dropping table", table_str
            cur.close()
        except Exception, e:
            print e, table_str

        self.db_lock.release()

def translate_table_schema_to_schema_str(table_schema_dict, table_str):
        schema_str = "("

        for col_i in range(len(table_schema_dict)):
            schema_str += "\"" +table_schema_dict[col_i][0] + "\" " + table_schema_dict[col_i][1] + "," 
        
        # remove , and add )
        return schema_str[:-1] + ")"


# used only if arguments passed to program
# gets each argument as a table name
def arg_parser(argv, dict_keys):
    if (len(argv) == 1):
        sys.exit(1)

    table_str_arr = []

    for arg in argv[1:]:
        
        try:
            table_str = str(arg)
        except ValueError:
            print "Not a string."
            sys.exit(1)
        if table_str not in dict_keys:
            print "Argument " + arg + " converted to string " + table_str + " was not found in schema dictionary keys:"
            print dict_keys.keys()
            sys.exit(1)
        else:
            table_str_arr.append(table_str)

    return table_str_arr


def main():

    config_path = "../config/"

    print "Running table_manager manually"
    local_or_agg = raw_input("Do you want to connect to the local database or aggregator database (Enter L or A)? ")

    if local_or_agg == 'l' or local_or_agg == 'L':
        db_name = "local"
    elif local_or_agg == 'a' or local_or_agg == 'A':
        db_name = "aggregator"
    else:
        print local_or_agg + " is not a valid response.  Enter L or A"
        sys.exit(1)


    tm = TableManager(db_name, config_path)

    # get all tables all event types (data_schema) and info types
    # (info_schema) for local datastore database or aggregator
    # database to have a table for all event types

    if (len(sys.argv) > 1):
        table_str_arr = arg_parser(sys.argv,info_schema.keys() + data_schema.keys())
    else:
        print "\nNo tables passed as arguments, selecting all tables."
        print "Next time, provide at least one argument for which "
        print "table(s) to be reset"
        print "Example usage `python table_manager.py mem_used cpu_util"
        info_schema = json.load(open(config_path + "info_schema"))
        data_schema = json.load(open(config_path + "data_schema"))
        table_str_arr = info_schema.keys() + data_schema.keys()

    clear_tables = raw_input("\nDo you want to reset the following tables from database " + db_name + ": \n\n" + str(table_str_arr) + " \n\n (Enter y or n)? ")
    if clear_tables == 'y' or clear_tables == 'Y':
        tm.drop_tables(table_str_arr)
        tm.establish_tables(table_str_arr)
    elif clear_tables == 'n' or clear_tables == 'N':
        print "Not reseting tables"
    else:
        print clear_tables + " is not a valid response.  y or n"

    tm.close_con();

if __name__ == "__main__":

    main()
