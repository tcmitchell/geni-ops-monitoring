#!/usr/bin/python

def get_schema():
    schema = {}
    schema["memory_util"] = [("aggregate_id","varchar"),("resource_id","varchar"), ("time", "float8"), ("value", "float8")]

    return schema

def get_schema_for_type(schema_type):
    schema = get_schema()

    return schema[schema_type]



