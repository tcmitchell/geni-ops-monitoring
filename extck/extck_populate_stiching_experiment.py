#!/usr/bin/env python
#----------------------------------------------------------------------
# Copyright (c) 2015 Raytheon BBN Technologies
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
import sys
import time
import os
import tempfile
import subprocess
import shlex

extck_path = os.path.abspath(os.path.dirname(__file__))
top_path = os.path.dirname(extck_path)
common_path = os.path.join(top_path, "common")
config_path = os.path.join(top_path, "config")
sys.path.append(common_path)
sys.path.append(extck_path)
import extck_config
import logger
import table_manager
opslogger = logger.get_logger(config_path)
config = extck_config.ExtckConfigLoader(opslogger)


def name_stitch_path_experiment(am_source, am_dest):
    return am_source + "_to_" + am_dest + "_stitching"

AM_URL1_STR = "AM_URN1"
AM_URL2_STR = "AM_URN2"

def expand_template_line(line, am_urn1, am_urn2):
    res = line.replace(AM_URL1_STR, am_urn1)
    res = res.replace(AM_URL2_STR, am_urn2)
    return res

def write_tmp_rspec(outfile_handle, rspec_template_file_content, am_urn1, am_urn2):
    for line in rspec_template_file_content:
        os.write(outfile_handle, expand_template_line(line, am_urn1, am_urn2))
    os.close(outfile_handle)

def get_am_details_from_urn(am_urn, tbl_mgr):
    am_type = None
    am_id = None
    am_url = None
    res = tbl_mgr.query('select id, ' + tbl_mgr.get_column_name('selfRef') + ' from ops_aggregate where urn=\'' + am_urn + '\'')
    if res is not None:
        am_id = res[0][0]
        am_url = res[0][1]
        res = tbl_mgr.query('select type from extck_aggregate where aggregate_id=\'' + am_id + '\'')
        if res is not None:
            am_type = res[0][0]

    return (am_type, am_id, am_url)

def get_stitch_sites_details(tbl_mgr):
    tmp_site_urns = config.get_stitch_sites_urns()
    # Only retain compute aggregates URNs
    site_info = list()
    for urn in tmp_site_urns:
        (am_type, am_id, am_url) = get_am_details_from_urn(urn, tbl_mgr)
        if is_compute_aggregate(am_type):
            site_info.append((am_id, urn, am_url))
    return site_info

def is_compute_aggregate(am_type):
    return am_type in ('protogeni', 'instageni', 'exogeni')

def execute_stitcher_command(rspec_filename, slicename, projectname, user_dir):
    available = 0
    (fh, tmpFilename) = tempfile.mkstemp(suffix='.xml', prefix='stitchOutput', dir=user_dir)
    os.close(fh)
    os.remove(tmpFilename)

    cmd_str = config.get_stitch_path_available_cmd(projectname, slicename, rspec_filename, tmpFilename)
    args = shlex.split(cmd_str)
    opslogger.debug("About to execute \'%s\'" % cmd_str)
    ret_val = subprocess.call(args)
    if ret_val == 0:
        available = 1
    else:
        opslogger.warning("Command \'%s\' returned error code %d" % (cmd_str, ret_val))

    return available



def main():
    db_name = "local"
    tbl_mgr = table_manager.TableManager(db_name, config_path)
    tbl_mgr.poll_config_store()

    # getting content of template rspec
    template_filename = os.path.join(extck_path, config.get_stitcher_rspec_template_filename())
    fh = open(template_filename, "r")
    template_content = list(fh)
    fh.close()

    slicename = config.get_stitch_experiment_slicename()
    sliceinfo = config.get_experiment_slices_info()[slicename]
    projectname = sliceinfo[2]

    site_info = get_stitch_sites_details(tbl_mgr)

    user_dir = config.get_user_path()

    table_name = 'ops_experiment_is_stitch_path_available'
    for idx1 in range(len(site_info)):
        site1 = site_info[idx1]
        for idx2 in range(idx1 + 1, len(site_info)):
            site2 = site_info[idx2]
            opslogger.debug("Checking on stitching path from %s to %s" % (site1[0], site2[0]))
            (fh, tmpFilename) = tempfile.mkstemp(suffix='.rspec', prefix='tmpstitch', dir=user_dir)
            write_tmp_rspec(fh, template_content, site1[1], site2[1])
            # launch stitcher with no reservation command and get result
            path_available = execute_stitcher_command(tmpFilename, slicename, projectname, user_dir)
            if path_available == 0:
                opslogger.warning("Stitching path from %s to %s could NOT be successfully computed" % (site1[0], site2[0]))
            else:
                opslogger.debug("Stitching path from %s to %s was successfully computed" % (site1[0], site2[0]))
            # remove tmp file.
            os.remove(tmpFilename)
            # insert record
            ts = int(time.time() * 1000000)
            experiment_id = name_stitch_path_experiment(site1[0], site2[0])
            val_str = "(\'" + experiment_id + "\', " + str(ts) + ", " + str(path_available) + ")"
            tbl_mgr.insert_stmt(table_name, val_str)



if __name__ == "__main__":
    main()
