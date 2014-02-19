from flask import Flask, request
import sys

class LocalDatastoreServer:
    def __init__(self, parent_path):
        self.local_path = parent_path + "/local/"
        self.common_path = parent_path + "/common/"
        self.config_path = parent_path + "/config/"
        sys.path.append(self.local_path)
        sys.path.append(self.common_path)
        sys.path.append(self.config_path)

        import rest_call_handler
        import table_manager

        self.db_name = "local"
        self.tm = table_manager.TableManager(self.db_name, self.config_path)

        self.app = Flask(__name__)
       
        @self.app.route('/info/aggregate/<agg_id>', methods = ['GET'])
        def info_aggregate_args(agg_id): 
            return rest_call_handler.handle_aggregate_info_query(
                self.tm, agg_id)

        @self.app.route('/info/node/<node_id>', methods = ['GET'])
        def info_node_args(node_id): 
            return rest_call_handler.handle_node_info_query(self.tm, node_id)
        
        @self.app.route('/info/interface/<iface_id>', methods = ['GET'])
        def info_interface_args(iface_id): 
            return rest_call_handler.handle_interface_info_query(
                self.tm, iface_id)
        
        @self.app.route('/info/sliver/<sliver_id>', methods = ['GET'])
        def info_sliver_args(sliver_id): 
            return rest_call_handler.handle_sliver_info_query(
                self.tm, sliver_id)
        
        @self.app.route('/info/slice/<slice_id>', methods = ['GET'])
        def info_slice_args(slice_id): 
            return rest_call_handler.handle_slice_info_query(self.tm, slice_id)
        
        @self.app.route('/info/user/<user_id>', methods = ['GET'])
        def info_user_args(user_id): 
            return rest_call_handler.handle_user_info_query(self.tm, user_id)
        
        @self.app.route('/info/authority/<authority_id>', methods = ['GET'])
        def info_authority_args(authority_id): 
            return rest_call_handler.handle_authority_info_query(
                self.tm, authority_id)
        
        @self.app.route('/info/opsconfig/<opsconfig_id>', methods = ['GET'])
        def info_opsconfig_args(opsconfig_id): 
            return rest_call_handler.handle_opsconfig_info_query(
                self.tm, opsconfig_id)
        
        @self.app.route('/data/', methods = ['GET'])
        def data(): 
            # get everything to the right of ?q= as string from flask.request
            filters = request.args.get('q', None)
            return rest_call_handler.handle_ts_data_query(self.tm, filters)
        
if __name__ == '__main__':

    server = LocalDatastoreServer('..')
    server.app.run(debug = True)
