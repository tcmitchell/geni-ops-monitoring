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
