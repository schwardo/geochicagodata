from google.appengine.ext import db

class View(db.Model):
    id = db.StringProperty()
    name = db.StringProperty()
    column_id = db.StringProperty()
