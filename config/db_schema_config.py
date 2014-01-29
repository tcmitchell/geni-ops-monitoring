#!/usr/bin/python



def get_schema_dict():
    db_schema = {}
    db_schema["memory_util"] = "(aggregate_id varchar, resource_id varchar, time float8, value float8)"
    
    return db_schema

def get_schema():
    schema = {}
    schema["memory_util"] = [("aggregate_id","varchar"),("resource_id","varchar"), ("time", "float8"), ("value", "float8")]

    return schema

# make this into a class for the config store? 
def get_schema_for_type(schema_type):
    schema = {}
    schema["memory_util"] = [("aggregate_id","varchar"),("resource_id","varchar"), ("time", "float8"), ("value", "float8")]

    return schema[schema_type]



