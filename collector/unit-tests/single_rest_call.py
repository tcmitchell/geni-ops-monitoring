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

'''
This program is designed to make it easier to debug a (local)datastore's 
output.  If the datastore's database tables are populated properly, then
everything will work fine.  This program enables debugging of this, since
debugging in the web-browser is no longer possible with the client 
certificate credential system.

This requires sudo pip install requests --upgrade

and

git clone https://github.com/sunlightlabs/validictory.git
to ops-monitoring/extern/validictory

'''

import json
import sys
import requests
import getopt

sys.path.append("../")
import response_validator

from pprint import pprint as pprint

def usage():
    print "Correct usage is:"
    print "python single_rest_call.py https://<datastore url>/info/<object_type>/<object_id>"
    print "hard code the location of your cert in main() for easier execution"
    sys.exit(-1)

def make_request_print_response(url, cert_path):

    resp = None
    json_dict = None

    try:
        resp = requests.get(url, verify=False, cert=cert_path)
    except Exception, e:
        print "No response from local datastore at: " + url
        print e

    if resp:
        try:
            json_dict = json.loads(resp.content)
        except Exception, e:
            print "Could not load into JSON",
            print resp.content
            print e

        pprint(json_dict)
    else:
        print "resp object is None from", url

    return json_dict



def main(argv): 

    # Hard coding to make calling without args faster 
    cert_path = "/Users/dwiggins/geni/collector-gpo-withnpkey.pem"
    validictory_path = "/Users/dwiggins/geni/ops-monitoring/extern/validictory"

    if len(sys.argv) != 2:
        usage()

    url = sys.argv[1]
    
    json_dict = make_request_print_response(url, cert_path)


    # custom prints of parts of the dictionary
    if json_dict:

        # get json-schema from $schema
        schema = response_validator.parse_schema(json_dict["$schema"])
        valid = response_validator.validate(json_dict, schema, validictory_path)
        print "Response from", url, "is",
        if valid:
            print "valid"
        else:
            print "NOT valid"

        '''
        # Uncomment to checks part of response dictionary
        part_of_dict = "resources"
        # avoids error if not in dict
        if part_of_dict in json_dict:
            print " ----- "
            pprint(json_dict[part_of_dict])
        '''

if __name__ == "__main__":
    main(sys.argv[1:])

