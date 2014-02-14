import ConfigParser

def local(config_path):
    config = ConfigParser.ConfigParser()
    config.read(config_path + "/local_datastore_operator.conf")
    database = config.get("postgres","database")
    username = config.get("postgres","username")
    password = config.get("postgres","password")
    host = config.get("postgres","host")
    port = config.get("postgres","port")
    return [database, username, password, host, port]

def aggregator(config_path):
    config = ConfigParser.ConfigParser()
    config.read(config_path + "/aggregator_operator.conf")
    database = config.get("postgres","database")
    username = config.get("postgres","username")
    password = config.get("postgres","password")
    host = config.get("postgres","host")
    port = config.get("postgres","port")
    return [database, username, password, host, port]
