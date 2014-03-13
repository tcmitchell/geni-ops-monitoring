#----------------------------------------------------------------------
# Copyright (c) 2014 Raytheon BBN Technologies
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and/or hardware specification (the "Work") to
# deal in the Work without restriction, including without limitation the
# rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Work, and to permit persons to whom the Work
# is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Work.
#
# THE WORK IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
# OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE WORK OR THE USE OR OTHER DEALINGS
# IN THE WORK.
#----------------------------------------------------------------------

import sys
import json

common_path = "../../common/"

sys.path.append(common_path)
import table_manager

def main():

    db_type = "aggregator"
    config_path = "../../config/"
    tbl_mgr = table_manager.TableManager(db_type, config_path)

    info_schema = json.load(open(config_path + "info_schema"))
    data_schema = json.load(open(config_path + "data_schema"))
    table_str_arr = info_schema.keys() + data_schema.keys()

    tbl_mgr.drop_tables(table_str_arr)
    tbl_mgr.establish_tables(table_str_arr)
   
    tbl_mgr.con.close()

if __name__ == "__main__":
    main()
