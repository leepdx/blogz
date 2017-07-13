from flask import Flask, request, redirect, render_template
from flask_sqlalchemy import SQLAlchemy
import jinja2
import os
import cgi

app = Flask(__name__)
app.config['DEBUG'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://build-a-blog:blog@localhost:8889/build-a-blog'
app.config['SQLALCHEMY_ECHO'] = True

db = SQLAlchemy(app)

template_dir = os.path.join(os.path.dirname(__file__), 'templates')

jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir), autoescape=True)


class Blog(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120))
    body = db.Column(db.Text())

    def __init__(self, title, body):
        self.title = title
        self.body = body


@app.route('/blog', methods=['GET'])
def index():
    blogid = request.args.get('id')
    if blogid:
        blogs = Blog.query.filter_by(id=blogid).all()
        template = jinja_env.get_template('blog.html')
        return template.render(blogs=blogs)

    else:
        posts = Blog.query.all()
        template = jinja_env.get_template('blog.html')
        return template.render(posts=posts)




@app.route('/newpost', methods=['POST', 'GET'])
def newpost():
    titleerror = ''
    bodyerror = ''
    title = ''
    body = ''

    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']
    if request.method == 'POST' and title == '':
        titleerror = "Please fill in the title"
    if request.method == 'POST' and body == '':
        bodyerror = "Please fill in the body"
    if not titleerror and not bodyerror and request.method =='POST':
        new_blog = Blog(title, body)
        db.session.add(new_blog)
        db.session.commit()
        return redirect("/blog?id=" + str(new_blog.id))
        #posts = Blog.query.all()
        #return render_template('blog.html',title="Build a Blog",posts=posts)

    else:
        template = jinja_env.get_template('newpost.html')
        return template.render(title=title,body=body,titleerror=titleerror,bodyerror=bodyerror)

if __name__ == '__main__':
    app.run()
