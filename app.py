from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import json

with open('settings/config.json', 'r') as f:
    config = json.load(f)

app = Flask(__name__)
app.config['SECRET_KEY'] = config['SECRET_KEY']
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///clash_db.db'
# app.config['SQLALCHEMY_DATABASE_URI'] = environ.get(
#    'DATABASE_URL').replace("://", "ql://", 1) or 'sqlite:///clash_DB.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login = LoginManager(app)
login.init_app(app)
login.login_view = 'login'

import routes

if __name__ == '__main__':
    app.run(debug=True)
