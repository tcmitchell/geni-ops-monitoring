#!/usr/bin/python
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
import os
import getopt

sys.path.append("../common/")
import table_manager
import opsconfig_loader

def usage():
    print "use -i, -p, -h, -u, args only"
    sys.exit(0)

def parse_args(argv):
    if argv == []:
        usage()

    identity_file_full_path = ""
    port = ""
    host = ""
    user = ""
    try:
        opts, args = getopt.getopt(argv,"i:p:h:u:",["full-key-file-path=","port=","host=","user="])
    except getopt.GetoptError:
        usage()

    for opt, arg in opts:
        if opt in ("-i", "--full-key-file-path"):
            identity_file_full_path = arg
        elif opt in ("-p", "--port"):
            port = arg
        elif opt in ("-h", "--host"):
            host = arg
        elif opt in ("-u", "--user"):
            user = arg
        else:
            usage()

    return [identity_file_full_path, port, host, user]


db_type = "local"
config_path = "../config/"
debug = False

tbl_mgr = table_manager.TableManager(db_type, config_path, debug)
tbl_mgr.poll_config_store()

ocl = opsconfig_loader.OpsconfigLoader(config_path)

experiment_event_types = ocl.get_event_types()["experiment"]


filename = "raw_rows"

[key_path, port, host, user] = parse_args(sys.argv[1:])

os.system("ssh -i " + key_path + " " + user + "@" + host + " -p " + port + " \"rm -f " + filename + " && python pinger.py -o " + filename  + " -c . -s gpo-ig\"")
os.system("scp -i " + key_path + " -P " + port + " " + user + "@" + host + ":" + filename + " ./")

file_handle = open(filename, 'r')
val_str = ""
for line in file_handle:
    val_str += line + ","

table_str = "ops_experiment_" + experiment_event_types[0]

tbl_mgr.insert_stmt(table_str, val_str[:-1])
