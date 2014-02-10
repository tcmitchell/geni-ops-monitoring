#!/usr/bin/python

import psycopg2
import json
import sys
from pprint import pprint as pprint

class TableManager:

    def __init__(self, con, data_schema, info_schema):
        self.con = con
        self.schema_dict = self.create_schema_dict(data_schema, info_schema)
        print "Schema loaded" 
        pprint(self.schema_dict)

    def create_schema_dict(self, data_schema, info_schema):
        schema_dict = {}
        schema_dict["units"] = {}
        if (len(dict(data_schema.items() + info_schema.items())) != len(data_schema) + len(info_schema)):
            print "Error: table namespace collision"
            return None

        # TODO id an opaque identifier that keeps metadata 
        for ds_k in data_schema.keys():
            schema_dict[ds_k] = data_schema[ds_k][:-1] # last of list is units
            # 2nd of tuple is a string of what unit type is (i.e., percent)
            schema_dict["units"][ds_k] = data_schema[ds_k][-1][1] 

        for is_k in info_schema.keys():
            schema_dict[is_k] = info_schema[is_k]

        return schema_dict

    def table_exists(self, table_str):
        exists = False
        try:
            cur = self.con.cursor()
            cur.execute("select exists(select relname from pg_class where relname='" + table_str + "')")
            exists = cur.fetchone()[0]
            cur.close()
        except Exception, e:
            print e
        return exists
    
    def get_table_col_names(self, table_str):

        col_names = []
        try:
            cur = self.con.cursor()
            cur.execute("select * from " + table_str + " LIMIT 0")
            col_names = [desc[0] for desc in cur.description]
            cur.close()
        except Exception, e:
            print e
            
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
            # TODO check if different schema
            # TODO user input for overwrite or not
            
        else:
            try:
                cur = self.con.cursor()
                print "create table " + table_str + schema_str
                cur.execute("create table " + table_str + schema_str)
                self.con.commit()
                cur.close()
            except Exception, e:
                print e

    def drop_tables(self, table_str_arr):
        for table_str in table_str_arr:
            self.drop_table(table_str)

    def drop_table(self, table_str):
        
        try:
            cur = self.con.cursor()
            cur.execute("drop table if exists " + table_str)
            self.con.commit()
            print "Dropping table", table_str
            cur.close()
        except Exception, e:
            print e

        

def translate_table_schema_to_schema_str(table_schema_dict, table_str):
        schema_str = "("

        for col_i in range(len(table_schema_dict)):
            #print table_schema_dict[col_i][0]
            #print table_schema_dict[col_i][1]
            schema_str += "\"" +table_schema_dict[col_i][0] + "\" " + table_schema_dict[col_i][1] + "," 
        
        # remove , and add )
        return schema_str[:-1] + ")"


def print_keys(dict_keys):
    for key in dict_keys:
        print key, 

def arg_parser(argv, dict_keys):
    if (len(argv) == 1):
        print "Provide at least one argument for which table(s) to be created"
        print "Example usage `python create_tables memory_util processor_util"
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
            print_keys(dict_keys)
            sys.exit(1)
        else:
            table_str_arr.append(table_str)

    return table_str_arr


def main():

    info_schema = json.load(open("../config/info_schema"))
    data_schema = json.load(open("../config/data_schema"))

    # to have a table for all event types for local store or
    # aggregator to have a table for all event types
    table_str_arr = info_schema.keys() + data_schema.keys()
    
    print table_str_arr

    # to pass in event types to create subset of all event types
    #(table_str_arr) = arg_parser(sys.argv, schema_dict.keys())

    db_con_str = "dbname=local user=rirwin"
    con = psycopg2.connect(db_con_str);
    
    tm = TableManager(con, data_schema, info_schema)
    
    tm.drop_tables(table_str_arr)
    tm.establish_tables(table_str_arr)
    

    con.close()
if __name__ == "__main__":
    main()
