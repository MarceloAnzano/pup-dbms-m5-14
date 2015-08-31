import cgi
from google.appengine.ext import ndb
from google.appengine.api import users
import os
import webapp2
import jinja2
import json
import logging
import time

jinja_env = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)


class ThesisDB(ndb.Model):
    year = ndb.IntegerProperty(required=True)
    title = ndb.StringProperty(required=True)
    abstract = ndb.TextProperty(required=True)
    adviser = ndb.StringProperty(required=True)
    section = ndb.IntegerProperty(required=True)
    datecreated = ndb.DateTimeProperty(auto_now_add=True)
    created_by = ndb.TextProperty(required=True)

class UserDB(ndb.Model):
    email = ndb.StringProperty(indexed = True)
    firstname = ndb.StringProperty()
    lastname = ndb.StringProperty()
    phoneNum = ndb.StringProperty()
    created_date = ndb.DateTimeProperty(auto_now_add=True)
    user_id = ndb.StringProperty(required=True)

class LoginPage(webapp2.RequestHandler):
    def get(self):
        login_url = users.create_login_url(self.request.uri)
        template = jinja_env.get_template('login.html');
        content = {
            'register': '/register',
            'login': login_url,
        }
        self.response.write(template.render(content))
        user = users.get_current_user()
        if user is not None:
            self.redirect("/")

class Register(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()
        if user is not None:
            logout_url = users.create_logout_url(self.request.uri)
            query = UserDB.query(UserDB.user_id == user.user_id())
            entity = query.get()
            if entity is not None:
                message = """\
                <p>User already registered</p>
                <p>You will be automatically redirected</p>
                """
                redirect = '<meta http-equiv="refresh" content="4;url=/">'
            else:
                message = """\
                <form method="post">
                    <input type="text" id="fame" name="fname" value="First Name" />
                    <input type="text" id="lame" name="lname" value="Last Name" />
                    <input type="text" id="num" name="num" value="Phone Number" />
                    <input type="submit" value="submit">
                </form>
                """
                redirect = ""
            template = jinja_env.get_template('register.html')
            content = {
                'user' : user.nickname(),
                'logout_url': logout_url,
                'message': message,
                'redirect' : redirect,
            }
            self.response.write(template.render(content))
        else:
            login_url = users.create_login_url(self.request.uri)
            self.redirect(login_url)

    def post(self):
        user = users.get_current_user()
        userCreate = UserDB(
            email = user.nickname(),
            firstname = cgi.escape(self.request.get('fname')),
            lastname = cgi.escape(self.request.get('lname')),
            phoneNum = cgi.escape(self.request.get('num')),
            user_id = user.user_id(),
            )
        userCreate.put()
        self.redirect("/")


class ColorTest(webapp2.RequestHandler):
    def get(self):
        template = jinja_env.get_template('colorTest.html')
        self.response.write(template.render())

class MainPage(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()
        if user is not None:
            logout_url = users.create_logout_url(self.request.uri)
            query = UserDB.query(UserDB.user_id == user.user_id())
            entity = query.get()
            if entity is not None:
                template = jinja_env.get_template('index.html')
                content = {
                    'user' : user.nickname(),
                    'logout_url': logout_url,
                }
                self.response.write(template.render(content))
            else:
                self.redirect("/register")
        else:
            self.redirect("/login")
    
    def post(self):
        user = users.get_current_user()
        thesis = ThesisDB(
            year=int(self.request.get('year')),
            title=cgi.escape(self.request.get('title')),
            abstract=cgi.escape(self.request.get('abstract')),
            adviser=cgi.escape(self.request.get('adviser')),
            section=int(self.request.get('section')),
            created_by = user.user_id(),
            )
        thesis.put()
        self.redirect('/api/student')

class APIThesis(webapp2.RequestHandler):
    def get(self):
        thesis = ThesisDB.query().order(-ThesisDB.datecreated).fetch()
        thesis_list = []
        
        for paper in thesis:
            query = UserDB.query(UserDB.user_id == paper.created_by)
            entity = query.get()
            fullname = entity.firstname + " " + entity.lastname
            thesis_list.append({
                'id': paper.key.urlsafe(),
                'year': paper.year,
                'title': paper.title,
                'abstract': paper.abstract,
                'adviser' : paper.adviser,
                'section' : paper.section,
                'created_by' : fullname,
            })

        response = {
            'result': 'OK',
            'data': thesis_list
        }

        self.response.headers['Content-Type'] = 'application/json'
        self.response.out.write(json.dumps(response))

    def post(self):
        user = users.get_current_user()
        thesis = ThesisDB(
            year=int(self.request.get('year')),
            title=cgi.escape(self.request.get('title')),
            abstract=cgi.escape(self.request.get('abstract')),
            adviser=cgi.escape(self.request.get('adviser')),
            section=int(self.request.get('section')),
            created_by = user.user_id(),
            )
        thesis.put()

        self.response.headers['Content-Type'] = 'application/json'
        query = UserDB.query(UserDB.user_id == user.user_id())
        entity = query.get()
        fullname = entity.firstname + " " + entity.lastname
        response = {
            'result': 'OK',
            'data': {
                'id': thesis.key.urlsafe(),
                'year': thesis.year,
                'title': thesis.title,
                'abstract': thesis.abstract,
                'adviser' : thesis.adviser,
                'section' : thesis.section,
                'created_by' : fullname,
            }
        }
        self.response.out.write(json.dumps(response))


app = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/login',LoginPage),
    ('/api/thesis', APIThesis),
    ('/register', Register),
], debug=True)