#!/usr/bin/python

import psycopg2

import sys
sys.path.append("../config")
import schema_config

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
        print str(arg)
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

def table_exists(con, table_str):
    exists = False
    try:
        cur = con.cursor()
        cur.execute("select exists(select relname from pg_class where relname='" + table_str + "')")
        exists = cur.fetchone()[0]
        print exists
        cur.close()
    except psycopg2.Error as e:
        print e
    return exists
    
def get_table_col_names(con, table_str):

    col_names = []
    try:
        cur = con.cursor()
        cur.execute("select * from " + table_str + " LIMIT 0")
        col_names = [desc[0] for desc in cur.description]
        cur.close()
    except psycopg2.Error as e:
        print e

    return col_names

def establish_tables(con, schema_dict, table_str_arr):

    for table_str in table_str_arr:
        schema_str = translate_table_schema_to_schema_str(schema_dict[table_str],table_str)

        if table_exists(con, table_str):
            print "WARNING: table " + table_str + " already exists with schema:"
            print get_table_col_names(con, table_str)
            print "schema_str " + schema_str
            print "Skipping creation of " + table_str
            # TODO check if different schema
            # TODO user input for overwrite or not
            
        else:
            try:
                cur = con.cursor()
                cur.execute("create table " + table_str + schema_str)
                con.commit()
                cur.close()
            except psycopg2.Error as e:
                print e

def translate_table_schema_to_schema_str(table_schema, table_str):
        schema_str = "("
        for col_i in range(len(table_schema)):
            schema_str = schema_str + table_schema[col_i][0] + " " + table_schema[col_i][1] + "," 
        
        # remove , and add )
        return schema_str[:-1] + ")"

def main():

    schema_dict = schema_config.get_schema()
    (table_str_arr) = arg_parser(sys.argv, schema_dict.keys())

    # TODO make a connection string as an argument
    con_str = "dbname=local user=rirwin"
    con = psycopg2.connect(con_str);

    establish_tables(con, schema_dict, table_str_arr)

    con.close();

if __name__ == "__main__":
    main()
