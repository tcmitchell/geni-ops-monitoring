import json
import urllib2
#import validictory
from pprint import pprint
#
# Mock conversation between aggregator and local:
#  conversation about information
#  conversation about data
#

# information
#
# aggregator learns of gpo-ig and queries domain
# aggregator goes to url <local of gpo-ig>/info/domain


# local responds with nodes (incl. href since talking about physical resources)


# aggregator queries nodes with <gpo-ig>/info/nodes


# local resonds with properties about the node including ports


# aggregator queries node



'''
For the reference aggregator each eventType has its own table, with
the noun hierarchy being ids /domain/<domain_id>/<node_id> has tsdata
so the data would be:
table: <eventType> with columns: (domain_id, node_id, ts, v)

for ports data would be accessed from:
/domain/<domain_id>/<node_id>/<port> 
table: <eventType> with columns: (domain_id, node_id, port_id, ts, v)

'''

'''
Rougher thoughts:

Slivers Chaos has an idea that is a work in progress.


External checker of port to port tests:
(src_domain_id, src_node_id, src_port_id, dst_domain_id, dst_node_id, dst_port_id, ts, v)
'''

url_dict = {}
url_dict["gpo-ig"] = {}

# retrieved from local store
url_dict["gpo-ig"]["info"] = "http://127.0.0.1:5000/info/domain/" 

info = urllib2.urlopen(url_dict["gpo-ig"]["info"])


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
