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
import json
import ConfigParser
import requests
import logger

class OpsconfigLoader:

    def __init__(self, config_path):
        self.config_path = config_path
        self.load_from_local_config()
        self.logger = logger.get_logger(config_path)


    def load_from_network_config(self):
        config = ConfigParser.ConfigParser()
        config.read(self.config_path + "/collector_operator.conf")
        self.config_store_url = config.get("main", "configstoreurl")
        self.cert_path = config.get("main", "certificatepath")

        try:
            resp = requests.get(self.config_store_url, verify=False, cert=self.cert_path)
            self.config_json= json.loads(resp.content)

        except Exception, e:
            self.logger.warning("Cannot reach the config local datastore at ", self.config_store_url)
            self.logger.warning(e)
            self.load_from_local_config()


    def load_from_local_config(self):       
        self.config_json = json.load(open(self.config_path + "opsconfig.json"))


    def get_event_types(self):
        
        opsconfig = self.config_json
        
        event_types = {}
        event_types["node"] = []
        event_types["interface"] = []
        event_types["interfacevlan"] = []
        event_types["experiment"] = []
        event_types["aggregate"] = []

        # node event types
        for ev_i in opsconfig["events"]["node"]:
            event_types["node"].append(ev_i["name"])

        # interface event types
        for ev_i in opsconfig["events"]["interface"]:
            event_types["interface"].append(ev_i["name"])

        # interfacevlan event types
        for ev_i in opsconfig["events"]["interfacevlan"]:
            event_types["interfacevlan"].append(ev_i["name"])

        # experiment event types
        for ev_i in opsconfig["events"]["experiment"]:
            event_types["experiment"].append(ev_i["name"])

        # aggregate event types
        for ev_i in opsconfig["events"]["aggregate"]:
            event_types["aggregate"].append(ev_i["name"])

        return event_types


    def get_data_schema(self):
        """
        Method to get the DB data tables schema.
        The schema is a dictionary where the keys are the table names and the values are lists.
        These lists contain lists each with 2 objects: column name, column type. There is 
        one extra list in the value list, which contains the "units" string and the type of the
        units for that table.
        :return: the DB tables data schema. 
        """

        opsconfig = self.config_json
        data_schema = {}

        # node event types 
        # add ops_ to avoid namespace collision with database (i.e.,
        # user not allowed)
        for ev_i in opsconfig["events"]["node"]:
            data_schema["ops_node_"+ev_i["name"]] = [["id",ev_i["id"]],["ts",ev_i["ts"]],["v",ev_i["v"]],["units",ev_i["units"]]]

        # interface event types
        for ev_i in opsconfig["events"]["interface"]:
            data_schema["ops_interface_"+ev_i["name"]] = [["id",ev_i["id"]],["ts",ev_i["ts"]],["v",ev_i["v"]],["units",ev_i["units"]]]

        # interfacevlan event types
        for ev_i in opsconfig["events"]["interfacevlan"]:
            data_schema["ops_interfacevlan_"+ev_i["name"]] = [["id",ev_i["id"]],["ts",ev_i["ts"]],["v",ev_i["v"]],["units",ev_i["units"]]]
        
        # experiment event types
        for ev_i in opsconfig["events"]["experiment"]:
            data_schema["ops_experiment_"+ev_i["name"]] = [["id",ev_i["id"]],["ts",ev_i["ts"]],["v",ev_i["v"]],["units",ev_i["units"]]]
        
        # aggregate event types
        for ev_i in opsconfig["events"]["aggregate"]:
            data_schema["ops_aggregate_"+ev_i["name"]] = [["id",ev_i["id"]],["ts",ev_i["ts"]],["v",ev_i["v"]],["units",ev_i["units"]]]
        
        return data_schema


    def get_info_schema(self):
        """
        Method to get the DB information tables schema.
        The schema is a dictionary where the keys are the table names and the values are lists.
        These lists contain lists each with 3 objects: column name, column type and whether the column is required.
        :return: the DB information tables schema. 
        """

        opsconfig = self.config_json
        info_schema = {}

        # info schema is json-formatted array
        # add ops_ to avoid namespace collision with database (i.e.,
        # user not allowed)
        for info_i in opsconfig["info"]:
            info_schema["ops_"+info_i["name"]] = info_i["db_schema"]

        return info_schema

    def get_info_constraints(self):
        """
        Method to get the DB information tables constraints.
        The constraints object is a dictionary where the keys are the table names and the values are lists.
        These lists contain lists each with 2 objects: a constraint format string and a list of arguments 
        for the format (i.e. column or table names).
        :return: the DB information tables constraints. 
        """
        opsconfig = self.config_json
        info_constr = {}

        # info schema is json-formatted array
        # add ops_ to avoid namespace collision with database (i.e.,
        # user not allowed)
        for info_i in opsconfig["info"]:
            info_constr["ops_" + info_i["name"]] = info_i["constraints"]

        return info_constr

    def get_info_dependencies(self):
        """
        Method to get the DB information tables dependencies.
        The dependencies object is a dictionary where the keys are the table names and the values are lists.
        These lists contain the names of the tables the table identified by the key, is dependent upon.
        :return: the DB information tables dependencies. 
        """
        opsconfig = self.config_json
        info_dep = {}

        # info schema is json-formatted array
        # add ops_ to avoid namespace collision with database (i.e.,
        # user not allowed)
        for info_i in opsconfig["info"]:
            info_dep["ops_" + info_i["name"]] = info_i["dependencies"]

        return info_dep
