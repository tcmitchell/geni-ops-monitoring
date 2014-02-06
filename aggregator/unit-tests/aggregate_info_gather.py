import json
import urllib2
#import validictory
from pprint import pprint
#
# Mock conversation between aggregator and local:
#  conversation about information
#  conversation about data
#

#
# ---- INFORMATION ----
#
# ** CONFIG store
#
# Conversation between config store and aggregator here
#
# Outcome is that the config store provides aggregator with a list of
# aggregates and their urls (https://url_of_local_datastore/aggregate/agg_id)
#
#
# ** LOCAL store
#
# aggregator learns of gpo-ig and queries for each domain/aggregate info
#
# aggregator goes to each url <local url>/info/aggregate/<agg_id>
aggregate_urls = {}
aggregate_urls["gpo-ig"] = "http://127.0.0.1:5000/info/aggregate/gpo-ig"

print json.load(urllib2.urlopen(aggregate_urls["gpo-ig"]))
#print json.load(urllib2.urlopen("http://127.0.0.1:5000/info/aggregate/gpo-ig-should-fail"))

#
#
# local responds with nodes (incl. href since talking about physical resources)
# 
#
# aggregator queries for each node <local url>/info/aggregate/<gpo-ig>/<node_id>
#
#
# local resonds with properties about the node including interface existence
#
#
# aggregator queries for each interface
# <local url>/info/aggregate/<gpo-ig>/<node_id>/<interface_id>
#
#
# local responds with properties about the interfaces



'''
For the reference aggregator each eventType has its own table, with
the noun hierarchy being ids /domain/<domain_id>/<node_id> has tsdata.
Examples:

For aggregate level tsdata:
table: <eventType> with columns: (agg_id, ts, v)

node level:
table: <eventType> with columns: (agg_id, node_id, ts, v)

port level:
table: <eventType> with columns: (agg_id, node_id, port_id, ts, v)



Rougher thoughts:

Slivers Chaos has an idea that is a work in progress.


External checker of port to port tests:
(src_domain_id, src_node_id, src_port_id, dst_domain_id, dst_node_id, dst_port_id, ts, v)
'''




'''
schema_file = schema_dir + schema_name
schema_raw = open(schema_file)
schema_dict = json.load(schema_raw)
#pprint.pprint(schema_dict)

# loops through adding each extends 

while "extends" in schema_dict:
    schema_name = schema_dict["extends"]["$ref"]
    schema_dict.pop("extends", None)
    schema_raw = open(schema_dir + schema_name)
    schema_dict = dict(schema_dict.items() + json.load(schema_raw).items())

#pprint(schema_dict)

for k in schema_dict.keys():
    print k, pprint(schema_dict[k]) 


print "properties"
pprint(schema_dict["properties"])

prop_dict = schema_dict["properties"]

print
print

for k in prop_dict.keys():
    if prop_dict[k]["required"] == True:
        print k #pprint(schema_dict["properties"][k])

#print schema_dict["properties"]["required"]

#print(schema_dict["id"])
'''
