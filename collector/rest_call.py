#!/usr/bin/env python
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
This program exercises the monitoring REST/JSON API by making REST
call local datastores and validating the JSON reponses it receives
against the monitoring schema.  The URLs specifying the REST calls are
supplied on the command line.  A disk filename can be given instead of
a URL to verify test data.  See the commmand line options (invoke with
--help) for more information about the program's capabilities.

This requires sudo pip install requests --upgrade

and

git clone https://github.com/sunlightlabs/validictory.git
to ops-monitoring/extern/validictory

'''

import json
import sys
import requests
import getopt
import re
import os
from optparse import OptionParser

# XXX this program must be run with the current directory set to
# collector/ (the directory containing this file) OR with said
# directory added to the PYTHONPATH environment variable so that it
# can find the response_validatory module.
import response_validator


def visit_url(url, cert_path):
    """
    Make a monitoring REST call and collect the response.

    :param url: URL of the monitoring REST call for which to fetch the
      response.  If this doesn't start with http(s)://, interpret it as
      a filename.
    :param cert_path: path to tool certificate file for SSL access.
    :return: a dictionary containing the JSON response to url, or None if an
      error occurred.
    """
    json_dict = None

    if re.match("https?://", url):
        # interpret url as an actual URL
        resp = None
        try:
            resp = requests.get(url, verify=False, cert=cert_path)
        except Exception, e:
            print "No response from local datastore for URL %s\s%s" % (url,
                                                                       str(e))
        if resp:
            try:
                json_dict = json.loads(resp.content)
            except Exception, e:
                print "Could not load as URL %s, %s\n%s" % (url, resp.content,
                                                           str(e))
        else:
            print "resp object is None from", url
    else:
        # interpret url as a file on the local disk
        try:
            json_dict = json.load(open(url))
        except Exception, e:
            print "Could not load as file: %s\n%s" % (url, str(e))

    return json_dict


def find_embedded_urls(json_dict):
    """
    Examine a JSON response to find other URLs that could be visited.
    Fields named "href" or "selfRef" are assumed to be URLs.

    :param json_dict: dictionary containing a JSON response to examine.
    :return: a list, possibly empty, of embedded urls found.
    """
    embedded_urls = []

    if isinstance(json_dict, dict):
        for urlKey in ["href", "selfRef"]:
            if urlKey in json_dict:
                embedded_urls.append(json_dict[urlKey])

        for (key, dval) in json_dict.items():
            if isinstance(dval, dict):
                embedded_urls.extend(find_embedded_urls(dval))
            elif isinstance(dval, list):
                for lval in dval:
                    if isinstance(lval, dict):
                        embedded_urls.extend(find_embedded_urls(lval))
    return embedded_urls


def validate_response(json_dict, options):
    """
    Check a JSON response against its schema.

    :param json_dict: dictionary containing a JSON response to validate..
    :param options: command line options object
    :return: True if json_dict was valid, else False
    """
    if not json_dict:
        return False

    if not "$schema" in json_dict:
        print "No $schema specified in response"
        return False

    schema = response_validator.parse_schema(json_dict["$schema"],
                                             options.schema_path)
    if not schema:
        return False

    if options.print_schema:
        print "Schema used for validation:\n%s" % (json.dumps(schema, indent=4,
                                                              sort_keys=True))

    valid = response_validator.validate(json_dict, schema,
                                        options.validictory_path,
                                        options.schema_base)
    return valid


def choose_url_to_visit(unvisited_urls, num_visited_urls, interactive):
    """
    Decide which URL to visit next.

    :param unvisited_urls: candidate URLs that could be visited next.
    :param num_visited_urls: number of URLs already visited.
    :param interactive: boolean, are we in interactive mode?
    :return: URL (string) to visit next, or None 
    """
    if interactive:
        # If there is only one possible URL, and this is the first time
        # visiting anything, just go there without asking.
        if len(unvisited_urls) == 1 and num_visited_urls == 0:
            return unvisited_urls[0]
            
        print 79 * "=" # line of === for visual separation
        for idx in range(len(unvisited_urls)):
            print str(idx) + ": " + unvisited_urls[idx]
        user_input = raw_input("Which URL to go to? (enter number from above, or anything else to exit)\n")
        try:
            choice = int(user_input)
        except ValueError:
            # If non-numeric input was received, pretend we got an
            # invalid choice.
            choice = -1

        # If it's an invalid choice...
        if (choice < 0) or (choice >= len(unvisited_urls)):
            return None
        else:
            return unvisited_urls[choice]
    else:
        # non-interactive: always return the first URL in the list
        return unvisited_urls[0]


def main(argv): 

    # Set up command-line options

    parser = OptionParser(usage="usage: %prog [options] <list-of-datastore-urls>",
                          description="Make a monitoring REST call, and "
                          "validate and display the JSON response. "
                          "If any of the URLs in <list-of-datastore-urls> "
                          "does not start with \"http(s)://\", then it is "
                          "interpreted as a file containing a JSON response.")
    parser.add_option("-c", "--cert-path", dest="cert_path",
                      help="path to tool certificate file")
    parser.add_option("-v", "--validictory-path", dest="validictory_path",
                      help="path to validictory python module")
    parser.add_option("-s", "--schema-path", dest="schema_path",
                      help="path to directory of schema files to use for validation")
    parser.add_option("-b", "--schema-base", dest="schema_base",
                      help="expected $schema string in JSON responses")
    parser.add_option("-f", "--follow-urls", dest="follow_urls",
                      default=False, action="store_true",
                      help="follow URLs in JSON responses to find other "
                           "objects, i.e., crawl the datastore")
    parser.add_option("-i", "--interactive", dest="interactive",
                      default=False, action="store_true",
                      help="allow user to choose which URLs to follow "
                           "(implies -f)")
    parser.add_option("--skip-validation", dest="skip_validation",
                      default=False, action="store_true",
                      help="don't do JSON validation of responses")
    parser.add_option("--print-schema", dest="print_schema",
                      default=False, action="store_true",
                      help="print the schema used to validate each response")
    (options, url_args) = parser.parse_args()

    # Do some more checking on the options provided

    if options.cert_path and not os.path.isfile(options.cert_path):
        print "cert-path %s is not a file" % (options.cert_path)
        return 1

    if options.validictory_path and not os.path.isdir(options.validictory_path):
        print "validictory-path %s is not a directory" % (options.validictory_path)
        return 1

    if options.schema_path and not os.path.isdir(options.schema_path):
        print "schema-path %s is not a directory" % (options.schema_path)
        return 1

    # If in interactive mode, enable follow_urls so that the user has choices
    if options.interactive:
        options.follow_urls = True

    # Options look good.  Let's get to work.

    # URLs that haven't been fetched yet
    unvisited_urls = list(url_args) # make a copy of url_args

    # URLs for which we have attempted to fetch a response
    visited_urls = set() # empty set to begin

    # Number of URLs visited that returned valid JSON according to their schema
    num_valid_urls = 0

    # main loop

    while unvisited_urls:
        url = choose_url_to_visit(unvisited_urls, len(visited_urls),
                                  options.interactive)
        if not url: # chose to exit
            break

        json_dict = visit_url(url, options.cert_path)

        # now that we've visited it, move this url from unvisited to visited
        unvisited_urls.remove(url)
        visited_urls.add(url)

        # print the response

        print 79 * "-", \
            "\nVisiting %s returns:\n%s" % (url,
                                            json.dumps(json_dict, indent=4,
                                                       sort_keys=True))
        # maybe validate the response

        if not options.skip_validation:
            valid = validate_response(json_dict, options)
            print "Response from %s is" % (url),
            if valid:
                print "valid"
                num_valid_urls += 1
            else:
                print "NOT valid"

        # maybe "crawl"; harvest other URLs from the response

        if options.follow_urls:
            # Find the URLs embedded in this response.  Any that we have
            # not already visited go into unvisited_urls.
            embedded_urls = find_embedded_urls(json_dict)
            for embedded_url in embedded_urls:
                if not (embedded_url in visited_urls):
                    unvisited_urls.append(embedded_url)

    # print a summary of this run

    print "%d URLs visited" % (len(visited_urls)),
    if not options.skip_validation:
        print ", %d valid" % (num_valid_urls)


if __name__ == "__main__":
    main(sys.argv[1:])
