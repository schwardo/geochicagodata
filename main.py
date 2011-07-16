try:
  import simplejson as json
except ImportError:
  import json

import sys
import urllib2

from google.appengine.ext import webapp
from google.appengine.ext import db
from google.appengine.ext.webapp.util import run_wsgi_app


class View(db.Model):
    id = db.StringProperty()
    name = db.StringProperty()
    column_id = db.StringProperty()

class QueryPage(webapp.RequestHandler):
    def get(self):
        lat = float(self.request.get('lat'))
        lng = float(self.request.get('lng'))
        range = long(self.request.get('range'))
        self.response.headers['Content-Type'] = 'text/plain'
        for view in View.all():
            view_id = view.id
            column_id = long(view.column_id)
            data = json.dumps(
                {
                    "originalViewId": view_id,
                    "name": "BillsMom",
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
            request = urllib2.Request(url, data, headers={'Content-type:' : 'application/json'})
            results = json.loads(urllib2.urlopen(request).read())
            # TODO: Obviously we need much better formatting here.
            if results['data']:
              self.response.out.write("*** %s *****\n" % view.name)
              for d in results['data']:
                self.response.out.write(' '.join(str(x).encode('utf-8') for x in d))
                self.response.out.write('\n')
        

class GeneratePage(webapp.RequestHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'text/plain'
        for page in xrange(1, 12):
            f = urllib2.urlopen('http://data.cityofchicago.org/api/views?page=%d&limit=50' % page).read()
            results = json.loads(f)
            for r in results:
                id = r['id']

                f = urllib2.urlopen('http://data.cityofchicago.org/api/views/%s/columns.json' % id).read()
                for c in json.loads(f):
                    if c['dataTypeName'] == 'location':
                        self.response.out.write(
                            "%s (%s), col name = %s\n" % (r['name'], id, c['name']))
                        v = View(id = id,
                                 name = r['name'],
                                 column_id = str(c['id']))
                        v.put()


application = webapp.WSGIApplication(
                                     [('/query', QueryPage),
                                      ('/generate', GeneratePage),
                                      ],
                                     debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()
