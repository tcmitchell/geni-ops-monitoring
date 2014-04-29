import sys
import traceback
import os
import OpenSSL

try:
  sys.path.insert(0, '/usr/local/ops-monitoring/local')
  from web_server import LocalDatastoreServer
  server = LocalDatastoreServer('/usr/local/ops-monitoring')
  _application = server.app
except Exception, e:
  sys.stderr.write("WSGI threw an exception: %s: %s\n" % (
    str(e), str(traceback.format_exc())))

def authorized_certificate(cert_string):
    # parse the certificate data
    cert = OpenSSL.crypto.load_certificate(OpenSSL.crypto.FILETYPE_PEM,
    	                                   cert_string)

    # assume no subject alternative name
    alt_name = None

    # loop over extensions, checking each to see if it is the subject
    # alternative name
    for x in range(cert.get_extension_count()):
	ext = cert.get_extension(x)
	short_name = ext.get_short_name()
	if short_name == 'subjectAltName':
	    alt_name = ext
	    break

    # If no subject alternative name...
    if not alt_name:
        print "No subject alternative name found in cert"
	return False

    # convert subject alt name value to string, split on comma,
    # and strip whitespace before & after
    names = [s.strip() for s in str(alt_name).split(',')]

    # find the URN by matching the prefix
    for name in names:
        if name.startswith('URI:urn:publicid:IDN'):
            # XXX check whitelist here
	    if 'tool+collector-' in name:
                return True
            else:
                print "%s not authorized" % name
                return False

    print "No publicid found in certificate"
    return False

def application(environ, start_response):
    if authorized_certificate(environ['SSL_CLIENT_CERT']):
        return _application(environ, start_response)
    else:
        start_response('403 Forbidden', [('Content-Type', 'text/plain')])
        return ["Client certificate not authorized\n"]
