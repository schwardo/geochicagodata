try:
  import simplejson as json
except ImportError:
  import json

import sys

from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app

import metadata
import models


class BuildMetadataPage(webapp.RequestHandler):
  def get(self):
    metadata.update()
    self.response.headers['Content-Type'] = 'text/plain'
    self.response.out.write('Metadata will now be updated in the background.')


application = webapp.WSGIApplication(
                                     [('/admin/build-metadata', BuildMetadataPage),
                                      ],
                                     debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()
