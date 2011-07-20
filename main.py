try:
  import simplejson as json
except ImportError:
  import json

import urllib2
import sys

from google.appengine.ext import webapp
from google.appengine.api import urlfetch
from google.appengine.ext.webapp.util import run_wsgi_app

import metadata
import models


# Approximate Chicago area boundary.
BOUNDS = '41.496235,-87.978516|42.106374,-87.138062'

class QueryPage(webapp.RequestHandler):
    def get(self):
        address = self.request.get('address')
        if address:
          # Note that in its current form, this application violates
          # the Google Maps Geocoder ToS.  You must display the
          # results on a map.  We plan to do this in the future but
          # are not yet.
          r = urlfetch.fetch('http://maps.googleapis.com/maps/api/geocode/json?address=%s&sensor=false&bounds=%s' % (
              urllib2.quote(address), BOUNDS))
          if r.status_code == 200:
            j = json.loads(r.content)
            if j['status'] == "OK":
              lat = j['results'][0]['geometry']['location']['lat']
              lng = j['results'][0]['geometry']['location']['lng']
            else:
              self.response.out.write('Could not find address %s: %s' % (
                  address, j['status']))
              return
        else:
          lat = float(self.request.get('lat'))
          lng = float(self.request.get('lng'))
        range = long(self.request.get('range'))  # Meters
        self.response.headers['Content-Type'] = 'text/plain'
        rpcs = []
        for view in models.View.all():
            view_id = view.id
            column_id = long(view.column_id)
            data = json.dumps(
                {
                    "originalViewId": view_id,
                    "name": view.name,
                    "query": {
                        "filterCondition": {
                            "type": "operator",
                            "value": "AND",
                            "children": [
                                {
                                    "children": [
                                        {
                                            "type": "operator",
                                            "value": "within_circle",
                                            "metadata": {
                                                "freeform": True
                                                },
                                            "children": [
                                                {
                                                    "type": "column",
                                                    "columnId": column_id
                                                    },
                                                {
                                                    "type": "literal",
                                                    "value": lat
                                                    },
                                                {
                                                    "type": "literal",
                                                    "value": lng
                                                    },
                                                {
                                                    "type": "literal",
                                                    "value": range
                                                    }
                                                ]
                                            }
                                        ],
                                    "type": "operator",
                                    "value": "OR"
                                    }
                                ]
                            }
                        }
                    })
            url = "http://data.cityofchicago.org/api/views/INLINE/rows.json?method=index"
            rpc = urlfetch.create_rpc()
            urlfetch.make_fetch_call(rpc, url,
                                     headers={'Content-type:' : 'application/json'},
                                     method=urlfetch.POST,
                                     payload=data)
            rpcs.append(rpc)
        for rpc in rpcs:
            rpc.wait()
            result = rpc.get_result()
            if result.status_code == 200:
              response = json.loads(result.content)
              # TODO: Obviously we need much better formatting here.
              if response['data']:
                self.response.out.write("%s\n" % response['meta']['view']['name'])
                for d in response['data']:
                  for i in xrange(len(d)):
                    col = response['meta']['view']['columns'][i]
                    if col['dataTypeName'] == 'text':
                      col_name = col['name']
                      data = d[i]
                      self.response.out.write('  %s: %s\n' % (col_name, data))
                  self.response.out.write('\n')


application = webapp.WSGIApplication(
                                     [('/query', QueryPage),
                                      ],
                                     debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()
