-0  #!/usr/bin/python
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
import threading
import opsconfig_loader

class DBManager(object):
    """
    Base Database Manager class.
    Defines the "base" methods to be implemented by subclasses
    """
    def __init__(self, dbnm, usernm, pw, hostnm, prt, poolsize, logger):
        """
        Base constructor, capturing the arguments as attributes of the class.
        """
        self.dbname = dbnm
        self.username = usernm
        self.passwd = pw
        self.hostname = hostnm
        self.port = prt
        self.poolsize = poolsize
        self.logger = logger

    def get_column_name(self, column):
        """
        Method to return a column name with the proper quotation for a given DB engine.
        :param column: the name of the column
        :return: the column name with the proper quotation for the DB engine represented by the class.
        """
        raise NotImplementedError();

    def get_connection(self):
        """
        Method to get a connection. This class functions as a connection pool. Once the caller is done 
        using its connection, it should return it to the pool, using the return_connection() method.
        :return: a connection to the DB specified by the arguments passed in the constructor
        """
        raise NotImplementedError();

    def return_connection(self, conn):
        """
        Method to return a connection after it's been used.
        :param conn: the connection that was once obtained via get_connection()
        """
        raise NotImplementedError();

    def get_import_module_name(self):
        """
        Method to get the DB module name used by this class.
        This is useful for example when trying to catch exception that are defined by the DB API, but truly
        provided by the DB driver module. 
        """
        raise NotImplementedError();


class MySQLDBManager (DBManager):
    """
    Database Manager class for MySQL. 
    """
    def __init__(self, dbnm, usernm, pw, hostnm, prt, poolsize, logger):
        super(MySQLDBManager, self).__init__(dbnm, usernm, pw, hostnm, prt, poolsize, logger)

    def get_column_name(self, column):
        return column

    def get_connection(self):
        # TODO implement poolsize restrictions
        import MySQLdb
        try:
            con = MySQLdb.connect(db=self.dbname, user=self.username, passwd=self.passwd, host=self.hostname, port=int(self.port))
        except Exception, e:
            self.logger.critical("%s \nCannot open a mysql connection to database %s. \n Exiting.\n" % (e, self.dbname))
            sys.exit(1)
        return con

    def return_connection(self, conn):
        conn.close()

    def get_import_module_name(self):
        import MySQLdb
        return MySQLdb

class PostgreSQLDBManager (DBManager):
    """
    Database Manager class for postgreSQL. 
    """
    def __init__(self, dbnm, usernm, pw, hostnm, prt, poolsize, logger):
        super(PostgreSQLDBManager, self).__init__(dbnm, usernm, pw, hostnm, prt, poolsize, logger)
        import psycopg2.pool
        self.pool = psycopg2.pool.ThreadedConnectionPool(1, poolsize, database=dbnm, user=usernm, password=pw, host=hostnm, port=prt)

    def get_column_name(self, column):
        return "\"" + column + "\""

    def get_connection(self):
        return self.pool.getconn()

    def return_connection(self, conn):
        self.pool.putconn(conn)

    def get_import_module_name(self):
        import psycopg2
        return psycopg2


class TableManager:

    def __init__(self, db_type, config_path):

        self.config_path = config_path
        import logger
        self.logger = logger.get_logger(config_path)

        # load a 2-function package for reading database connection config
        sys.path.append(config_path)
        import database_conf_loader

        self.conf_loader = database_conf_loader  # clarify naming conventions

        [db_prog] = self.conf_loader.main(config_path, db_type)

        self.database_type = db_type  # local or collector
        self.database_program = db_prog  # postgres or mysql

        self.dbmanager = self.init_dbmanager()

        self.db_lock = threading.Lock()


    # fetches DB schemas from config local datastore
    def poll_config_store(self):

        self.ocl = opsconfig_loader.OpsconfigLoader(self.config_path)

        # parses the DB schemas
        self.info_schema = self.ocl.get_info_schema()
        self.data_schema = self.ocl.get_data_schema()
        self.event_types = self.ocl.get_event_types()

        # hold the DB schemas in the schema dictionary
        self.schema_dict = self.create_schema_dict(self.data_schema, self.info_schema)

        self.logger.debug("Schema loaded with keys:\n" + str(self.schema_dict.keys()))


    # This is a special table for bootstrapping the configuration
    # It stores the other schemas. This function drops and creates
    # these tables
    def reset_opsconfig_tables(self):

        self.db_lock.acquire()

        table_str = "ops_opsconfig_info"
        schema_arr = [['tablename', 'varchar'], ['schemaarray', 'varchar']]
        schema_str = self.translate_table_schema_to_schema_str(schema_arr, table_str)
        if not self.execute_sql("drop table if exists " + table_str, \
                                "create table if not exists " + table_str + schema_str):
            self.logger.warning("Exception while reseting opsconfig info table %s %s" % (table_str, schema_str))



        table_str = "ops_opsconfig_event"
        schema_arr = [["object_type", "varchar"], ["name", "varchar"], ["id", "varchar"], ["ts", "varchar"], ["v", "varchar"], ["units", "varchar"]]
        schema_str = self.translate_table_schema_to_schema_str(schema_arr, table_str)
        if not self.execute_sql("drop table if exists " + table_str, \
                                "create table if not exists " + table_str + schema_str):
            self.logger.warning("Exception while reseting opsconfig event table %s %s" % (table_str, schema_str))


        table_str = "ops_opsconfig"
        schema_arr = [["$schema", "varchar"], ["id", "varchar"], ["selfRef", "varchar"], ["ts", "int8"]]
        schema_str = self.translate_table_schema_to_schema_str(schema_arr, table_str)
        if not self.execute_sql("drop table if exists " + table_str, \
                         "create table if not exists " + table_str + schema_str):
            self.logger.warning("Exception while reseting opsconfig table %s %s" % (table_str, schema_str))


        table_str = "ops_opsconfig_aggregate"
        schema_arr = [["id", "varchar"], ["opsconfig_id", "varchar"], ["amtype", "varchar"], ["urn", "varchar"], ["selfRef", "varchar"]]
        schema_str = self.translate_table_schema_to_schema_str(schema_arr, table_str)
        if not self.execute_sql("drop table if exists " + table_str, \
                         "create table if not exists " + table_str + schema_str):
            self.logger.warning("Exception while reseting opsconfig aggregate table %s %s" % (table_str, schema_str))


        table_str = "ops_opsconfig_authority"
        schema_arr = [["id", "varchar"], ["opsconfig_id", "varchar"], ["urn", "varchar"], ["selfRef", "varchar"]]
        schema_str = self.translate_table_schema_to_schema_str(schema_arr, table_str)
        if not self.execute_sql("drop table if exists " + table_str, \
                         "create table if not exists " + table_str + schema_str):
            self.logger.warning("Exception while reseting opsconfig authority table %s %s" % (table_str, schema_str))

        self.db_lock.release()

    def init_dbmanager(self):
        """
        Method to initialize the Database Manager based on the settings from the configuration file.
        :return: The correct instance of a concrete class inheriting from DBManager
        :note: This method will cause the program to exit if the specified DB engine is not recognized.
        """
        [database_, username_, password_, host_, port_, poolsize_] = self.conf_loader.get_db_parameters(self.config_path, \
                                                                                             self.database_program, \
                                                                                             self.database_type)

        if self.database_program == "postgres":
            return PostgreSQLDBManager(database_, username_, password_, host_, port_, poolsize_, self.logger)
        elif self.database_program == "mysql":
            return MySQLDBManager(database_, username_, password_, host_, port_, poolsize_, self.logger)
        else:
            self.logger.critical("%s is not a valid database program\n" % self.database_program)
            sys.exit(1)

    def create_schema_dict(self, data_schema, info_schema):
        schema_dict = {}
        schema_dict["units"] = {}
        if (len(dict(data_schema.items() + info_schema.items())) != len(data_schema) + len(info_schema)):
            self.logger.warning("Error: table namespace collision\n")
            return None

        for ds_k in data_schema.keys():
            # last of list is units
            # 2nd of tuple is a string of what unit type is (i.e., percent)
            if self.database_type == "local":
                schema_dict[ds_k] = data_schema[ds_k][:-1]
            elif self.database_type == "collector":
                l = data_schema[ds_k][:-1]
                l.insert(0, ["aggregate_id", "varchar"])
                schema_dict[ds_k] = l
            schema_dict["units"][ds_k] = data_schema[ds_k][-1][1]

        for is_k in info_schema.keys():
            schema_dict[is_k] = info_schema[is_k]

        return schema_dict

    def purge_old_tsdata(self, table_name, delete_older_than_ts):
        self.db_lock.acquire()

        del_str = "delete from " + table_name + " where ts < " + str(delete_older_than_ts)
        self.logger.debug(del_str)

        if not self.execute_sql(del_str):
            self.logger.warning("Trouble deleting data to %s.\n" % table_name)
            self.logger.warning("delete_older_than_ts %s\n" % delete_older_than_ts)

        self.db_lock.release()

    # inserts done here to handle cursor write locking
    def insert_stmt(self, table_name, val_str):

        self.db_lock.acquire()
        ins_str = "insert into " + table_name + " values " + val_str
        self.logger.debug(ins_str)

        if not self.execute_sql(ins_str):
            self.logger.warning("Trouble inserting data to %s.\n" % table_name)
            self.logger.warning("val str %s\n" % val_str)
        self.db_lock.release()

    # deletes done here to handle cursor write locking
    def delete_stmt(self, table_name, obj_id):

        self.db_lock.acquire()
        del_str = "delete from " + table_name + " where id = '" + obj_id + "'"
        self.logger.debug(del_str)

        if not self.execute_sql(del_str):
            self.logger.warning("Trouble deleting %s as id from %s.\n" % (obj_id, table_name))

        self.db_lock.release()


    '''
    Not allowed in a transaction block, connection implies a database 
    TODO drop database
    def drop_database(self, dbname_str): 
        try:
            cur = self.con.cursor()
            cur.execute("drop database if exists " + dbname_str)
            self.con.commit()
            print "Dropping database", dbname_str
            cur.close()
        except Exception, e:
            print e

    def create_database(self, dbname_str):
        try:
            cur = self.con.cursor()
            cur.execute("create database " + dbname_str)
            self.con.commit()
            print "Creating database", dbname_str
            cur.close()
        except Exception, e:
            print e
    '''

    # break this into postgres and mysql
    def table_exists(self, table_str):
        if self.database_program == "postgres":
            return self.table_exists_psql(table_str)
        elif self.database_program == "mysql":
            return self.table_exists_mysql(table_str)

    def table_exists_mysql(self, table_str):
        exists = False
        self.db_lock.acquire()
        q_res = self.query("show tables like '" + table_str + "'")
        if q_res is not None and len(q_res) > 0:
            exists = True
        self.db_lock.release()

        return exists

    def table_exists_psql(self, table_str):
        exists = False
        self.db_lock.acquire()
        q_res = self.query("select exists(select relname from pg_class where relname='" + table_str + "')")
        if q_res is not None and len(q_res) > 0 and len(q_res[0]) > 0:
            exists = q_res[0][0]
        self.db_lock.release()

        return exists


    def get_column_name(self, column):
        """
        Method to return the column name properly quoted, or not for the DB engine currently used.
        :param column: the name of the column
        :return: the column string to be inserted into a SQL statement 
        """
        return self.dbmanager.get_column_name(column)


    def get_col_names(self, table_str):
        if (self.database_program == "postgres"):
            self.get_col_names_psql(table_str)
        if (self.database_program == "mysql"):
            self.get_col_names_mysql(table_str)


    def get_col_names_psql(self, table_str):
        # using cursor description not cursor.fetchall(), so have to kinda duplicate the query() code here...
        self.db_lock.acquire()
        err = True
        con = self.dbmanager.get_connection()
        cur = con.cursor()
        col_names = []
        try:
            cur.execute("select * from " + table_str + " LIMIT 0")
            err = False
        except (AttributeError, self.dbmanager.get_import_module_name().OperationalError):
            cur.close()
            self.dbmanager.return_connection(con)
            con = self.dbmanager.get_connection()
            cur = con.cursor()
            try:
                cur.execute("select * from " + table_str + " LIMIT 0")
                err = False
            except Exception, e:
                self.logger.warning("%s\n" % e)
        except Exception, e:
            self.logger.warning("%s\n" % e)

        if not err:
            col_names = [desc[0] for desc in cur.description]
        cur.close()

        self.dbmanager.return_connection(con)
        self.db_lock.release()
        return col_names


    def get_col_names_mysql(self, table_str):

        self.db_lock.acquire()
        con = self.dbmanager.get_connection()
        col_names = []

        # todo fill in

        self.dbmanager.return_connection(con)
        self.db_lock.release()
        return col_names


    def establish_tables(self, table_str_arr):
        for table_str in table_str_arr:
            # Ensures table_str is in ops_ namespace
            if table_str.startswith("ops_"):
                self.establish_table(table_str)


    def establish_all_tables(self):
        self.establish_tables(self.schema_dict.keys())

    def purge_outdated_resources_from_info_tables(self):
        pass  # TODO fill in


    def establish_table(self, table_str):

        schema_str = self.translate_table_schema_to_schema_str(self.schema_dict[table_str], table_str)

        if self.table_exists(table_str):
            self.logger.debug("INFO: table " + table_str + " already exists with schema: \n" + schema_str)
            self.logger.debug("Skipping creation of " + table_str)

        else:
            self.db_lock.acquire()
            self.logger.info("create table " + table_str + schema_str)
            if not self.execute_sql("create table " + table_str + schema_str):
                self.logger.warning("Exception while creating table %s %s" % (table_str, schema_str))
            self.db_lock.release()


    def drop_tables(self, table_str_arr):
        for table_str in table_str_arr:
            self.drop_table(table_str)


    def drop_table(self, table_str):

        self.db_lock.acquire()
        self.logger.debug("drop table if exists " + table_str)

        if self.execute_sql("drop table if exists " + table_str):
            self.logger.info("Dropped table" + table_str)
        else:
            self.logger.warning("Error while dropping table %s" % (table_str))

        self.db_lock.release()


    def get_all_ids_from_table(self, table_str):

        res = [];
        self.db_lock.acquire()
        q_res = self.query("select distinct id from " + table_str)
        self.logger.debug(q_res)

        if q_res is not None:
            for res_i in range(len(q_res)):
                res.append(q_res[res_i][0])  # gets first of single tuple

        self.db_lock.release()

        return res



    def translate_table_schema_to_schema_str(self, table_schema_dict, table_str):
        schema_str = "("
        if self.database_program == "postgres":
            for col_i in range(len(table_schema_dict)):
                schema_str += "\"" + table_schema_dict[col_i][0] + "\" " + table_schema_dict[col_i][1] + ","
        else:
            for col_i in range(len(table_schema_dict)):
                if table_schema_dict[col_i][1] == "varchar":
                    schema_str += table_schema_dict[col_i][0] + " " + table_schema_dict[col_i][1] + "(512),"
                else:
                    schema_str += table_schema_dict[col_i][0] + " " + table_schema_dict[col_i][1] + ","

        # remove , and add )
        return schema_str[:-1] + ")"

    def query(self, querystr):
        """
        Execute a query and returns the results.
        :param querystr:  the query to be executed
        :return: a tuple containing the tuples of all the records selected, themselves in the form of tuples.
                 None if there was an issue executing the query.
        """
#         if self.database_program == "postgres":
#             import psycopg2 as dbengine
#         elif self.database_program == "mysql":
#             import MySQLdb as dbengine

        con = self.dbmanager.get_connection()
        cur = con.cursor()
        q_res = None
        try:
            cur.execute(querystr)
            if cur.rowcount > 0:
                q_res = cur.fetchall()
        except (AttributeError, self.dbmanager.get_import_module_name().OperationalError):
            self.logger.info("Trying to reconnect")
            con.rollback()
            cur.close()
            self.dbmanager.return_connection(con)
            con = self.dbmanager.get_connection()
            cur = con.cursor()
            try:
                cur.execute(querystr)
                if cur.rowcount > 0:
                    q_res = cur.fetchall()
            except Exception, e:
                # TODO replace with logging statement
                self.logger.warning("Error while executing the following query: " + querystr)
                self.logger.warning(str(e))
        except Exception, e:
            # TODO replace with logging statement
            self.logger.warning("Error while executing the following query: " + querystr)
            self.logger.warning(e)

        finally:
            con.commit()

        cur.close()
        self.dbmanager.return_connection(con)

        return q_res

    def execute_sql(self, sqlstatement):
        """
        Execute one or more SQL statements and returns True if the statement(s) executed correctly.
        :param querystr:  the statement or statements to be executed. No results are expected.
        :return: True if all the statement executed correctly, False if there was an issue. 
        As soon as an issue is encountered, no more statements are executed and a DB rollback is issued.
        """
#         if self.database_program == "postgres":
#             import psycopg2 as dbengine
#         elif self.database_program == "mysql":
#             import MySQLdb as dbengine

        con = self.dbmanager.get_connection()
        cur = con.cursor()
        res = False

        if isinstance(sqlstatement, basestring):
            statements = (sqlstatement,)
        elif isinstance(sqlstatement, list):
            statements = sqlstatement
        elif isinstance(sqlstatement, tuple):
            statements = sqlstatement
        else:
            self.logger.critical("Unexpected type for sqlstatement argument %s.\n Exiting.\n" % (sqlstatement,))
            sys.exit(1)


        tryNumber = 1
        fatalErr = False
        while True:
            err = False
            for statement in statements:
                err = True
                try:
                    cur.execute(statement)
                    err = False
                except (AttributeError, self.dbmanager.get_import_module_name().OperationalError):
                    self.logger.info("Trying to reconnect")
                    # since we're dealing with mutilple statements, in case of a disconnection, we need to reissue them all.
                    con.rollback()
                    cur.close()
                    self.dbmanager.return_connection(con)
                    con = self.dbmanager.get_connection()
                    cur = con.cursor()
                    tryNumber += 1
                except Exception, e:
                    # TODO replace with logging statement
                    self.logger.warning("Error while executing the following SQL statement: " + statement)
                    self.logger.warning(str(e))
                    con.rollback()
                    # we don't want to retry after this
                    fatalErr = True
                if err:
                    break
            else:  # for loop else
                # so we had no issue.
                con.commit()
                res = True
                break;
            if fatalErr or (tryNumber > 2):
                res = False
                break

        cur.close()
        self.dbmanager.return_connection(con)

        return res

# used only if arguments passed to program
# gets each argument as a table name
def arg_parser(argv, dict_keys):
    if (len(argv) == 1):
        sys.exit(1)

    table_str_arr = []

    for arg in argv[1:]:

        try:
            table_str = str(arg)
        except ValueError:
            sys.stderr.write("%s Not a string.\n" % arg)
            sys.exit(1)
        if table_str not in dict_keys:
            print "Argument " + arg + " converted to string " + table_str + " was not found in schema dictionary keys:"
            print dict_keys.keys()
            sys.exit(1)
        else:
            table_str_arr.append(table_str)

    return table_str_arr


def main():
    print "no unit test"


if __name__ == "__main__":

    main()
