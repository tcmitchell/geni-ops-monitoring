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


import subprocess
import ConfigParser
import sys
import getopt
import subprocess
import time

def usage():
    print "pinger --outfile filename --configpath pathWithoutFile"
    sys.exit(0)

def parse_args(argv):
    out_file = ""
    config_path = ""
    source_name = ""
    try:
        opts, args = getopt.getopt(argv,"o:c:s:",["outfile=","configpath=","sourcename="])
    except getopt.GetoptError:
        usage()

    for opt, arg in opts:

        if opt in ("-o", "--outfile"):
            out_file = arg
        elif opt in ("-c", "--configpath"):
            config_path = arg
        elif opt in ("-s", "--sourcename"):
            source_name = arg
        else:
            usage()

    return [out_file, config_path, source_name]

class Pinger:

    def __init__(self, out_file, config_path, source_name):

        self.file_handle = open(out_file,'w')
        self.source_name = source_name
        config = ConfigParser.ConfigParser()
        config.read(config_path + "/ip_addresses.conf")
        self.ip_addr_dict = dict(config.items("main"))

        self.run_pings()
        self.file_handle.close()


    def run_pings(self):
        for addr_name in self.ip_addr_dict.keys():
            dst_addr = self.ip_addr_dict[addr_name]
            delay_ms = None
            try:
                delay_ms = float(subprocess.Popen(["/bin/ping", "-c3", "-w3", dst_addr], stdout=subprocess.PIPE).stdout.read().split('/')[5])
            except Exception, e:
                try:
                    delay_ms = float(subprocess.Popen(["/bin/ping", "-c3", "-w3", dst_addr], stdout=subprocess.PIPE).stdout.read().split('/')[5])
                except Exception, e:
                    delay_ms = -1
            ts = str(int(time.time()*1000000))
            self.file_handle.write("('" + self.source_name + "_to_" + addr_name + "'," + ts + "," + str(delay_ms) + ")" + "\n")
            


def main(argv):

    [out_file, config_path, source_name] = parse_args(argv)
    pinger = Pinger(out_file, config_path, source_name)


if __name__ == "__main__":
    main(sys.argv[1:])
