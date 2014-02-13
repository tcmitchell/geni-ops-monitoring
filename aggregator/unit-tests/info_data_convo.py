import json
import requests
#import validictory
from pprint import pprint


agg_atlas = {}
agg_atlas["aggregate"] = []

# These are provided by the config store.
# Aggregator knows which aggregates to monitor.
agg_atlas["aggregate"].append({"href":"http://127.0.0.1:5000/info/aggregate/404-ig", "urn":"404-ig-urn"})

# Get info about all aggregates in the agg_atlas
for am_i in agg_atlas["aggregate"]:
    resp = requests.get(am_i["href"])
    am_dict = json.loads(resp.content)
    
    for key in am_dict:
        if key == "resources" or key == "slivers":
            agg_atlas[key]  = []
            for res_i in am_dict[key]:
                agg_atlas[key].append(res_i)
        else:
            am_i[key] = am_dict[key]

# Get info about resources in the agg_atlas
for res_i in agg_atlas["resources"]:
    resp = requests.get(res_i["href"])
    res_dict = json.loads(resp.content)
    for key in res_dict:
        if key == "ports":
            agg_atlas["interfaces"]  = []
            for res_i in res_dict[key]:
                agg_atlas["interfaces"].append(res_i)
        else:
            res_i[key] = res_dict[key]

# Get info about interfaces in the agg_atlas
for ifc_i in agg_atlas["interfaces"]:
    resp = requests.get(ifc_i["href"])
    ifc_dict = json.loads(resp.content)
    for key in ifc_dict:
        ifc_i[key] = ifc_dict[key]

pprint(agg_atlas)
