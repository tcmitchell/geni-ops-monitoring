#----------------------------------------------------------------------
# Copyright (c) 2014-2015 Raytheon BBN Technologies
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
import time

def usage():
    print "pinger --outfile filename --configpath pathWithoutFile"
    sys.exit(0)

def parse_args(argv):
    out_file = ""
    config_path = ""
    source_name = ""
    try:
        opts, _args = getopt.getopt(argv, "o:c:s:t:", ["outfile=", "configpath=", "sourcename=", "type="])
    except getopt.GetoptError:
        usage()

    for opt, arg in opts:

        if opt in ("-o", "--outfile"):
            out_file = arg
        elif opt in ("-c", "--configpath"):
            config_path = arg
        elif opt in ("-s", "--sourcename"):
            source_name = arg
        elif opt in ("-t", "--type"):
            ping_type = arg
        else:
            usage()

    return [out_file, config_path, source_name, ping_type]

class Pinger:

    def __init__(self, out_file, config_path, source_name, ping_type):

        self.file_handle = open(out_file, 'w')
        self.srcSite = source_name
        self.ping_type = ping_type
        config = ConfigParser.ConfigParser()
        config.read(config_path)
        self.ip_list = dict(config.items(ping_type))
        self.run_pings(self.ip_list)
        self.file_handle.close()


    def _ping(self, dst_addr):
        """
        """
        wrote_output = False
        try:
            output = (subprocess.Popen(["ping", "-c 6", dst_addr], stdout=subprocess.PIPE).stdout.read().split('/')[3])
            delay_ms = (output.split("="))[1]
        except Exception, _e:
            try:
                output = (subprocess.Popen(["ping", "-c 6", dst_addr], stdout=subprocess.PIPE).stdout.read().split('/')[3])
                delay_ms = (output.split("="))[1]
            except Exception, _e:
                delay_ms = -1
                sys.stdout.write("a")
                wrote_output = True
        return delay_ms, wrote_output

    def run_pings(self, ipList):
        output = False
        for dstSite in ipList:
            if self.srcSite == dstSite:
                # No "self" pinging
                continue

            experiment_id = self.srcSite + "_to_" + dstSite
            if self.ping_type == 'campus':
                experiment_id = experiment_id + "_campus"
            else:
                dstSiteFlag = dstSite.strip().split('-')
                srcSiteFlag = self.srcSite.strip().split('-')
                if srcSiteFlag[2] != dstSiteFlag[2]:
                    # Can't ping between hosts in different networks
                    continue

            # TODO build argument list for process pool
            dst_addr = ipList[dstSite]
            (_, tmp_output) = self._ping(dst_addr)
            if tmp_output: output = True
            # Running a second set of pings so that we eliminate the possible
            # delays seen when the first set of pings is affected by the flows
            # being set up on the OpenFlow switches.
            (delay_ms, tmp_output) = self._ping(dst_addr)
            if tmp_output: output = True
            ts = str(int(time.time() * 1000000))
            # Use a lock when writing to the result file.
            self.file_handle.write("('" + experiment_id + "'," + ts + "," + str(delay_ms) + ")" + "\n")


        # TODO create process pool - use the map() method with the argument list built above

        if output:
            print

def main(argv):

    [out_file, config_path, source_name, ping_type] = parse_args(argv)
    _pinger = Pinger(out_file, config_path, source_name, ping_type)

if __name__ == "__main__":
    main(sys.argv[1:])
