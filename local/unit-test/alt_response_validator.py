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

import json
import os
import sys
import urllib2
import types
from pprint import pprint as pprint

# schema key in which most expected element properties are stored
PROPERTIES_KEYNAME = 'properties'

# Schemas are likely to have these top-level keys, and we can ignore
# them in processing.  If schemas have any keys other than these,
# we want to know about it
VERIFY_KNOWN_TOP_LEVEL_KEYS = [
  '$schema',
  'extends',
  'additionalProperties',
  'links',
  'name',
  'type',
  'id',
  'description',
]

def parse_schema(schemaurl):
  schema = json.load(urllib2.urlopen(schemaurl))
  if 'extends' in schema and '$ref' in schema['extends']:
    parent_schema = parse_schema(schema['extends']['$ref'])
    for key in sorted(parent_schema.keys()):
      if key in schema:
        if key == PROPERTIES_KEYNAME:
          for subkey in sorted(parent_schema[key].keys()):
            if not subkey in schema[key]:
              schema[key][subkey] = parent_schema[key][subkey]
      else:
        schema[key] = parent_schema[key]
  return schema

def parse_test_data(filename):
  testdata = json.load(open(filename))
  cases = []
  for case in testdata['cases']:
    cases.append([case[0], testdata['base_url'] + case[1]])
  return cases

class UrlChecker:
  def __init__(self, expected_type, url):
    self.expected_type = expected_type
    self.url = url
    self.errors = []
    self.hrefs_found = []
    try:
      self.resp = json.load(urllib2.urlopen(self.url))
      self.validate_response()
    except urllib2.HTTPError, e:
      self.errors.append("Received HTTP error while loading URL: %s" % str(e))
    except ValueError, e:
      self.errors.append("Received ValueError while loading URL: %s" % str(e))

  def validate_response(self):
    if '$schema' in self.resp:
      schema_lastpart = self.resp['$schema'].split('/')[-1].split('#')[0]
      if self.expected_type and not schema_lastpart == self.expected_type:
        self.errors.append(
          'Expected schema of type %s, but got %s (inferred type %s)' % (
            self.expected_type, self.resp['$schema'], schema_lastpart))
      self.schema = parse_schema(self.resp['$schema'])
      self.validate_response_against_schema()

      # required, but the schema verify will complain if it's not present
      if 'selfRef' in self.resp:
        if not self.resp['selfRef'] == self.url:
          self.errors.append(
            'URL queried was %s, but response reported selfRef of %s' % (
              self.url, self.resp['selfRef']))
    else:
      self.errors.append('"$schema" parameter missing from response')

  def validate_response_against_schema(self):
    for key in self.schema:
      if key in VERIFY_KNOWN_TOP_LEVEL_KEYS: continue
      if key == PROPERTIES_KEYNAME:
        self.schemaprops = self.schema[key]
        self.validate_response_properties()
        continue
      self.errors.append("Unknown schema top-level key %s: %s" % (key, self.schema[key]))

  def validate_response_properties(self):
    for prop in self.schemaprops.keys():
      if prop in self.resp:
        if 'type' in self.schemaprops[prop]:
          self.validate_prop_as_type(
	    self.resp[prop],
            prop,
            self.schemaprops[prop],
	    self.schemaprops[prop]['type'],
          )
        else:
          self.errors.append("Schema property %s has no type" % prop)
      else:
        proprequired = True
        if 'required' in self.schemaprops[prop]:
          proprequired = self.schemaprops[prop]['required']
        if proprequired:
          self.errors.append("Required property %s is missing from response" % prop)

  def validate_prop_as_type(self, propresp, prop, propattrs, proptype):
    if type(proptype) == types.ListType:
      self.validate_prop_as_type_dict(propresp, prop, propattrs, proptype)
    elif proptype == 'object' and 'properties' in propattrs:
      self.validate_prop_as_type_object(propresp, prop, propattrs, proptype)
    elif proptype == 'string':
      self.validate_prop_type_in_list(
        propresp, prop, 'string', [types.StringType, types.UnicodeType])
    elif proptype == 'integer':
      self.validate_prop_type_in_list(
        propresp, prop, 'integer', [types.IntType, ])
    elif proptype == 'array':
      self.validate_prop_as_type_array(propresp, prop, propattrs)
    elif proptype.startswith('http://'):
      self.validate_prop_as_url(propresp, prop, proptype)
    else:
      self.errors.append(
        "Don't know how to validate prop type %s for property %s" % (
        proptype, prop))

  def validate_prop_as_url(self, propresp, prop, proptype):
    preerrcount = len(self.errors)
    self.validate_prop_type_in_list(
      propresp, prop, 'string', [types.StringType, types.UnicodeType])
    posterrcount = len(self.errors)
    if preerrcount == posterrcount:
      if not propresp.startswith('http'):
        self.errors.append(
          "Property %s should have URL type (schema %s) but instead has value %s" % (
            prop, proptype, propresp))

  def validate_prop_type_in_list(self, propresp, prop, typename, typelist):
    if not type(propresp) in typelist:
      self.errors.append("Response %s for property %s is of type %s not %s" % (
        propresp, prop, type(propresp), typename))

  def validate_prop_as_type_array(self, propresp, prop, propattrs):
    self.validate_prop_type_in_list(propresp, prop, 'array',
      [types.ListType, ])
    schemavalid = True
    if 'items' in propattrs:
      if not 'type' in propattrs['items']:
        self.errors.append(
          "Schema for property %s does not specify type for each array item" % prop)
        schemavalid = False
    else:
      self.errors.append(
        "Schema for property %s does not describe array items" % prop)
      schemavalid = False
    if schemavalid:
      for propentry in propresp:
        self.validate_prop_as_type(
          propentry,
          '%s [list item]' % (prop),
          propattrs['items'],
          propattrs['items']['type']
        )

  def validate_prop_as_type_object(self, propresp, prop, propattrs, proptype):
    subprops = propattrs['properties']
    for subprop in sorted(subprops.keys()):
      subproptype = subprops[subprop]['type']
      if subprop in propresp:
        self.validate_prop_as_type(
          propresp[subprop],
          "%s [subobject %s]" % (prop, subprop),
          subprops[subprop],
          subproptype
        )
      else:
        self.errors.append(
          "Property %s (%s) is missing required object subproperty %s" % \
            (prop, propresp, subprop))

  def validate_prop_as_type_dict(self, propresp, prop, propattrs, proptype):
    if type(proptype[0]) != types.DictType:
      self.errors.append(
        "Schema for property %s has an array type which does not contain a dictionary" \
        % (prop))
    # FIXME: if the type is an array of dicts with length > 1, then
    # those dicts are alternative options for what the item may
    # contain.  Since, in practice, the alternatives are all schemas
    # for the href to match, and this script doesn't investigate
    # sub-URL schema matching yet, we don't worry about this yet.
    for subprop in sorted(proptype[0].keys()):
      subproptype = proptype[0][subprop]
      if subprop == '$ref':
        expprop = 'href'
        if expprop in propresp:
          self.hrefs_found.append(propresp[expprop])
      else:
        expprop = subprop
      if expprop in propresp:
        self.validate_prop_as_type(
          propresp[expprop],
          "%s [subprop %s]" % (prop, expprop),
          propattrs,
          subproptype
        )
      else:
        self.errors.append(
          "Property %s (%s) is missing required subproperty %s" % \
          (prop, propresp, subprop))

def test_found_hrefs(hrefs_found, hrefs_checked):
  print ""
  hrefs_to_check = []
  for href in sorted(hrefs_found.keys()):
    if not href in hrefs_checked:
      hrefs_to_check.append(href)
  if len(hrefs_to_check) == 0:
    print "All found URLs have now been checked"
    return False
  for href in hrefs_to_check:
    print "testing discovered URL %s (referenced by: %s):" % (href, ", ".join(hrefs_found[href])),
    check = UrlChecker(None, href)
    if len(check.errors) > 0:
      print ""
      for error in check.errors:
        print "  ERROR: " + error
    else:
      print "OK"
    hrefs_checked.append(href)
    for newhref in check.hrefs_found:
      hrefs_found.setdefault(newhref, [])
      hrefs_found[newhref].append(check.url)
  return True

def test_all_cases(cases):
  hrefs_found = {}
  hrefs_checked = []
  for case in cases:
    print "testing URL %s (type %s):" % (case[1], case[0]),
    check = UrlChecker(case[0], case[1])
    if len(check.errors) > 0:
      print ""
      for error in check.errors:
        print "  ERROR: " + error
    else:
      print "OK"
    hrefs_checked.append(case[1])
    for newhref in check.hrefs_found:
      hrefs_found.setdefault(newhref, [])
      hrefs_found[newhref].append(check.url)
  while test_found_hrefs(hrefs_found, hrefs_checked):
    continue

testcases = parse_test_data(sys.argv[1])
test_all_cases(testcases)

