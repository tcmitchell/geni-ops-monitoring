import ConfigParser

def main(config_path):
    config = ConfigParser.ConfigParser()
    config.read(config_path + "/local_datastore_operator.conf")
    database = config.get("postgres","database")
    username = config.get("postgres","username")
    password = config.get("postgres","password")
    host = config.get("postgres","host")
    port = config.get("postgres","port")
    return [database, username, password, host, port]
