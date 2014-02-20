import sys
import traceback

try:
  sys.path.insert(0, '/usr/local/ops-monitoring/local')
  from web_server import LocalDatastoreServer
  server = LocalDatastoreServer('/usr/local/ops-monitoring')
  application = server.app
except Exception, e:
  sys.stderr.write("WSGI threw an exception: %s: %s\n" % (
    str(e), str(traceback.format_exc())))
