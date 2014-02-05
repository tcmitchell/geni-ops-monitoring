# Invoke this as:
#   python validate_examples.py [/path/to/validictory]

# If you provide a path to validictory, it'll assume that it's not
# installed in your normal python path, and include the path you provide

import os
import subprocess
import sys
import traceback

if len(sys.argv) > 1:
  sys.path.append(sys.argv[1])

import json
import urllib2
import validictory

def validate_file(datafile):
  try:
    data = json.load(open(datafile))
    schema = json.load(urllib2.urlopen(data['$schema']))
    validictory.validate(data, schema)
    print "JSON file %s is valid" % datafile
    return True
  except Exception, e:
    print "Received exception %s while trying to validate: %s\n  %s" % (
      str(e), datafile, traceback.format_exc())
  return False

def find_json_files(dirname):
  p = subprocess.Popen(
    ["find", dirname, "-type", "f", "-name", "*.json"],
    stdout=subprocess.PIPE, stderr=subprocess.PIPE)
  [output, errout] = p.communicate()
  if p.returncode == 0:
    return output.split()
  else:
    print "find failed - couldn't look for JSON files"
    sys.exit(1)

for jsonfile in find_json_files('.'):
  validate_file(jsonfile)
