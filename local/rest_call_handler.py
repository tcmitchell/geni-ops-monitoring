#!/usr/bin/python
#----------------------------------------------------------------------
# Copyright (c) 2014-2015 Raytheon BBN Technologies
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and/or hardware specification (the "Work") to
# deal in the Work without restriction, including without limitation the
# rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Work, and to permit persons to whom the Work
# is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Work.
#
# THE WORK IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
# OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE WORK OR THE USE OR OTHER DEALINGS
# IN THE WORK.
#----------------------------------------------------------------------

import json
import logger
import time


__SCHEMA_BASE = "http://www.gpolab.bbn.com/monitoring/schema/20151105/"

# Main query handler functions

# Main handle for data queries


def handle_ts_data_query(tm, filters):

    url = "/data/?q=" + filters
    opslog = logger.get_logger()
    schema_dict = tm.schema_dict
    opslog.debug(
        "handling time series query for filter ='" +
        str(filters) +
        "'")
    try:
        q_dict = json.loads(filters)  # try to make a dictionary
    except Exception as e:
        opslog.warning(filters + "failed to parse as JSON\n" + str(e))
        fail_str = "query: " + filters + "\n\nhad error: " + str(e) + \
            "\n\n failed to parse as JSON"
        return json.dumps(create_json_error_response(fail_str, url))

        return "query: " + filters + "<br><br>had error: " + str(e) + \
            "<br><br> failed to parse as JSON"

    # check for necessary keys
    (ok, fail_str) = check_data_query_keys(q_dict)
    if ok == True:
        ts_filters = q_dict["filters"]["ts"]
        # eliminate possible redundancy in list of types.
        event_types = set(q_dict["filters"]["eventType"])
        objects = q_dict["filters"]["obj"]
        # eliminate possible redundancy in list of object ids.
        objid_set = set(objects["id"])
        obj_type = objects["type"]
    else:
        # returns why filters failed
        return json.dumps(create_json_error_response(fail_str, url))

    ts_where_str = build_ts_where_str(ts_filters)

    # ts
    if ts_where_str == "":
        return "[]"

    resp_arr = []

    # Remember if we are wildcarding (selecting all of) the objects.
    # If we are, none of the other object ids in the list (if any)
    # matter, since we're going to get them all anyway.
    obj_wildcard = "*" in objid_set

    for event_type in event_types:
        et_split = event_type.split(':')
        if et_split[0] == "ops_monitoring":
            event_type = et_split[1]

            # Construct the name of the database table.
            table_str = "ops_" + obj_type + "_" + event_type
            object_table_name = "ops_" + obj_type

            # If wildcarding the objects, get all possible object ids
            # from this table.
            if obj_wildcard:
                objid_set = get_object_ids(tm, table_str)

            for obj_id in objid_set:
                resp_i = {}

                ts_arr = get_tsdata(
                    tm,
                    event_type,
                    obj_type,
                    obj_id,
                    ts_where_str)
                obj_href = None
                obj_href_res = get_refs(
                    tm, object_table_name, obj_id, ("selfRef",))
                if obj_href_res is None:
                    tm.logger.warning(
                        "Could not find URL for object %s with ID '%s'" %
                        (obj_type, obj_id))
                else:
                    obj_href = obj_href_res[0]

                if (ts_arr is not None):
                    resp_i["$schema"] = __SCHEMA_BASE + "data#"
                    resp_i["id"] = event_type + ":" + obj_id
                    resp_i["subject"] = obj_href
                    resp_i["eventType"] = "ops_monitoring:" + event_type
                    resp_i["description"] = "ops_monitoring:" + \
                        event_type + " for " + obj_id + " of type " + obj_type
                    resp_i["units"] = schema_dict["units"][table_str]
                    resp_i["tsdata"] = ts_arr
                    resp_arr.append(resp_i)
        else:
            opslog.warning(
                "event " +
                event_type +
                " not recognized: missing namespace 'ops_monitoring:' ?")

    return json.dumps(resp_arr)


# Main handle for node queries
def handle_node_info_query(tm, node_id):
    url = "/info/node/" + node_id
    opslog = logger.get_logger()
    table_str = "ops_node"
    node_schema = tm.schema_dict[table_str]

    iface_refs = []

    node_info = get_object_info(tm, table_str, node_id)

    if node_info is not None:
        iface_refs = get_related_objects_refs(
            tm,
            "ops_interface",
            "node_id",
            node_id)
        parent_idx = tm.get_column_from_schema(node_schema, "parent_node_id")
        parent_node_ref = None
        if node_info[parent_idx] is not None:
            parent_node_ref = get_refs(tm, "ops_node", node_info[parent_idx])

        metrics_ids = get_related_objects_refs(tm,
                                               "ops_node_metricsgroup_relation",
                                               "group_id",
                                               node_info[
                                                   tm.get_column_from_schema(
                                                       node_schema,
                                                       'metricsgroup_id')],
                                               ("id", "period")
                                               )

        return json.dumps(get_node_info_dict(
            node_schema, node_info, iface_refs, parent_node_ref, metrics_ids))

    else:
        errStr = "node not found: " + node_id
        opslog.debug(errStr)
        return json.dumps(create_json_error_response(errStr, url))


# Main handle interface queries
def handle_interface_info_query(tm, iface_id):
    url = "/info/interface/" + iface_id
    opslog = logger.get_logger()
    table_str = "ops_interface"
    iface_schema = tm.schema_dict[table_str]

    iface_info = get_object_info(tm, table_str, iface_id)

    if iface_info is not None:
        parent_idx = tm.get_column_from_schema(
            iface_schema,
            "parent_interface_id")
        parent_if_ref = None
        if iface_info[parent_idx] is not None:
            parent_if_ref = get_refs(
                tm,
                "ops_interface",
                iface_info[parent_idx])
        addr_table_str = "ops_interface_addresses"
        address_schema = tm.schema_dict[addr_table_str]
        address_rows = get_related_objects_full(tm, addr_table_str,
                                                "interface_id", iface_id)
        metrics_ids = get_related_objects_refs(tm,
                                               "ops_interface_metricsgroup_relation",
                                               "group_id",
                                               iface_info[
                                                   tm.get_column_from_schema(
                                                       iface_schema,
                                                       'metricsgroup_id')],
                                               ("id", "period")
                                               )

        return json.dumps(get_interface_info_dict(iface_schema, iface_info,
                                                  parent_if_ref,
                                                  address_schema,
                                                  address_rows,
                                                  metrics_ids)
                          )
    else:
        errStr = "interface not found: " + iface_id
        opslog.debug(errStr)
        return json.dumps(create_json_error_response(errStr, url))


# Main handle interface queries
def handle_interfacevlan_info_query(tm, ifacevlan_id):
    url = "/info/interfacevlan/" + ifacevlan_id
    opslog = tm.logger
    table_str = "ops_interfacevlan"
    iface_schema = tm.schema_dict[table_str]

    ifacevlan_info = get_object_info(tm, table_str, ifacevlan_id)

    if ifacevlan_info is not None:
        if_id = ifacevlan_info[
            tm.get_column_from_schema(
                iface_schema,
                'interface_id')]
        if if_id is None:
            if_ref = None
        else:
            if_ref = get_related_objects_refs(
                tm,
                'ops_interface',
                'id',
                if_id)[0]

        metrics_ids = get_related_objects_refs(tm,
                                               "ops_interfacevlan_metricsgroup_relation",
                                               "group_id",
                                               ifacevlan_info[
                                                   tm.get_column_from_schema(
                                                       iface_schema,
                                                       'metricsgroup_id')],
                                               ("id", "period")
                                               )
        return json.dumps(get_interfacevlan_info_dict(
            iface_schema, ifacevlan_info, if_ref, metrics_ids))
    else:
        errStr = "interfacevlan not found: " + ifacevlan_id
        opslog.debug(errStr)
        return json.dumps(create_json_error_response(errStr, url))


# Main handle for sliver queries
def handle_sliver_info_query(tm, sliver_id):
    url = "/info/sliver/" + sliver_id
    opslog = logger.get_logger()
    table_str = "ops_sliver"
    sliver_schema = tm.schema_dict[table_str]

    sliver_info = get_object_info(tm, table_str, sliver_id)

    if sliver_info is not None:

        # find sliver resources
        resource_refs = list()
        node_ids = get_related_objects(
            tm,
            "ops_sliver_node",
            "sliver_id",
            sliver_id)
        for node_id in node_ids:
            node_ref = get_refs(tm, "ops_node", node_id)
            res_ref = dict()
            res_ref['resource_type'] = "node"
            res_ref["href"] = node_ref[0]
            res_ref["urn"] = node_ref[1]
            resource_refs.append(res_ref)
        link_ids = get_related_objects(
            tm,
            "ops_sliver_link",
            "sliver_id",
            sliver_id)
        for link_id in link_ids:
            link_ref = get_refs(tm, "ops_link", link_id)
            res_ref = dict()
            res_ref['resource_type'] = "link"
            res_ref["href"] = link_ref[0]
            res_ref["urn"] = link_ref[1]
            resource_refs.append(res_ref)

        if len(resource_refs) == 0:
            opslog.warning(
                "Failed to find resource for sliver %s" %
                (sliver_id))

        agg_refs = get_refs(
            tm,
            'ops_aggregate',
            sliver_info[
                tm.get_column_from_schema(
                    sliver_schema,
                    'aggregate_id')])

        return json.dumps(
            get_sliver_info_dict(sliver_schema, sliver_info, resource_refs, agg_refs))
    else:
        errStr = "sliver not found: " + sliver_id
        opslog.debug(errStr)
        return json.dumps(create_json_error_response(errStr, url))


# Main handle aggregate for info queries
def handle_aggregate_info_query(tm, agg_id, monitoring_version):
    """
    Function to handle an aggregate info query.
    :param tm: the table manager instance
    :param agg_id: the aggregate id to look for
    :param monitoring_version: the monitoring version of the ops monitoring software implementation.
    :return: a json dictionary containing either the aggregate information or an error message.
    """
    url = "/info/aggregate/" + agg_id
    opslog = logger.get_logger()
    table_str = "ops_aggregate"
    agg_schema = tm.schema_dict[table_str]

    res_refs = list()
    slv_refs = list()

    agg_info = get_object_info(tm, table_str, agg_id)
    if agg_info is not None:

        node_resources = get_related_objects_refs(
            tm,
            "ops_node",
            "aggregate_id",
            agg_id)
        if node_resources is not None:
            for node_res in node_resources:
                res_refs.append((node_res[0], node_res[1], "node"))

        link_resources = get_related_objects_refs(
            tm,
            "ops_link",
            "aggregate_id",
            agg_id)
        if link_resources is not None:
            for link_res in link_resources:
                res_refs.append((link_res[0], link_res[1], "link"))

        slv_refs = get_related_objects_refs(
            tm,
            "ops_sliver",
            "aggregate_id",
            agg_id)

        metrics_ids = get_related_objects_refs(tm,
                                               "ops_aggregate_metricsgroup_relation",
                                               "group_id",
                                               agg_info[
                                                   tm.get_column_from_schema(
                                                       agg_schema,
                                                       'metricsgroup_id')],
                                               ("id", "period")
                                               )

        return json.dumps(get_aggregate_info_dict(agg_schema, agg_info,
                                                  res_refs, slv_refs,
                                                  monitoring_version,
                                                  metrics_ids)
                          )

    else:
        errStr = "aggregate not found: " + agg_id
        opslog.debug(errStr)
        return json.dumps(create_json_error_response(errStr, url))


def handle_externalcheck_info_query(tm, extck_id, monitoring_version):
    """
    Function to handle an external check info query.
    :param tm: the table manager instance
    :param agg_id: the external check id to look for
    :param monitoring_version: the monitoring version of the ops monitoring software implementation.
    :return: a json dictionary containing either the external check information or an error message.
    """
    url = "/info/externalcheck/" + extck_id
    opslog = logger.get_logger()
    table_str = "ops_externalcheck"
    extck_schema = tm.schema_dict[table_str]

    extck_info = get_object_info(tm, table_str, extck_id)
    if extck_info is not None:

        monitored_aggregates_info = get_monitored_aggregates(tm, extck_id)
        monitored_aggregates = None
        if monitored_aggregates_info:
            monitored_aggregates = list()
            metrics_dict = dict()
            for mon_agg_info in monitored_aggregates_info:
                # Chances are, the same metrics group is used over and over again.
                # so let's look up the corresponding metrics once only.
                if mon_agg_info[2] in metrics_dict:
                    metrics_ids = metrics_dict[mon_agg_info[2]]
                else:
                    metrics_ids = get_related_objects_refs(tm,
                                                           "ops_aggregate_metricsgroup_relation",
                                                           "group_id",
                                                           mon_agg_info[2],
                                                           ("id", "period")
                                                           )
                    metrics_dict[mon_agg_info[2]] = metrics_ids
                monitored_aggregates.append(
                    (mon_agg_info[0], mon_agg_info[1], metrics_ids))

        exp_refs = get_related_objects_refs(
            tm,
            "ops_experiment",
            "externalcheck_id",
            extck_id,
            ("selfRef",
             ))

        return json.dumps(get_externalcheck_info_dict(extck_schema,
                                                      extck_info,
                                                      exp_refs,
                                                      monitored_aggregates,
                                                      monitoring_version))

    else:
        errStr = "external check store not found: " + extck_id
        opslog.debug(errStr)
        return json.dumps(create_json_error_response(errStr, url))


# Main handle aggregate for info queries
def handle_authority_info_query(tm, auth_id, monitoring_version):
    """
    Function to handle an authority info query.
    :param tm: the table manager instance
    :param agg_id: the authority id to look for
    :param monitoring_version: the monitoring version of the ops monitoring software implementation.
    :return: a json dictionary containing either the authority information or an error message.
    """
    url = "/info/authority/" + auth_id
    opslog = logger.get_logger()
    table_str = "ops_authority"
    auth_schema = tm.schema_dict[table_str]

    user_refs = []
    slice_refs = []

    auth_info = get_object_info(tm, table_str, auth_id)
    if auth_info is not None:

        user_refs = get_related_objects_refs(
            tm,
            "ops_user",
            "authority_id",
            auth_id)

        slice_refs = get_related_objects_refs(
            tm,
            "ops_slice",
            "authority_id",
            auth_id)

        return json.dumps(get_authority_info_dict(auth_schema,
                                                  auth_info,
                                                  user_refs,
                                                  slice_refs,
                                                  monitoring_version))

    else:
        errStr = "authority not found: " + auth_id
        opslog.debug(errStr)
        return json.dumps(create_json_error_response(errStr, url))


# Main handle slice info queries
def handle_slice_info_query(tm, slice_id):
    url = "/info/slice/" + slice_id
    opslog = logger.get_logger()
    table_str = "ops_slice"
    slice_schema = tm.schema_dict[table_str]

    user_refs = []

    slice_info = get_object_info(tm, table_str, slice_id)
    if slice_info is not None:

        users = get_related_objects(tm, "ops_slice_user", "slice_id", slice_id)

        for user_i in users:
            user_refs.append(get_slice_user_refs(tm, slice_id, user_i))

        auth_ref = get_refs(
            tm,
            'ops_authority',
            slice_info[
                tm.get_column_from_schema(
                    slice_schema,
                    'authority_id')])

        return json.dumps(
            get_slice_info_dict(slice_schema, slice_info, user_refs, auth_ref))

    else:
        errStr = "slice not found: " + slice_id
        opslog.debug(errStr)
        return json.dumps(create_json_error_response(errStr, url))


# Main handle user info queries
def handle_user_info_query(tm, user_id):
    url = "/info/user/" + user_id
    opslog = logger.get_logger()
    table_str = "ops_user"
    user_schema = tm.schema_dict[table_str]

    user_info = get_object_info(tm, table_str, user_id)
    if user_info is not None:
        auth_ref = get_refs(
            tm,
            'ops_authority',
            user_info[
                tm.get_column_from_schema(
                    user_schema,
                    'authority_id')])
        return json.dumps(get_user_info_dict(user_schema, user_info, auth_ref))
    else:
        errStr = "user not found: " + user_id
        opslog.debug(errStr)
        return json.dumps(create_json_error_response(errStr, url))


# Main handle for link info queries
def handle_link_info_query(tm, link_id):
    url = "/info/link/" + link_id
    opslog = logger.get_logger()
    table_str = "ops_link"
    link_schema = tm.schema_dict[table_str]

    link_info = get_object_info(tm, table_str, link_id)
    if link_info is not None:
        endpt_refs = []
        children_refs = []
        endpts = get_related_objects(
            tm,
            "ops_link_interfacevlan",
            "link_id",
            link_id)
        for endpt_i in endpts:
            endpt_refs.append(get_refs(tm, "ops_interfacevlan", endpt_i))
        # get parent info
        parent_id = link_info[
            tm.get_column_from_schema(
                link_schema,
                'parent_link_id')]
        if parent_id is None:
            parent_ref = None
        else:
            parent_ref = get_refs(tm, table_str, parent_id)
        # same for children
        children_ids = get_related_objects(
            tm,
            "ops_link",
            "parent_link_id",
            link_id)
        for child_id in children_ids:
            children_refs.append(get_refs(tm, table_str, child_id))

        return json.dumps(get_link_info_dict(
            link_schema, link_info, endpt_refs, parent_ref, children_refs))

    else:
        errStr = "link not found: " + link_id
        opslog.debug(errStr)
        return json.dumps(create_json_error_response(errStr, url))


# Main handle for experiment queries
def handle_experiment_info_query(tm, exp_id):
    url = "/info/experiment/" + exp_id
    opslog = logger.get_logger()
    table_str = "ops_experiment"
    exp_schema = tm.schema_dict[table_str]

    exp_info = get_object_info(tm, table_str, exp_id)

    if exp_info is not None:
        group_id = exp_info[
            tm.get_column_from_schema(
                exp_schema,
                "experimentgroup_id")]
        group_refs = get_related_objects_refs(
            tm,
            "ops_experimentgroup",
            "id",
            group_id,
            ("selfRef",
             "id"))
        metrics_ids = get_related_objects_refs(tm,
                                               "ops_experiment_metricsgroup_relation",
                                               "group_id",
                                               exp_info[
                                                   tm.get_column_from_schema(
                                                       exp_schema,
                                                       'metricsgroup_id')],
                                               ("id", "period")
                                               )
        return json.dumps(
            get_experiment_info_dict(exp_schema, exp_info, group_refs[0], metrics_ids))
    else:
        errStr = "experiment not found: " + exp_id
        opslog.debug(errStr)
        return json.dumps(create_json_error_response(errStr, url))


def handle_experimentgroup_info_query(tm, expgroup_id):
    url = "/info/experimentgroup/" + expgroup_id
    opslog = tm.logger
    table_str = "ops_experimentgroup"
    expgroup_schema = tm.schema_dict[table_str]

    expgroup_info = get_object_info(tm, table_str, expgroup_id)

    if expgroup_info is not None:
        return json.dumps(
            get_experiment_group_info_dict(expgroup_schema, expgroup_info))
    else:
        errStr = "experiment group not found: " + expgroup_id
        opslog.debug(errStr)
        return json.dumps(create_json_error_response(errStr, url))

# Main handle opsconfig info queries


def handle_opsconfig_info_query(tm, opsconfig_id, monitoring_version):
    url = "/info/opsconfig/" + opsconfig_id
    opslog = logger.get_logger()
    if opsconfig_id == "geni-prod":
        json_dict = json.load(open(tm.config_path + "opsconfig.json"))
        json_dict["version"] = monitoring_version
        json_dict['ts'] = int(time.time() * 1000000)
        return json.dumps(json_dict)
    else:
        errStr = "opsconfig not found: " + opsconfig_id
        opslog.debug(errStr)
        return json.dumps(create_json_error_response(errStr, url))


# Argument checker for tsdata queries

# Checks the filters for data queries. It needs a filters dictionary
# with ts, eventType, and obj keys
def check_data_query_keys(q_dict):
    opslog = logger.get_logger()
    if "filters" not in q_dict:
        opslog.debug(
            str(q_dict) +
            "\n has dictionary error.  It is missing filters key")
        return (False, "query: " + str(q_dict) +
                "<br><br>has dictionary error.  It is missing filters key")

    missing_keys = []
    if "ts" not in q_dict["filters"]:
        missing_keys.append("ts")
    if "eventType" not in q_dict["filters"]:
        missing_keys.append("eventType")
    if "obj" not in q_dict["filters"]:
        missing_keys.append("obj")

    if len(missing_keys) > 0:
        opslog.debug(
            str(q_dict) +
            "\n has dictionary error. It is missing keys: " +
            str(missing_keys))
        return (False, "query: " + str(q_dict) +
                "<br><br>has dictionary error.  It is missing keys: " + str(missing_keys))

    return (True, None)


def should_include_json_field(schema, info_row, column):
    """
    Function to determine whether or not a particular column of the information for an object
    should be included in the json response given the knowledge we have of the schema.
    :param schema: the schema for the corresponding table (in the usual format)
    :param info_row: the row of information from the table
    :param column: the index of the column in the schema and row to consider.
    :return: True if the value for that column shold be included, False otherwise.
    """
    condition = (
        info_row[column] is not None) or (
        (info_row[column] is None) and schema[column][2])
    if len(schema[column]) == 3:
        return condition
    elif len(schema[column]) == 4:
        return condition or schema[column][3]

# Form response dictionary functions

# Forms interface info dictionary (to be made to JSON)


def get_interface_info_dict(schema, info_row, parent_if_ref, address_schema, address_rows,
                            metrics_ids):

    json_dict = {}
    # NOT all of info_row goes into top level dictionary
    for col_i in range(len(schema)):
        if should_include_json_field(schema, info_row, col_i):
            if schema[col_i][0].startswith("properties$"):
                # parse off properties$
                json_dict[
                    "ops_monitoring:" +
                    schema[col_i][0].split("$")[1]] = info_row[col_i]
            else:
                if schema[col_i][0] == 'parent_interface_id':
                    continue
                if schema[col_i][0] == 'node_id':
                    continue
                # Not including metricsgroup_id column.
                if schema[col_i][0] == 'metricsgroup_id':
                    continue
                json_dict[schema[col_i][0]] = info_row[col_i]

    if parent_if_ref:
        json_dict["parent_interface"] = {
            "href": parent_if_ref[0],
            "urn": parent_if_ref[1]}

    # construct the list of addresses
    json_address_list = []
    for address_row in address_rows:
        json_addr = {}
        for col_i in range(len(address_schema)):
            fieldname = address_schema[col_i][0]
            if ((address_row[col_i] is not None) or
                    ((address_row[col_i] is None) and address_schema[col_i][2])):
                if fieldname != "interface_id":
                    # interface_id field doesn't go in the json response
                    # all other fields go in the json response
                    json_addr[fieldname] = address_row[col_i]
        json_address_list.append(json_addr)

    if len(json_address_list) > 0:
        json_dict["addresses"] = json_address_list

    reported_metrics_list = list()
    if metrics_ids:
        for metric in metrics_ids:
            reported_metric = dict()
            reported_metric["metric"] = "ops_monitoring:" + metric[0]
            reported_metric["period"] = metric[1]
            reported_metrics_list.append(reported_metric)
    json_dict["reported_metrics"] = reported_metrics_list

    return json_dict


# Forms experiment info dictionary (to be made to JSON)
def get_experiment_info_dict(schema, info_row, group_ref, metrics_ids):

    json_dict = {}
    # NOT all of info_row goes into top level dictionary
    for col_i in range(len(schema)):
        if should_include_json_field(schema, info_row, col_i):
            if schema[col_i][0] == "source_aggregate_urn":
                src_agg_urn = info_row[col_i]
            elif schema[col_i][0] == "source_aggregate_href":
                src_agg_href = info_row[col_i]
            elif schema[col_i][0] == "destination_aggregate_urn":
                dest_agg_urn = info_row[col_i]
            elif schema[col_i][0] == "destination_aggregate_href":
                dest_agg_href = info_row[col_i]
            elif schema[col_i][0] == 'externalcheck_id':
                continue
            elif schema[col_i][0] == "experimentgroup_id":
                continue
            # Not including metricsgroup_id column.
            elif schema[col_i][0] == 'metricsgroup_id':
                continue
            else:  # top level keys are equal to what is in DB
                json_dict[schema[col_i][0]] = info_row[col_i]

#    json_dict["source_aggregate"] = {"urn":src_agg_urn,"href":src_agg_href}
    if (src_agg_urn is not None) or (src_agg_href is not None):
        json_dict["source_aggregate"] = {}
        if (src_agg_urn is not None):
            json_dict["source_aggregate"]["urn"] = src_agg_urn
        if (src_agg_href is not None):
            json_dict["source_aggregate"]["href"] = src_agg_href

#    json_dict["destination_aggregate"] = {"urn":dest_agg_urn,"href":dest_agg_href}
    if (dest_agg_urn is not None) or (dest_agg_href is not None):
        json_dict["destination_aggregate"] = {}
        if (dest_agg_urn is not None):
            json_dict["destination_aggregate"]["urn"] = dest_agg_urn
        if (dest_agg_href is not None):
            json_dict["destination_aggregate"]["href"] = dest_agg_href

    if group_ref is not None:
        json_dict["experiment_group"] = dict()
        json_dict["experiment_group"]["href"] = group_ref[0]
        json_dict["experiment_group"]["id"] = group_ref[1]

    reported_metrics_list = list()
    if metrics_ids:
        for metric in metrics_ids:
            reported_metric = dict()
            reported_metric["metric"] = "ops_monitoring:" + metric[0]
            reported_metric["period"] = metric[1]
            reported_metrics_list.append(reported_metric)
    json_dict["reported_metrics"] = reported_metrics_list

    return json_dict


# Forms interfacevlan info dictionary (to be made to JSON)
def get_interfacevlan_info_dict(schema, info_row, if_ref, metrics_ids):

    json_dict = {}

    # NOT all of info_row goes into top level dictionary
    for col_i in range(len(schema)):
        if should_include_json_field(schema, info_row, col_i):
            if schema[col_i][0] == "interface_id":
                continue
            # Not including metricsgroup_id column.
            if schema[col_i][0] == 'metricsgroup_id':
                continue
            json_dict[schema[col_i][0]] = info_row[col_i]

    if if_ref is not None:
        json_dict["interface"] = dict()
        json_dict["interface"]["href"] = if_ref[0]
        json_dict["interface"]["urn"] = if_ref[1]

    reported_metrics_list = list()
    if metrics_ids:
        for metric in metrics_ids:
            reported_metric = dict()
            reported_metric["metric"] = "ops_monitoring:" + metric[0]
            reported_metric["period"] = metric[1]
            reported_metrics_list.append(reported_metric)
    json_dict["reported_metrics"] = reported_metrics_list

    return json_dict


def get_experiment_group_info_dict(schema, info_row):

    json_dict = dict()
    # NOT all of info_row goes into top level dictionary
    for col_i in range(len(schema)):
        if should_include_json_field(schema, info_row, col_i):
            json_dict[schema[col_i][0]] = info_row[col_i]
    return json_dict

# Forms user info dictionary (to be made to JSON)


def get_user_info_dict(schema, info_row, auth_ref):

    json_dict = {}

    # NOT all of info_row goes into top level dictionary
    for col_i in range(len(schema)):
        if should_include_json_field(schema, info_row, col_i):
            if schema[col_i][0] == "authority_id":
                continue
            else:
                json_dict[schema[col_i][0]] = info_row[col_i]

    json_dict["authority"] = dict()
    json_dict["authority"]["href"] = auth_ref[0]
    json_dict["authority"]["urn"] = auth_ref[1]

    return json_dict


# Forms node info dictionary (to be made to JSON)
def get_node_info_dict(
        schema, info_row, interface_refs, parent_node_ref, metrics_ids):

    json_dict = {}

    # Not all of info_row goes into top level dictionary
    for col_i in range(len(schema)):
        if should_include_json_field(schema, info_row, col_i):
            if schema[col_i][0].startswith("properties$"):
                # parse off properties$
                json_dict[
                    "ops_monitoring:" +
                    schema[col_i][0].split("$")[1]] = info_row[col_i]
            else:
                # Not including parent_node_id column.
                if schema[col_i][0] == 'parent_node_id':
                    continue
                # Not including aggregate_id column.
                if schema[col_i][0] == 'aggregate_id':
                    continue
                # Not including metricsgroup_id column.
                if schema[col_i][0] == 'metricsgroup_id':
                    continue
                json_dict[schema[col_i][0]] = info_row[col_i]

    if interface_refs:
        json_dict["interfaces"] = []
        for interface_ref in interface_refs:
            if len(interface_ref) > 0:
                json_dict["interfaces"].append(
                    {"href": interface_ref[0], "urn": interface_ref[1]})
    if parent_node_ref:
        json_dict["parent_node"] = {
            "href": parent_node_ref[0],
            "urn": parent_node_ref[1]}
    reported_metrics_list = list()
    if metrics_ids:
        for metric in metrics_ids:
            reported_metric = dict()
            reported_metric["metric"] = "ops_monitoring:" + metric[0]
            reported_metric["period"] = metric[1]
            reported_metrics_list.append(reported_metric)
    json_dict["reported_metrics"] = reported_metrics_list

    return json_dict


# Forms sliver info dictionary (to be made to JSON)
def get_sliver_info_dict(schema, info_row, resource_refs, agg_refs):

    json_dict = {}

    # NOT all of info_row goes into top level dictionary
    for col_i in range(len(schema)):
        if should_include_json_field(schema, info_row, col_i):
            if schema[col_i][0] == "aggregate_id":
                continue
            json_dict[schema[col_i][0]] = info_row[col_i]

    json_dict["aggregate"] = {"href": agg_refs[0], "urn": agg_refs[1]}

#    json_dict["aggregate"] = {"urn":agg_urn,"href":agg_href}
#     if (agg_urn is not None) or (agg_href is not None):
#         json_dict["aggregate"] = {}
#         if (agg_urn is not None):
#             json_dict["aggregate"]["urn"] = agg_urn
#         if (agg_href is not None):
#             json_dict["aggregate"]["href"] = agg_href

#   json_dict["resource"] = {"resource_type": resource_type,
#                            "urn":  resource_urn,
#                            "href": resource_href }
    json_dict["resources"] = resource_refs

    return json_dict


# Forms aggregate info dictionary (to be made to JSON)
def get_aggregate_info_dict(schema, info_row, res_refs, slv_refs,
                            monitoring_version, metrics_ids):
    json_dict = {}

    # All of info_row goes into top level dictionary
    for col_i in range(len(schema)):
        if should_include_json_field(schema, info_row, col_i):
            # Not including metricsgroup_id column.
            if schema[col_i][0] == 'metricsgroup_id':
                continue
            json_dict[schema[col_i][0]] = info_row[col_i]

    if res_refs:
        json_dict["resources"] = []
        for res_ref in res_refs:
            if len(res_ref) > 0:
                json_dict["resources"].append({"href": res_ref[0],
                                               "urn": res_ref[1],
                                               "resource_type": res_ref[2]})

    if slv_refs:
        json_dict["slivers"] = []
        for slv_ref in slv_refs:
            if len(slv_ref) > 0:
                json_dict["slivers"].append(
                    {"href": slv_ref[0], "urn": slv_ref[1]})

    json_dict["monitoring_version"] = monitoring_version

    reported_metrics_list = list()
    if metrics_ids:
        for metric in metrics_ids:
            reported_metric = dict()
            reported_metric["metric"] = "ops_monitoring:" + metric[0]
            reported_metric["period"] = metric[1]
            reported_metrics_list.append(reported_metric)
    json_dict["reported_metrics"] = reported_metrics_list

    return json_dict

# Forms external check store info dictionary (to be made to JSON)


def get_externalcheck_info_dict(
        schema, info_row, exp_refs, mon_agg_refs, monitoring_version):

    json_dict = {}

    # All of info_row goes into top level dictionary
    for col_i in range(len(schema)):
        if should_include_json_field(schema, info_row, col_i):
            json_dict[schema[col_i][0]] = info_row[col_i]

    json_dict["experiments"] = []
    if exp_refs:
        for exp_ref in exp_refs:
            if len(exp_ref) > 0:
                json_dict["experiments"].append({"href": exp_ref[0]})

    json_dict["monitored_aggregates"] = []
    if mon_agg_refs:
        for mon_agg_ref in mon_agg_refs:
            if len(mon_agg_ref) > 0:
                mon_agg = {"id": mon_agg_ref[0], "href": mon_agg_ref[1]}
                reported_metrics_list = list()
                if mon_agg_ref[2]:
                    for metric in mon_agg_ref[2]:
                        reported_metric = dict()
                        reported_metric[
                            "metric"] = "ops_monitoring:" + metric[0]
                        reported_metric["period"] = metric[1]
                        reported_metrics_list.append(reported_metric)
                mon_agg['reported_metrics'] = reported_metrics_list
                json_dict["monitored_aggregates"].append(mon_agg)

    json_dict["monitoring_version"] = monitoring_version

    return json_dict


# Forms link info dictionary (to be made to JSON)
def get_link_info_dict(
        schema, info_row, endpt_refs, parent_ref, children_refs):

    json_dict = {}

    # All of info_row goes into top level dictionary
    for col_i in range(len(schema)):
        if should_include_json_field(schema, info_row, col_i):
            # Not including aggregate_id column.
            if schema[col_i][0] == 'aggregate_id':
                continue
            # Not including parent_link_id column.
            elif schema[col_i][0] == 'parent_link_id':
                continue
            json_dict[schema[col_i][0]] = info_row[col_i]

    if endpt_refs:
        json_dict["endpoints"] = []
        for endpt_ref in endpt_refs:
            if len(endpt_ref) >= 2:
                json_dict["endpoints"].append(
                    {"href": endpt_ref[0], "urn": endpt_ref[1]})

    if parent_ref:
        if len(parent_ref) >= 2:
            json_dict["parent"] = {"href": parent_ref[0], "urn": parent_ref[1]}

    if children_refs:
        json_dict["children"] = []
        for child_ref in children_refs:
            if len(child_ref) >= 2:
                json_dict["children"].append(
                    {"href": child_ref[0], "urn": child_ref[1]})

    return json_dict


# Forms slice info dictionary (to be made to JSON)
def get_slice_info_dict(schema, info_row, user_refs, auth_ref):

    json_dict = {}

    # NOT all of info_row goes into top level dictionary
    for col_i in range(len(schema)):
        if should_include_json_field(schema, info_row, col_i):
            if schema[col_i][0] == "authority_id":
                continue
            else:
                json_dict[schema[col_i][0]] = info_row[col_i]

        json_dict["authority"] = dict()
        json_dict["authority"]["href"] = auth_ref[0]
        json_dict["authority"]["urn"] = auth_ref[1]

    if user_refs:
        json_dict["members"] = []
        for member_ref in user_refs:
            if len(member_ref) > 0:
                json_dict["members"].append(
                    {"href": member_ref[0], "urn": member_ref[1], "role": member_ref[2]})

    return json_dict


# Forms authority info dictionary (to be made to JSON)
def get_authority_info_dict(
        schema, info_row, user_refs, slice_refs, monitoring_version):

    json_dict = {}

    # All of info_row goes into top level dictionary
    for col_i in range(len(schema)):
        if should_include_json_field(schema, info_row, col_i):
            json_dict[schema[col_i][0]] = info_row[col_i]

    if user_refs:
        json_dict["users"] = []
        for user_ref in user_refs:
            if len(user_ref) > 0:
                json_dict["users"].append(
                    {"href": user_ref[0], "urn": user_ref[1]})

    if slice_refs:
        json_dict["slices"] = []
        for slice_ref in slice_refs:
            if len(slice_ref) > 0:
                json_dict["slices"].append(
                    {"href": slice_ref[0], "urn": slice_ref[1]})

    json_dict["monitoring_version"] = monitoring_version

    return json_dict


# SQL query functions

# Gets object info where an object can be anything (node, aggregate,
# interface, sliver
def get_object_info(tm, table_str, obj_id):
    """
    Method to get the database record of an object with a specific id in a given table.
    :param tm: the instance of TableManager to use
    :param table_str: the name of the table to query
    :param obj_id: the id of the object being looked up.
    :return: a list of data corresponding to the object information,
    or None if no object was found matching the given id.
    """
    res = None
    q_res = tm.query(
        "select * from " +
        table_str +
        " where id = '" +
        obj_id +
        "' order by ts desc limit 1")
    if q_res is not None:
        res = q_res[0]  # first (and only) row...
    return res

# Gets event types for an object


def get_events_list(tm):
    return tm.query(
        "select object_type, name, id, ts, v, units from ops_opsconfig_event")

# Gets info for an object


def get_info_list(tm):
    return tm.query("select tablename, schemaarray from ops_opsconfig_info")


# Gets related objects
def get_related_objects(tm, table_str, colname_str, id_str, id_column="id"):

    q_res = tm.query("select distinct " + tm.get_column_name(id_column) + " from "
                     + table_str + " where " + colname_str + " = '" + id_str + "'")
    res = []
    if q_res is not None:
        for res_i in range(len(q_res)):
            res.append(q_res[res_i][0])  # gets first of single tuple

    return res


def get_related_objects_refs(
        tm, table_str, colname_str, id_str, column_names=("selfRef", "urn")):
    """
    Query a table for objects related to a given id and by default, return the selfRef
    and urn information about all of the objects.
    :param tm: table manager to use for the query
    :param table_str: table to query
    :param colname_str: column name of that table in which to look for id
    :param id_str: id to look for in the given column
    :param column_names: tuple representing the names of the columns that should
    be returned.
    :return: a tuple of tuples.  Each inner tuple represents by default the (selfRef, urn) pair
            that matched (was related by id) from the given table. If column_names was specified
            each inner tuple will contain the values of these columns.
    """
    col_selection = ""
    for col_i in range(len(column_names)):
        if col_i > 0:
            col_selection += ", "
        col_selection += tm.get_column_name(column_names[col_i])

    q_res = tm.query("SELECT DISTINCT " + col_selection +
                     " FROM " + table_str + " WHERE " + colname_str + " = '" + id_str + "'")
    return q_res


# Gets related objects
def get_related_objects_full(tm, table_str, colname_str, id_str):
    """
    Query a table for objects related to a given id and return full
    information (complete table rows) about all of them.
    :param tm: table manager to use for the query
    :param table_str: table to query
    :param colname_str: column name of that table in which to look for id
    :param id_str: id to look for in the given column
    :return: a tuple of tuples.  Each inner tuple represents one row that
             matched (was related by id) from the given table.
    """
    q_res = tm.query("select * from " + table_str + " where " +
                     tm.get_column_name(colname_str) + " = '" + id_str + "'")
    res = []
    if q_res is not None:
        for res_i in range(len(q_res)):
            res.append(q_res[res_i])

    return res


# Get references of objects TODO refactor similar functions
def get_refs(tm, table_str, object_id, column_names=("selfRef", "urn")):

    col_selection = ""
    for col_i in range(len(column_names)):
        if col_i > 0:
            col_selection += ", "
        col_selection += tm.get_column_name(column_names[col_i])

    refs = []
    q_res = tm.query("select " + col_selection + " from " + table_str +
                     " where id = '" + object_id + "' limit 1")
    if q_res is not None:
        refs = q_res[0]
    return refs


# Get self reference only TODO refactor similar functions
def get_monitored_aggregates(tm, extck_id):

    res = tm.query("SELECT ops_aggregate.id, ops_aggregate." + tm.get_column_name("selfRef") +
                   ", ops_externalcheck_monitoredaggregate.metricsgroup_id"
                   " FROM ops_aggregate, ops_externalcheck_monitoredaggregate " +
                   "WHERE ops_externalcheck_monitoredaggregate.externalcheck_id = '" + extck_id + "' AND " +
                   "ops_externalcheck_monitoredaggregate.id = ops_aggregate.id")
    return res


# special get of refs for slice users which includes role
def get_slice_user_refs(tm, slice_id, user_id):

    refs = list()
    q_res = tm.query(
        "SELECT " +
        tm.get_column_name("selfRef") +
        ", urn FROM ops_user WHERE id = '" +
        user_id +
        "' limit 1")
    if q_res is not None:
        refs.extend(q_res[0])
        q_res = tm.query(
            "select role from ops_slice_user where id = '" +
            user_id +
            "' and slice_id = '" +
            slice_id +
            "' limit 1")
        if q_res is not None:
            refs.extend(q_res[0])
    return refs


# special get of refs for opsconfig aggregates which includes amtype
# TODO refactor similar functions
def get_opsconfig_aggregate_refs(tm, table_str, opsconfig_id):

    # Unused method...
    refs = []
    q_res = tm.query("select " + tm.get_column_name("selfRef") + ", urn, amtype from " + table_str +
                     " where id = '" + opsconfig_id + "' limit 1")
    if q_res is not None:
        refs = q_res[0]

    return refs


# builds timestamp filter as a where clause for SQL statement
def build_ts_where_str(ts_dict):
    opslog = logger.get_logger()
    ts_where_str = ""
    ts_filters = []

    if 'gte' not in ts_dict and 'gt' not in ts_dict:
        opslog.warning("must past a ts filter for (lt or lte) and (gt or gte)")
        opslog.warning("missing gt or gte filter")
        return ts_where_str

    if 'lte' not in ts_dict and 'lt' not in ts_dict:
        opslog.warning("must past a ts filter for (lt or lte) and (gt or gte)")
        opslog.warning("missing lt or lte filter")
        return ts_where_str

    try:
        for ts_k in ts_dict:
            ts_v = ts_dict[ts_k]
            if ts_k == 'gte':
                ts_filters.append("ts >= " + str(ts_v))
            elif ts_k == 'gt':
                ts_filters.append("ts > " + str(ts_v))
            elif ts_k == 'lte':
                ts_filters.append("ts <= " + str(ts_v))
            elif ts_k == 'lt':
                ts_filters.append("ts < " + str(ts_v))
    except Exception as e:
        opslog.warning(str(e), "ts filters has invalid key or value:")

    try:
        ts_where_str = ts_filters[0] + " and " + ts_filters[1]
    except Exception as e:
        opslog.warning(
            str(e),
            "must past a ts filter for (lt or lte) and (gt or gte)")

    return ts_where_str


def get_tsdata(tm, event_type, obj_type, obj_id, ts_where_str):
    res = None
    q_res = tm.query("select ts,v from ops_" + obj_type + "_" + event_type +
                     " where id = '" + obj_id + "' and " + ts_where_str)
    if q_res is not None:
        res = []
        for q_res_i in xrange(len(q_res)):  # parsing result "<ts>,<v>"
            res.append({"ts": q_res[q_res_i][0], "v": q_res[q_res_i][1]})
    return res


def get_object_schema(tm, obj_type, obj_id):
    res = None
    q_res = tm.query("select " + tm.get_column_name("$schema") + " from ops_" + obj_type +
                     " where id = '" + obj_id + "' order by ts desc limit 1")
    if q_res is not None:
        res = q_res[0][0]

    return res


def get_object_ids(tm, table_str):
    """
    Get all unique object ids from a table.
    :param table_str: the table to search for ids in
    :return: a list of object ids that appear in the given table.
    """
    obj_ids = []
    q_res = tm.query("select distinct id from " + table_str)
    if q_res is not None:
        obj_ids = [x[0] for x in q_res]

    return obj_ids


def create_json_error_response(message, url):
    error_dict = dict()
    error_dict["$schema"] = __SCHEMA_BASE + "error#"
    error_dict["error_message"] = message
    error_dict["origin_url"] = url
    return error_dict


def main():
    print "no unit test"

if __name__ == "__main__":
    main()
