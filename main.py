import os
import pprint
import cgi
import urllib

import jinja2
import webapp2
from google.appengine.ext import ndb
from google.appengine.api import users

# Chart.io
import datetime
import time
import jwt

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True,
    trim_blocks=True)

class Info(ndb.Model):
    secret = ndb.StringProperty(default='')

class Dashboard(webapp2.RequestHandler):
    def get(self, id):

        # This grabs the Chart ID from URL
        try:
            dashboardID = id.split("/")[0]

        except:
            dashboardID = id

        # This grabs the iFrame height from URL
        try:
            height = str(id.split("/")[1]) + "px"
            if height == "px":
                height = "100%"
        except:
            height = "100%"

        # This grabs the iFrame width from URL
        try:
            width = str(id.split("/")[2]) + "px"
            if width == "px":
                width = "100%"
        except:
            width = "100%"

        # Here is the important info for the Chart.io payload
        ORGANIZATION_SECRET = Info.query().fetch()[0].secret
        BASE_URL = 'https://embed.chartio.com/d/'
        BASE_URL = BASE_URL + str(dashboardID)
        payload = {
            'dashboard': int(dashboardID),
            'organization': 14483,
            'env': {"MYVAR": 42}
        }
        token = jwt.generate_jwt(payload, ORGANIZATION_SECRET, 'HS256',
                                 datetime.timedelta(days=1))
        iFrameURL = '<iframe id="dashboard" src="%s/%s"></iframe>' % (BASE_URL, token)

        # This handles user authentication by checking for @optimizely.com
        user = users.get_current_user()
        if user:
            url = users.create_login_url(self.request.uri)
            email = user.nickname()

        else:
            url = users.create_login_url(self.request.uri)
            email = "none"

        template_values = {
            'iFrameURL': iFrameURL,
            'dashboardID': dashboardID,
            'url': url,
            'email' : email,
            'height' : height,
            'width' : width,
        }

        # This will handle the redirect to the login if a user isn't logged in with an @optimizely.com email
        try:
           user.nickname().index('@optimizely.com')
        except:
            template = JINJA_ENVIRONMENT.get_template('login.html')
            self.response.write(template.render(template_values))
        else:
            template = JINJA_ENVIRONMENT.get_template('dashboard.html')
            self.response.write(template.render(template_values))

class NotFound(webapp2.RequestHandler):
    def get(self, id):
        page = id;
        self.response.out.write('<html><head><title>404 Not Found</title></head><body><h1>404 Not Found</h1><p>Sorry, "%s" is not a real directory.</p></body></html>' % page)

application = webapp2.WSGIApplication([
    ('/dashboard/(.*)', Dashboard, id),
    ('/(.*)', NotFound, id),
], debug=True)