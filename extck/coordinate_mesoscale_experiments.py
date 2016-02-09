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
import sys
import os
import time
import tempfile
import multiprocessing
import multiprocessing.pool

import pinger

extck_path = os.path.abspath(os.path.dirname(__file__))
top_path = os.path.dirname(extck_path)
common_path = os.path.join(top_path, "common")
config_path = os.path.join(top_path, "config")
sys.path.append(common_path)
sys.path.append(extck_path)

import table_manager
import opsconfig_loader
import extck_config
import extck_store


def execute_cmd(cmdStr, opslogger, lock):
    lock.acquire()
    opslogger.debug("about to execute: " + cmdStr)
    lock.release()
    os.system(cmdStr)

def sync_up_files(local_path, remote_path, username, remote_addr, remote_port, ssh_key_file, opslogger, lock):
    rsyncStr = "rsync -z -e \"ssh -o PasswordAuthentication=no -i " + ssh_key_file + " -p " + remote_port + "\" " + \
            local_path + " " + username + "@" + remote_addr + ":" + remote_path
    execute_cmd(rsyncStr, opslogger, lock)

PING_FAILURE_STR = str(pinger.PING_FAILURE_VALUE) + ")"
LEN_PING_FAILURE_STR = len(PING_FAILURE_STR)

def insert_ping_times(outputfile, tbl_mgr, table_str, lock, publish_negative_value):
    file_handle = open(outputfile, 'r')
    val_str = ""

    first = True
    for line in file_handle:
        # if the ping failed (delay set to -1 in pinger.py) we're not inserting the value.
        line = line.strip()
        if not publish_negative_value and (line[-LEN_PING_FAILURE_STR:] == PING_FAILURE_STR):
            continue
        if first:
            first = False
        else:
            val_str += ","
        val_str += line
    if val_str != "":
        lock.acquire()
        tbl_mgr.insert_stmt(table_str, val_str)
        lock.release()

def get_vm_address_and_port_for_site(ext_config, ping_site, ping_set, username, slicename, slices,
                                     lock, table_mgr, aggregateStores, nickCache, user_cred_file):
    gcf_path = ext_config.get_gcf_path()
    sys.path.append(os.path.join(gcf_path, "examples"))
    address = None
    port = None
    import readyToLogin
    # slices dictionary contains arrays [URN, UUID, project] keyed by slice names
    project = slices[slicename][2]
    (_id, srcSiteName, _name) = pinger.get_ping_experiment_name(ping_set, ping_site, ping_site)
    (_urn, _store_url, am_url) = extck_store.getSiteInfo(nickCache, srcSiteName, aggregateStores)

    readyToLoginArgs = [ '-r', project,
                         '-a', am_url,
                         '--usercredfile', user_cred_file,
                         slicename
                        ]

    lock.acquire()
    # readyToLogin.main_no_print() is not thread-safe so executing it one thread at a time
    # In addition it does a sys.exit() call when the AM is unreachable!
    table_mgr.logger.debug("Looking for login info for project '%s', slice '%s', username '%s' and site '%s' " % (project, slicename, username, am_url))
    try:
        loginInfoDict, _keyList = readyToLogin.main_no_print(argv=readyToLoginArgs)
    except SystemExit:
        loginInfoDict = None

    if loginInfoDict is not None:
        if loginInfoDict.has_key(am_url) and loginInfoDict[am_url].has_key('info'):
            for userinfo in loginInfoDict[am_url]['info']:
                if userinfo['username'] == username:
                    address = userinfo['hostname']
                    port = userinfo['port']
                    table_mgr.logger.debug("Found login info %s:%s for project '%s', slice '%s', username '%s' and site '%s' " \
                                           % (address, port, project, slicename, username, am_url))
                    break
        loginInfoDict.clear()  # so that successive calls do not interfere with one another
    lock.release()

    table_name = "extck_ping_login_info"
    table_schema = table_mgr.schema_dict[table_name]
    if address is None or port is None:
        # get them from the DB
        lock.acquire()
        table_mgr.logger.warning("Could not determine saved login information for project '%s', slice '%s', username '%s' and site '%s' " % (project, slicename, username, am_url))
        querystr = 'SELECT hostname, port FROM ' + table_name + ' WHERE project=\'' + \
                    project + '\' AND slice=\'' + slicename + '\' AND username=\'' + \
                    username + '\' AND site=\'' + am_url + '\''
        lock.release()
        result = table_mgr.query(querystr)
        if result is not None:
            address = result[0][0]
            port = result[0][1]
        else:
            lock.acquire()
            table_mgr.logger.warning("Could not find saved login information for project '%s', slice '%s', username '%s' and site '%s' " % (project, slicename, username, am_url))
            lock.release()
    else:
        # save them in the DB for a future use
        record = (project, slicename, username, am_url, address, port)
        if not table_mgr.upsert(table_name, table_schema, record,
                                (table_mgr.get_column_from_schema(table_schema, 'project'),
                                 table_mgr.get_column_from_schema(table_schema, 'slice'),
                                 table_mgr.get_column_from_schema(table_schema, 'username'),
                                 table_mgr.get_column_from_schema(table_schema, 'site')
                                 )):
            lock.acquire()
            table_mgr.logger.warning("Error while saving login information for project '%s', slice '%s', username '%s' and site '%s' " % (project, slicename, username, am_url))
            lock.release()

    return (address, port)

def run_remote_pings((ext_config, site, ping_set, ipConfigPathLocal,
                     ipConfigPathRemote, keyPath, pingerLocal, pingerRemote,
                     poolSize, initialPingCount, measurementPingCount, table_str,
                     lock, table_mgr, slices, aggregateStores, nickCache, user_cred_file)):


    # Get VM address and port
    slice_name = ext_config.get_experiment_source_ping_slice_name(ping_set, site)
    username = ext_config.get_username()
    (addr, port) = get_vm_address_and_port_for_site(ext_config, site, ping_set, username,
                                                    slice_name, slices, lock, table_mgr,
                                                    aggregateStores, nickCache, user_cred_file)
    if addr is None or port is None:
        lock.acquire()
        table_mgr.logger.warning("Failed to determine login information for ping set '%s' and site '%s'. Will skip ping tests." % (ping_set, site))
        lock.release()
        return
#     addr = ext_config.get_experiment_source_ping_vm_address(ping_set, site)
#     port = ext_config.get_experiment_source_ping_vm_port(ping_set, site)

    # First make sure the src site have the latest ips.conf and pinger.py
    # using rsync commands to avoid copying over & over the same files.
    sync_up_files(ipConfigPathLocal, ipConfigPathRemote, username, addr, port, keyPath, table_mgr.logger, lock)
    sync_up_files(pingerLocal, pingerRemote, username, addr, port, keyPath, table_mgr.logger, lock)

    remote_output_dir = ext_config.get_remote_output_dir()
    pref = "extck_tmp_"
    suff = ".pings"
    # clean up old tmp file in case some process was interrupted...
    # delete files older than 60 minutes, matching what we output.
    sshStr = "ssh -o PasswordAuthentication=no -i " + keyPath + " " + username + "@" + addr + " -p " + port + \
               " \"find " + remote_output_dir + " -mmin +60 -name '" + pref + "*" + suff + "' | xargs rm -vrf" + "\""
    execute_cmd(sshStr, table_mgr.logger, lock)

    publish_neg = ext_config.get_publish_negative_value_for_failed_ping()

    (fh, outputFileLocal) = tempfile.mkstemp(suffix=suff, prefix=pref, dir=ext_config.get_local_output_dir())
    os.close(fh)  # closing tmp file that was just created.
    filename = os.path.basename(outputFileLocal)
    outputFileRemote = os.path.join(remote_output_dir, filename)
    sshStr = "ssh -o PasswordAuthentication=no -i " + keyPath + " " + username + "@" + addr + " -p " + port + \
               " \"rm -f " + outputFileRemote + \
               " && python pinger.py -o " + outputFileRemote + " -c " + ipConfigPathRemote + " -s " + site + " -t " + ping_set + \
               " -p " + poolSize + " -i " + initialPingCount + " -m " + measurementPingCount + "\""
    execute_cmd(sshStr, table_mgr.logger, lock)

    scpStr = "scp -o PasswordAuthentication=no -i " + keyPath + " -P " + port + " " + username + "@" + addr + ":" + outputFileRemote + " " + outputFileLocal
    execute_cmd(scpStr, table_mgr.logger, lock)
    sshStr = "ssh -o PasswordAuthentication=no -i " + keyPath + " " + username + "@" + addr + " -p " + port + \
               " \"rm -f " + outputFileRemote + "\""
    execute_cmd(sshStr, table_mgr.logger, lock)

    insert_ping_times(outputFileLocal, table_mgr, table_str, lock, publish_neg)
    # Delete tmp file
    os.remove(outputFileLocal)

def main(argv):
    multiprocessing.util.log_to_stderr(multiprocessing.util.DEBUG)
    db_type = "local"

    tbl_mgr = table_manager.TableManager(db_type, config_path)

    tbl_mgr.poll_config_store()

    ocl = opsconfig_loader.OpsconfigLoader(config_path)

    aggregateStores = ocl.config_json['aggregatestores']
#     experiment_event_types = ocl.get_event_types()["experiment"]

    ext_config = extck_config.ExtckConfigLoader(tbl_mgr.logger)

    ipConfigPathLocal = os.path.join(extck_path, "ips.conf")
    ipConfigPathRemote = ext_config.get_ips_file_remote_location()
    pingerLocal = os.path.join(extck_path, "pinger.py")
    pingerRemote = ext_config.get_pinger_file_remote_location()
    keyPath = ext_config.get_ssh_key_file_location()
    poolSize = ext_config.get_experiment_ping_thread_pool_size()
    initialPingCount = ext_config.get_experiment_ping_initial_count()
    measurementPingCount = ext_config.get_experiment_ping_measurmentl_count()
    slices = ext_config.get_experiment_slices_info()

    nickCache = extck_store.AggregateNickCache(ext_config.get_nickname_cache_file_location())
    nickCache.parseNickCache()

    # Set up info about extra extck tables and establish them.
    ext_config.configure_extck_tables(tbl_mgr)

    # Relying on the fact that extck_populator.py has been run recently and has created the cached credentials file...
    user_cred_file = ext_config.get_user_credential_file()

    table_str = "ops_experiment_ping_rtt_ms"
    myLock = multiprocessing.Lock()

    argsList = []
    ping_sets = ext_config.get_experiment_ping_set()
    for ping_set in ping_sets:
        sources = ext_config.get_experiment_source_ping_for_set(ping_set)
        for site in sources:
            args = (ext_config, site, ping_set,
                    ipConfigPathLocal, ipConfigPathRemote, keyPath,
                    pingerLocal, pingerRemote,
                    poolSize, initialPingCount, measurementPingCount,
                    table_str, myLock, tbl_mgr, slices, aggregateStores,
                    nickCache, user_cred_file)
            argsList.append(args)
    pool = multiprocessing.pool.ThreadPool(processes=int(ext_config.get_experiment_coordination_thread_pool_size()))
    pool.map(run_remote_pings, argsList)
    # Purge data older than 168 hours (1 wk)
    old_ts = int((time.time() - 168 * 60 * 60) * 1000000)
    tbl_mgr.purge_old_tsdata(table_str, old_ts)

if __name__ == "__main__":
    main(sys.argv[1:])
