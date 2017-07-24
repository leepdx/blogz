from flask import Flask, request, redirect, render_template, session
from flask_sqlalchemy import SQLAlchemy
import jinja2
import os
import cgi

app = Flask(__name__)
app.config['DEBUG'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://blogz:blogz@localhost:8889/blogz'
app.config['SQLALCHEMY_ECHO'] = True
db = SQLAlchemy(app)
app.secret_key = 'dfOpEBDP2EkiwtNF1J'

template_dir = os.path.join(os.path.dirname(__file__), 'templates')

jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir), autoescape=True)

#create Blog DB table & references
class Blog(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120))
    body = db.Column(db.Text())
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __init__(self, title, body, owner):
        self.title = title
        self.body = body
        self.owner = owner

#create User DB table & references
class User(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120), unique=True)
    password = db.Column(db.String(120))
    blogs = db.relationship('Blog', backref='owner')

    def __init__(self, username, password):
        self.username = username
        self.password = password


#Force redirects to login.html if user is not logged in and is not going to a allowed route
#This should only be newpost.html
@app.before_request
def require_login():
    allowed_routes = ['login', 'signup', 'blog', 'index']
    if request.endpoint not in allowed_routes and 'username' not in session:
        return redirect('/login')

@app.route('/login', methods=['POST', 'GET'])
def login():
        #If user clicks submit then...
        if request.method == 'POST':
            #grab username from form
            username = request.form['username']

            #grab password from form
            password = request.form['password']

            #Querey user DB for user
            user = User.query.filter_by(username=username).first()

            usererror = ''
            passworderror = ''
            invaliderror = ''

            #validate username
            if username == '':
                usererror = "That's not a valid username"

            #validate password
            if password == '':
                passworderror = "That's not a valid password"

            #If no empty values in username or password field then verify that username and password match from DB query
            if not usererror and not passworderror:
                if user and user.password == password:
                    session['username'] = username
                    return redirect('/newpost')
            #If any errors or invalid username combo, render template with error messages
            else:
                invaliderror = "Not a valid combo"
                template = jinja_env.get_template('login.html')
                return template.render(passworderror=passworderror,usererror=usererror,invaliderror=invaliderror)

        return render_template('login.html')

@app.route('/signup', methods=['POST', 'GET'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        verify = request.form['verify']
        usererror = ''
        passworderror = ''
        verifyerror = ''

        #validate username
        if username == '':
            usererror = "That's not a valid username"

        #validate password
        if password == '':
            passworderror = "That's not a valid password"
        elif len(password) < 3:
            passworderror = "That's not a valid password"
        elif len(password) > 20:
            passworderror = "That's not a valid password"
        elif " " in password:
            passworderror = "That's not a valid password"

        #validate verification password
        if password == '':
            verifyerror = "Passwords don't match"
        elif password != verify:
            verifyerror = "Passwords don't match"

        #If no errors in username, password or verify fields then query Users DB for existing user
        if not usererror and not passworderror and not verifyerror:
            existing_user = User.query.filter_by(username=username).first()
            #if not existing users create user
            if not existing_user:
                new_user = User(username, password)
                db.session.add(new_user)
                db.session.commit()
                session['username'] = username
                return redirect('/newpost')
            #if duplicate use then render template with error
            else:
                duplicateerror = "User already exists"
                template = jinja_env.get_template('signup.html')
                return template.render(duplicateerror=duplicateerror)
        #if errors render template with errors
        else:
            template = jinja_env.get_template('signup.html')
            return template.render(username=username,usererror=usererror,
                passworderror=passworderror,
                verifyerror=verifyerror)

    return render_template('signup.html')

@app.route('/logout')
def logout():
    del session['username']
    return redirect('/blog')

@app.route('/blog', methods=['POST', 'GET'])
def blog():

    #Grab blogid or userid from url
    blogid = request.args.get('id')
    userid = request.args.get('user')

    #if user clicks on blog id then render specific blog post
    if blogid:
        posts = Blog.query.filter_by(id=blogid).all()
        template = jinja_env.get_template('blog.html')
        return template.render(posts=posts,title="Blogs")

    #if user clicks on username then render posts by user
    if userid:
        posts = Blog.query.filter_by(owner_id=userid)
        template = jinja_env.get_template('blog.html')
        return template.render(title="Posts", posts=posts)

    #if user is just on the blog.html page without clicking on a specific post or user then render all posts
    else:
        posts = Blog.query.all()
        template = jinja_env.get_template('blog.html')
        return template.render(posts=posts,title="Posts")

@app.route('/', methods=['POST', 'GET'])
def index():
    #query Users DB for all users and render them in index.html template
    users = User.query.all()
    template = jinja_env.get_template('index.html')
    return template.render(users=users)
    return render_template('index.html')

@app.route('/newpost', methods=['POST', 'GET'])
def newpost():
    titleerror = ''
    bodyerror = ''
    title = ''
    body = ''

    #Query Users DB for current user based off of session
    owner = User.query.filter_by(username=session['username']).first()


    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']

    if request.method == 'POST' and title == '':
        titleerror = "Please fill in the title"

    if request.method == 'POST' and body == '':
        bodyerror = "Please fill in the body"

    if not titleerror and not bodyerror and request.method =='POST':
        new_blog = Blog(title, body, owner)
        db.session.add(new_blog)
        db.session.commit()
        return redirect("/blog?id=" + str(new_blog.id))

    else:
        template = jinja_env.get_template('newpost.html')
        return template.render(title=title,body=body,titleerror=titleerror,bodyerror=bodyerror,owner=owner)

if __name__ == '__main__':
    app.run()
