try:
  import simplejson as json
except ImportError:
  import json

import urllib2
import logging

from google.appengine.ext import deferred

import models

# Note that due to a limitation in the deferred library this code must
# exist in its own module and not in a handler script.


VIEW_LIMIT = 20


def update():
  deferred.defer(_query_views, 1)


def _query_views(page_num):
  logging.info("Fetching page %d" % page_num)
  f = urllib2.urlopen('http://data.cityofchicago.org/api/views?page=%d&limit=%d' % (page_num, VIEW_LIMIT)).read()
  results = json.loads(f)
  if len(results) == VIEW_LIMIT:
    deferred.defer(_query_views, page_num + 1)
  for view_json in results:
    deferred.defer(_add_view, view_json)


def _add_view(view_json):
  view_id = view_json['id']
  logging.info("Processing view %s" % view_id)
  f = urllib2.urlopen('http://data.cityofchicago.org/api/views/%s/columns.json' % view_id).read()
  for col_json in json.loads(f):
    if col_json['dataTypeName'] == 'location':
      view = models.View.get_by_key_name(view_id)
      if view is None:
        view = models.View(key_name = view_id)
      view.id = view_id
      view.name = view_json['name']
      view.column_id = str(col_json['id'])
      view.put()
