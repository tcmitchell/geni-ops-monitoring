import json
import requests
from pprint import pprint

# agg is for aggregator 
# am is for aggregate manager 

# am_urls is a list of dictionaies with hrefs to reach the datastore of
# the am urn

class InfoFetcher:
    
    def __init__(self, am_urls_urns):
        self.agg_atlas = {}
        self.agg_atlas["aggregate"] = am_urls_urns

    # Get info about all aggregates with hrefs in the agg_atlas
    def poll_am_info(self):

        for am_i in self.agg_atlas["aggregate"]:
            resp = requests.get(am_i["href"])
            am_dict = json.loads(resp.content)
    
        for key in am_dict:
            if key == "resources" or key == "slivers":
                self.agg_atlas[key]  = []
                for res_i in am_dict[key]:
                    self.agg_atlas[key].append(res_i)
            else:
                am_i[key] = am_dict[key]

    # Get info about resources with hrefs in the agg_atlas
    def poll_res_info(self):
        
        for res_i in self.agg_atlas["resources"]:
            resp = requests.get(res_i["href"])
            res_dict = json.loads(resp.content)
            for key in res_dict:
                if key == "ports":
                    self.agg_atlas["interfaces"]  = []
                    for res_i in res_dict[key]:
                        self.agg_atlas["interfaces"].append(res_i)
                else:
                    res_i[key] = res_dict[key]

    # Get info about interfaces with hrefs in the agg_atlas
    def poll_iface_info(self):

        for ifc_i in self.agg_atlas["interfaces"]:
            resp = requests.get(ifc_i["href"])
            ifc_dict = json.loads(resp.content)
            for key in ifc_dict:
                ifc_i[key] = ifc_dict[key]

def main():
    am_urls_urns = []
    am_urls_urns.append({"href":"http://127.0.0.1:5000/info/aggregate/404-ig", "urn":"404-ig-urn"})
    
    info = InfoFetcher(am_urls_urns)
    info.poll_am_info()
    info.poll_res_info()
    info.poll_iface_info()
    pprint(info.agg_atlas)

if __name__ == "__main__":
    main()
