import sys
import json
import psycopg2

common_path = "../../common/"

sys.path.append(common_path)
import table_manager

def main():

    db_name = "local"
    config_path = "../../config/"
    tbl_mgr = table_manager.TableManager(db_name, config_path)

    info_schema = json.load(open(config_path + "info_schema"))
    data_schema = json.load(open(config_path + "data_schema"))
    table_str_arr = info_schema.keys() + data_schema.keys()

    tbl_mgr.drop_tables(table_str_arr)
    tbl_mgr.establish_tables(table_str_arr)
   
    tbl_mgr.con.close()

if __name__ == "__main__":
    main()
