#!/usr/bin/python

def get_schema_dict():
    db_schema = {}
    db_schema["memory_util"] = "(aggregate_id varchar, resource_id varchar, time float8, value float8)"
    
    return db_schema
