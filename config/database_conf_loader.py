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

import ConfigParser

class DbConfigLoader():
    def __init__(self, config_path, dbconfigtype):
        """
        Construct a configuration reader and parse in the appropriate configuration file.
        :param config_path: the path to the ops-monitoring configuration folder.
        :param dbconfigtype: either "local" or "collector"
        """
        import sys
        import logger
        self.__dbconfigtype = dbconfigtype
        if dbconfigtype == "local":
            self.config = self.generic_config_parser(config_path, True)
        elif dbconfigtype == "collector":
            self.config = self.generic_config_parser(config_path, False)
        else:
            logger.get_logger(config_path).critical("No collector or local database selected.  Exiting\n")
            sys.exit(1)
        self._dbtype = self.config.get("main", "dbtype")

    def generic_config_parser(self, config_path, local):
        """
        Method to create a ConfigParser object and parse in the appropriate configuration file.
        :param config_path: the path to the ops-monitoring configuration folder.
        :param local: boolean indicating whether the local datastore configuration file will be read in or the collector configuration file.
        :return: a ConfigParser object loaded with the configuration parameters.
        """
        config = ConfigParser.ConfigParser()
        if local:
            filename = config_path + "/local_datastore_operator.conf"
        else:
            filename = config_path + "/collector_operator.conf"
        config.read(filename)
        return config

    def get_dbType(self):
        """
        Method to get the DB engine type as specified by the configuration.
        """
        return self._dbtype

    def get_aging_timeout(self):
        return int(self.config.get("main", "aging_timeout"))

    def get_purge_period(self):
        return int(self.config.get("main", "purge_period"))

    def get_default_metrics_period(self):
        if self.__dbconfigtype != "local":
            return 0
        else:
            return int(self.config.get("main", "default_metrics_period"))


    def get_db_parameters(self):
        """
        Method to get the database parameters values for a dbengine kind of database and for a dbconfigtype of configuration.
        :param dbengine: the kind of database ("mysql" or "postgres" so far)
        :param dbconfigtype: the kind of DB configuration. ("local" or "collector" so far)
        """
        database = self.config.get(self._dbtype, "database")
        username = self.config.get(self._dbtype, "username")
        password = self.config.get(self._dbtype, "password")
        host = self.config.get(self._dbtype, "host")
        port = self.config.get(self._dbtype, "port")
        poolsize = self.config.get(self._dbtype, "poolsize")

        return [database, username, password, host, port, poolsize]

def main(config_path, dbconfigtype):
    """
    Method to get the DB engine type from the appropriate configuration file.
    :param config_path: the path to the ops-monitoring configuration folder.
    :param dbconfigtype: the kind of DB configuration. ("local" or "collector" so far)
    :return: the type of database from the corresponding configuration file
    """
    dbconfig = DbConfigLoader(config_path, dbconfigtype)
    return [dbconfig.get_dbType()]
    


def get_db_parameters(config_path, dbengine, dbconfigtype):
    """
    Method to get the database parameters values for a dbengine kind of database and for a dbconfigtype of configuration.
    :param config_path: 
    :param dbengine: the kind of database ("mysql" or "postgres" so far)
    :param dbconfigtype: the kind of DB configuration. ("local" or "collector" so far)
    """

    dbconfig = DbConfigLoader(config_path, dbconfigtype)
    return dbconfig.get_db_parameters()

