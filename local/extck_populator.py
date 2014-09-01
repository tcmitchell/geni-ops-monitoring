#!/usr/bin/python
#----------------------------------------------------------------------
# Copyright (c) 2014 Raytheon BBN Technologies
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
import json
import ConfigParser
import subprocess
from string import digits
from pprint import pprint as pprint
import os
import requests

##################################################
# geni-lib config for FOAM/FV listresources test #
geniLibConfigPath="/usr/local/geni-lib/samples"  #
geniLibPath="/usr/local/geni-lib"                #
sys.path.append(geniLibConfigPath)               #
sys.path.append(geniLibPath)                     #

import amcanary_config                           #
context = amcanary_config.buildContext()         #
from geni.aggregate.core import AM               #
##################################################

common_path = "../common/"
# input file with short-names and Urls aggregates 
# inputFile=open('/home/amcanary/src/gcf/agg_nick_cache.base')
inputFile=open('/home/amcanary/.bssw/geni/nickcache.json')
# dic to store short name and corresponding url 
# Format: shortname [fqdn]=[aggShortName,amtype, state, timestamp]
# shortName[urn]=[aggShortName, amType, selfRef, measRef, url, fqdn, schema, state, timestamp]
# where state is 0 for up and 1 for down
shortName={}

# Store cache of nickNames in here
# nickCache[urn]=[shortName, url]
nickCache ={}

sys.path.append(common_path)


import table_manager


class SiteOF(AM):
  def __init__ (self, name, url = None):
    super(SiteOF, self).__init__(name, url, "amapiv2", "foam")

def getOFState(context, site=None):
  try:
      ad = site.listresources(context) # Run listresources for a particular site
  except:
      print "Control plane connection to", site.name, "for FOAM/FV Offline"
      return str(0) # Can't reach the site via control path

  prtFlag=0 # Check to see if dpids have ports.
            # No ports on all dpids for a given switch indicates possible FV issues.
  for switch in ad.datapaths:
    if len(switch.ports) == 0:
      print "NO ports found on ", switch.dpid, ". FV may be hang or connection from dpid to FV is broken."
    else: # If any dpid has ports listed, FV is working for that switch
      prtFlag=1
      return str(prtFlag)
  return str(0) # All dpids on that switch had no ports. FV is down. 

class InfoPopulator():
    def __init__(self, tbl_mgr, url_base):

        self.tbl_mgr = tbl_mgr 
        self.url_base = url_base
        # steal config path from table_manager
        self.config_path = tbl_mgr.config_path

    def insert_agg_is_avail_datapoint(self,aggRow):
        # Insert into ops_externalcheck 
        agg_id = aggRow[0] # agg_id
        ts = aggRow[8]#str(int(time.time()*1000000))
        v = aggRow[7] 
        datapoint = [agg_id, ts, v]
        db_insert(self.tbl_mgr, "ops_aggregate_is_available", datapoint)  
        db_purge(self.tbl_mgr,"ops_aggregate_is_available")

    
def db_purge(tbl_mgr, table_str):
    old_ts = int((time.time()-168*60*60)*1000000) # Purge data older than 1 week (168 hours)
    tbl_mgr.purge_old_tsdata(table_str, old_ts)    


def db_insert(tbl_mgr, table_str, row_arr):
    val_str = "('"
    for val in row_arr:        
        val_str += val + "','" # join won't do this
    val_str = val_str[:-2] + ")" # remove last 2 of 3 chars: ',' and add )
    tbl_mgr.insert_stmt(table_str, val_str)
    
def getShortName(aggStores):

    nickCache=getNickCache()
   # print "aggStores", aggStores
    for aggregate in aggStores:
     #   break
        if aggregate['urn']=="urn:publicid:IDN+genirack.nyu.edu+authority+cm":
            continue
        # Do this for all aggregates with a data store 
     #   print ""
     #   print "agg", aggregate['amtype']
     #   print "aggUrn", aggregate['urn'] 

        if aggregate['amtype']=='instageni' or aggregate['amtype']=='protogeni':
        #    print "here",aggregate    
            aggDetails = handle_request(aggregate['href']) # Use url for site's store to query site
            selfRef = aggDetails['selfRef']
            measRef = aggDetails['measRef']
            urn = aggDetails['urn']
            schema = aggDetails['$schema']
            amType = "protogeni"
            aggShortName = aggDetails['id']
        #    print aggregate.keys()
            if aggregate.has_key('amurl'): # For non-prod aggregates
                url=aggregate['amurl']
            else:
                if nickCache.has_key(urn):
                    url=nickCache[urn][1]
                else:
                   # No point grabbing data for site without AM URL
                   print "Missing URL for ", aggShortName
                   continue

            cols=url.strip().split('/')
            cols1=cols[2].strip().split(':')
            fqdn=cols1[0]
            shortName[urn]=[aggShortName, amType, selfRef, measRef, url, fqdn, schema]

        elif aggregate['amtype'] == "network-aggregate": # Case for ion
            if nickCache.has_key(aggregate['urn']):
                aggDetails = handle_request(aggregate['href'])
                selfRef = aggDetails['selfRef']; measRef = aggDetails['measRef']
                urn = aggDetails['urn']; amType='myplc'; schema = aggDetails['$schema']
                aggShortName = aggDetails['id']; url=nickCache[urn][1]
                cols=url.strip().split('/'); cols1=cols[2].strip().split(':'); fqdn=cols1[0]
                shortName[urn]=[aggShortName, amType, selfRef, measRef, url, fqdn, schema]
        elif aggregate['amtype'] == "stitcher": # Special case
            selfRef = aggregate['href']; measRef = '';urn = aggregate['urn']
            amType = aggregate['amtype']
            schema = "http://www.gpolab.bbn.com/monitoring/schema/20140501/aggregate#"
            url="http://oingo.dragon.maxgigapop.net:8081/geni/xmlrpc"
            fqdn=''; aggShortName="scs"
            shortName[urn]=[aggShortName, amType, selfRef, measRef, url, fqdn, schema]
        else: # ExoGENI and FOAM
            selfRef = aggregate['href']
            measRef = ''
            urn = aggregate['urn']
            schema = "http://www.gpolab.bbn.com/monitoring/schema/20140501/aggregate#"
            amType = aggregate['amtype']

            if aggregate.has_key('amurl'): # For non-prod foam aggregates
                url = aggregate['amurl']
            else:
                if nickCache.has_key(urn):
                    url=nickCache[urn][1]
                else:
                    print "Missing URL for ", urn
                    continue

            # Get aggShortName
            if amType == "exogeni":
                cols=urn.strip().split(':')
                cols1=cols[3].strip().split('vmsite')
                aggShortName=cols1[0]+ "-eg"
                amType="orca" # Ask stephane to change this
            elif amType == "foam":
                cols=selfRef.strip().split('/')
                aggShortName=cols[5]

             # Get fqdn
            cols=url.strip().split('/')
            cols1=cols[2].strip().split(':')
            fqdn=cols1[0]
            shortName[urn]=[aggShortName, amType, selfRef, measRef, url, fqdn, schema]


    # Ask Stephane to set instageni AM type to protogeni and exogeni am type to orca
    # Ask Stephane to add amurl for EG aggregates
    # Ask Stephane to add amurl for OF EG aggregates
    #i=1
    return shortName 


def getNickCache():
    for line in inputFile: # Read in line
        if line[0]!='#' and line[0]!='[' and line[0]!='\n': # Don't read comments/junk
            cols = line.strip().split('=')
            aggShortName=cols[0]
            if aggShortName == "plcv3" or aggShortName == "plc3": # Only grab fqdn for aggShortName=plc
               continue
            aggShortName=formatShortName(aggShortName) # Grab shortname and convert to current format
            cols1=cols[1].strip().split(',')
            urn = cols1[0]
            url = cols1[1]
            nickCache[urn]=[aggShortName,url]
    return nickCache

def formatShortName(shortName):
  #  if len(shortName)>5:# Aggregate with 2 chars: ignore
    shortName = shortName.translate(None, digits) # Remove all #s froms shortName
    oldFormat = shortName.strip().split('-')
    suffix=['ig','eg', 'of', 'pg']  
    if len(oldFormat)==1: # For cases like "ion"
       return shortName
    for id in suffix:
        if oldFormat[0]==id and len(oldFormat) == 2: # For cases like gpo-ig
            newFormat= oldFormat[1]+"-"+id
            break 
        elif oldFormat[1]==id and len(oldFormat) == 2: # For cases like ig-gpo
            newFormat=shortName
            break
        elif oldFormat[0]==id and len(oldFormat) == 3: # For cases like ig-of-gpo
            newFormat= oldFormat[2] + '-' + id + '-' + oldFormat[1]
            break 
        elif oldFormat[1]==id and len(oldFormat) == 3: # For cases like gpo-ig-of
            newFormat= shortName
            break

    if newFormat == "i-of": # For i2-of case
        return "i2-of"
    else:
        return newFormat

def is_empty(any_structure): # Determine if "any_structure" is empty
    if any_structure:
       # print('Structure is not empty.')
        return False
    else:
       # print('Structure is empty.')
        return True
def getAMState(output):
    cols=output.strip().split(':')
    if cols[2] == " Timed out after 60 seconds": # Occurs if subprocess hangs 
        result ="0"
    elif cols[3]==" 0": # check for "returned: 0" output
        result="1" # Good result
    else:
        result="0" # Bad result   
    return result

def handle_request(url=None, cert_path=None):

    if url==None:
      #url='https://opsconfigdatastore.gpolab.bbn.com/info/opsconfig/geni-prod' 
      url='https://tamassos.gpolab.bbn.com/info/opsconfig/geni-prod'

    cert_path = '../collector/collector-gpo-withnpkey.pem'
    resp = None
    try:
        resp = requests.get(url, verify=False, cert=cert_path)
    except Exception, e:
        print "No response from local datastore at: " + url
        print e
        return None

    if resp:
        try:
            json_dict = json.loads(resp.content)
        except Exception, e:
            print "Could not load into JSON"
            print e
            return None

        return json_dict
    else:
        return None

def main():

    db_name = "local"
    config_path = "../config/"
    debug = False
    tbl_mgr = table_manager.TableManager(db_name, config_path, debug)
    tbl_mgr.poll_config_store()
    ip = InfoPopulator(tbl_mgr,"")
    
    # Grab urns and urls for all agg stores    
    aggRequest = handle_request()
    aggStores = aggRequest['aggregatestores']
    shortName=getShortName(aggStores)

    for urn in shortName:
        siteName = shortName[urn][0]
        amtype = shortName[urn][1]
        url=shortName[urn][4]  
        fqdn=shortName[urn][5]
        if amtype== "foam":
          site = SiteOF(siteName, url)
          state= getOFState(context, site)
        elif amtype== "stitcher": # Do something special
          continue 
        else:         
          p=subprocess.Popen(["/usr/local/bin/wrap_am_api_test", "genich",fqdn,amtype,"GetVersion"], stdout=subprocess.PIPE)            
          output, err = p.communicate()
          state=getAMState(output)
        shortName[urn].append(state)
        shortName[urn].append(str(int(time.time()*1000000)))
        ip.insert_agg_is_avail_datapoint(shortName[urn])
       
if __name__ == "__main__":
    main() 
