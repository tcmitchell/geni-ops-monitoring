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
import os

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
            self.config_json = json.loads(resp.content)

        except Exception, e:
            self.logger.warning("Cannot reach the config local datastore at ", self.config_store_url)
            self.logger.warning(e)
            self.load_from_local_config()


    def load_from_local_config(self):
        self.config_json = json.load(open(os.path.join(self.config_path, "opsconfig.json")))


    def get_event_types(self):

        opsconfig = self.config_json

        event_types = dict()


        for obj_type in ("node", "interface", "interfacevlan", "experiment", "aggregate"):
            event_types[obj_type] = list()
            for ev_i in opsconfig["events"][obj_type]:
                event_types[obj_type].append(ev_i["name"])

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
        data_schema = dict()

        # add ops_ to avoid namespace collision with database (i.e.,
        # user not allowed)
        for obj_type in ("node", "interface", "interfacevlan", "experiment", "aggregate"):
            for ev_i in opsconfig["events"][obj_type]:
                data_schema["ops_" + obj_type + "_" + ev_i["name"]] = [["id", ev_i["id"]],
                                                                       ["ts", ev_i["ts"]],
                                                                       ["v", ev_i["v"]],
                                                                       ["units", ev_i["units"]]
                                                                       ]


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
            info_schema["ops_" + info_i["name"]] = info_i["db_schema"]

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
        The dependencies object is a dictionary where the keys are the table names and the values are sets.
        These sets contain the names of the tables that the table identified by the key, is dependent upon.
        :return: the DB information tables dependencies. 
        """
        opsconfig = self.config_json
        info_dep = {}

        # info schema is json-formatted array
        # add ops_ to avoid namespace collision with database (i.e.,
        # user not allowed)
        for info_i in opsconfig["info"]:
            info_dep["ops_" + info_i["name"]] = set(info_i["dependencies"])

        return info_dep

    def get_obsolete_info_dependencies(self):
        """
        Method to get the obsolete DB information tables dependencies.
        The dependencies object is a dictionary where the keys are the obsolete
        table names and the values are sets. These sets contain the names of
        the tables (obsolete and valid) that the obsolete table identified by the key,
        was dependent upon.
        :return: the DB information tables dependencies.
        """
        info_dep = dict()
        for info_i in self.config_json["obsolete"]["info"]:
            info_dep["ops_" + info_i["name"]] = set(info_i["dependencies"])

        return info_dep

    def get_obsolete_data_table_names(self):
        """
        Method to get the obsolete DB data tables names.
        The returned value is a list of the obsolete data tables names.
        :return: the obsolete DB data tables names.
        """
        obsolete_data = list()

        # node event types
        # add ops_ to avoid namespace collision with database (i.e.,
        # user not allowed)
        for obj_type in ("node", "interface", "interfacevlan", "experiment", "aggregate"):
            for ev_i in self.config_json["obsolete"]["events"][obj_type]:
                obsolete_data.append("ops_" + obj_type + "_" + ev_i["name"])


        return obsolete_data

