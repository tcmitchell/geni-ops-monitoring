import json
import psycopg2
import sys
import requests
from pprint import pprint

config_path = "../config/"
common_path = "../common/"

sys.path.append(config_path)
sys.path.append(common_path)
import table_manager
import postgres_conf_loader

# agg is for aggregator 
# am is for aggregate manager 

# am_urls is a list of dictionaies with hrefs to reach the datastore of
# the am urn

# This program populates an "aggregator atlas" and sends the data to
# database tables.  The data_fetcher uses this to fetch tsdata about
# objects.  The aggregator apps (i.e., nagios) queries the tables
# for object existence instead of having an InfoFetcher instance.

class InfoFetcher:
    
    def __init__(self, tbl_mgr, am_urls_urns):
        self.tbl_mgr = tbl_mgr
        self.agg_atlas = {}
        self.agg_atlas["href"] = {}
        self.agg_atlas["href"]["aggregate"] = {}
        self.agg_atlas["href"]["resource"] = {}
        self.agg_atlas["href"]["node"] = {}
        self.agg_atlas["href"]["sliver"] = {}
        self.agg_atlas["href"]["interface"] = {}
        for am_i in am_urls_urns:
            self.agg_atlas["href"]["aggregate"][am_i["urn"]] = am_i["href"]
    
        self.agg_atlas["aggregate"] = []
        self.agg_atlas["sliver"]  = []        
        self.agg_atlas["node"]  = []        
        self.agg_atlas["interface"]  = []
        self.agg_atlas["aggregate_resource"] = {}
        self.agg_atlas["aggregate_sliver"] = {}
        self.agg_atlas["node_interface"] = {}


    # Get info about all aggregates with hrefs in the agg_atlas
    def poll_am_info(self):
        self.agg_atlas["aggregate"] = []
        for am_urn in self.agg_atlas["href"]["aggregate"]:
            resp = requests.get(self.agg_atlas["href"]["aggregate"][am_urn])
            am_dict = json.loads(resp.content)
            am_i = {}
            for key in am_dict:
                if key == "resources":
                    for res_i in am_dict[key]:
                        self.agg_atlas["href"]["resource"][res_i["urn"]] = res_i["href"]                        
                elif key == "slivers":
                    for res_i in am_dict[key]:
                        self.agg_atlas["href"]["sliver"][res_i["urn"]] = res_i["href"]
                else:
                    am_i[key] = am_dict[key]
            self.agg_atlas["aggregate"].append(am_i)

              
    def poll_aggregate_resource_info(self):
        self.agg_atlas["aggregate_resource"] = []
        for am_urn in self.agg_atlas["href"]["aggregate"]:
            resp = requests.get(self.agg_atlas["href"]["aggregate"][am_urn])
            am_dict = json.loads(resp.content)
            am_id = am_dict["id"]
            resources = am_dict["resources"]
            for res_i in resources:
                res_i_self_ref = res_i["href"]
                res_i_urn = res_i["urn"]
                resp = requests.get(res_i_self_ref)
                res_i_dict = json.loads(resp.content)
 
                res_i_id = res_i_dict["id"]
                agg_res_list = [res_i_id, am_id, res_i_urn, res_i_self_ref];
                agg_res_dict = {"id":res_i_id, "aggregate_id":am_id, "urn":res_i_urn, "selfRef":res_i_self_ref}                                
                self.agg_atlas["aggregate_resource"].append(agg_res_dict)
                info_insert(self.tbl_mgr, "aggregate_resource", agg_res_list)


    # Get info about resources with hrefs in the agg_atlas
    def poll_res_info(self):
        self.agg_atlas["node"] = []    
        for res_urn in self.agg_atlas["href"]["resource"]:
            resp = requests.get(self.agg_atlas["href"]["resource"][res_urn])
            res_dict = json.loads(resp.content)
              
            if res_dict["$schema"].endswith("node#"):
                node_i = {}
                for key in res_dict:
                    if key == "ports":
                        for res_i in res_dict[key]:
                            self.agg_atlas["href"]["interface"][res_i["urn"]] = res_i["href"]
                    else:
                        node_i[key] = res_dict[key]
                self.agg_atlas["node"].append(node_i)

    # Get info about interfaces with hrefs in the agg_atlas
    def poll_iface_info(self):
        self.agg_atlas["interface"] = []    
        for iface_urn in self.agg_atlas["href"]["interface"]:
            resp = requests.get(self.agg_atlas["href"]["interface"][iface_urn])
            iface_dict = json.loads(resp.content)
            iface_i = {}
            for key in iface_dict:
                iface_i[key] = iface_dict[key]
            self.agg_atlas["interface"].append(iface_i)
 
    # Not implemented on the local side 
            #NOT WORKING
    def poll_sliver_info(self):
        pass
        '''
        self.agg_atlas["sliver"] = []    
        for slv_urn in self.agg_atlas["href"]["sliver"]:
            resp = requests.get(self.agg_atlas["href"]["sliver"][slv_urn])
            slv_dict = json.loads(resp.content)
            slv_i = {}
            for key in slv_dict:
                slv_i[key] = slv_dict[key]
            self.agg_atlas["sliver"].append(slv_i)
            '''

    # Polls am hrefs, then drops/inserts aggregate table
    def refresh_am_info(self):
        self.poll_am_info()
        self.tbl_mgr.drop_table("aggregate") 
        self.tbl_mgr.establish_table("aggregate")

        schema = self.tbl_mgr.schema_dict["aggregate"]

        for am_i in self.agg_atlas["aggregate"]:
            am_info_list = []
            for key in schema:  
                am_info_list.append(am_i[key[0]])
            info_insert(self.tbl_mgr, "aggregate", am_info_list)

    # Polls res hrefs, then drops/inserts node table (and potentially
    # other types of resources tables)
    def refresh_res_info(self):
        self.poll_res_info()
        self.tbl_mgr.drop_table("node") 
        self.tbl_mgr.establish_table("node")

        schema = self.tbl_mgr.schema_dict["node"]

        for node_i in self.agg_atlas["node"]:
            node_info_list = []
            for key in schema:  
                node_info_list.append(node_i[key[0]])
            info_insert(self.tbl_mgr, "node", node_info_list)

    # Polls aggregate info and then resource info to get resource ids
    def refresh_aggregate_resource_info(self):
        self.tbl_mgr.drop_table("aggregate_resource") 
        self.tbl_mgr.establish_table("aggregate_resource")
        self.poll_aggregate_resource_info()


    # refresh_aggregate_sliver

    # refresh_sliver_resource

    # slices?


    # Polls interface hrefs, then drops/inserts interface table
    def refresh_iface_info(self):
        self.poll_iface_info()
        self.tbl_mgr.drop_table("interface") 
        self.tbl_mgr.establish_table("interface")

        schema = self.tbl_mgr.schema_dict["interface"]

        for iface_i in self.agg_atlas["interface"]:
            iface_info_list = []
            pprint(iface_i)
            pprint(schema)
            for key in schema:  
                if key[0] == "address_type":
                    iface_info_list.append(iface_i["address"]["type"])
                elif key[0] == "address_address":
                    iface_info_list.append(iface_i["address"]["address"])
                else:
                    iface_info_list.append(iface_i[key[0]])
            
            info_insert(self.tbl_mgr, "interface", iface_info_list)
             
def info_insert(tbl_mgr, table_str, row_arr):
    val_str = "'"
    for val in row_arr:
        val_str += str(val) + "','" # join won't do this

    val_str = val_str[:-2] # remove last 2 of ','
    cur = tbl_mgr.con.cursor()
    tbl_mgr.db_lock.acquire()
    cur.execute("insert into " + table_str + " values (" + val_str + ")")
    tbl_mgr.con.commit()
    tbl_mgr.db_lock.release()
    cur.close()  

def main():

    [database_, username_, password_, host_, port_] = postgres_conf_loader.aggregator(config_path)

    con = psycopg2.connect(database = database_, user = username_, password = password_, host = host_, port = port_)

    info_schema = json.load(open("../config/info_schema"))
    data_schema = json.load(open("../config/data_schema"))
    tbl_mgr = table_manager.TableManager(con, data_schema, info_schema)
    tbl_mgr.drop_tables(info_schema.keys())
    tbl_mgr.establish_tables(info_schema.keys())

    am_urls_urns = []
    am_urls_urns.append({"href":"http://127.0.0.1:5000/info/aggregate/404-ig", "urn":"404-ig-urn"})
    
    info = InfoFetcher(tbl_mgr, am_urls_urns)
    
    info.refresh_am_info()
    info.refresh_aggregate_resource_info()
    info.refresh_res_info()
    info.refresh_iface_info()
        
    
    pprint(info.agg_atlas)

if __name__ == "__main__":
    main()
