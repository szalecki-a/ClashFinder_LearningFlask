from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_required
from os import environ

app = Flask(__name__)
app.config['SECRET_KEY'] = 'loltotoksycznagra'
app.config['SQLALCHEMY_DATABASE_URI'] = environ.get('DATABASE_URL') or 'sqlite:///clash_DB.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login = LoginManager(app)
login.init_app(app)
login.login_view = 'login'


from routes import *

#if __name__ == '__main__':
#    app.run()