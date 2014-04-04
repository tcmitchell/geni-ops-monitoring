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
import json
import urllib2
import ConfigParser

class OpsconfigLoader:
    def __init__(self, config_path):

        config = ConfigParser.ConfigParser()
        config.read(config_path + "/local_datastore_operator.conf")
        self.config_store_url = config.get("main", "configstoreurl")
      
        try:
            config_json = json.load(urllib2.urlopen(self.config_store_url, timeout=0.5))
        except:
            print "Cannot reach the config local datastore at ", self.config_store_url
            # Read from local copy of response
            # cannot open the configuration from the web, read default copy
            try:
                self.config_json = json.load(open(config_path + "../schema/examples/opsconfig/geni-prod.json"))
                print "reading local copy at " + config_path + "../schema/examples/opsconfig/geni-prod.json"
            except:
                print "cannot load json file from schema examples"

    def get_event_types(self):
        
        opsconfig = self.config_json
        
        event_types = {}
        event_types["node"] = []
        event_types["interface"] = []

        # node event types
        for ev_i in opsconfig["events"]["node"]:
            event_types["node"].append(ev_i["name"])

        # interface event types
        for ev_i in opsconfig["events"]["interface"]:
            event_types["interface"].append(ev_i["name"])

        return event_types


    def get_data_schema(self):

        opsconfig = self.config_json
        data_schema = {}

        # node event types 
        # add ops_ to avoid namespace collision with database (i.e.,
        # user not allowed)
        for ev_i in opsconfig["events"]["node"]:
            data_schema["ops_"+ev_i["name"]] = [["id",ev_i["id"]],["ts",ev_i["ts"]],["v",ev_i["v"]],["units",ev_i["units"]]]

        # interface event types
        for ev_i in opsconfig["events"]["interface"]:
            data_schema["ops_"+ev_i["name"]] = [["id",ev_i["id"]],["ts",ev_i["ts"]],["v",ev_i["v"]],["units",ev_i["units"]]]
        
        return data_schema


    def get_info_schema(self):

        opsconfig = self.config_json
        info_schema = {}

        # info schema is json-formatted array
        # add ops_ to avoid namespace collision with database (i.e.,
        # user not allowed)
        for info_i in opsconfig["info"]:
            info_schema["ops_"+info_i["name"]] = info_i["db_schema"]

        return info_schema
