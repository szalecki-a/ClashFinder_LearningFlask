from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from app import db, login
from flask_login import LoginManager, UserMixin, login_required


# konto użytkownika
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), unique=True, index=True)
    password_hash = db.Column(db.String(128))
    profiles = db.relationship('Profile', backref='Player', lazy='dynamic',
                               cascade="all, delete, delete-orphan")  # powiązanie z kontem uzytkownika
    reports = db.relationship('ReportPlayer', backref='Report', lazy='dynamic',
                              cascade="all, delete, delete-orphan")  # powiązanie z kontem uzytkownika

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return '<User {}>'.format(self.username)

# profil uzytkownika


class Profile(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nickname = db.Column(db.String(64), index=True, unique=True)
    server = db.Column(db.String(10), index=True)
    division = db.Column(db.String(20), index=True)
    best_position = db.Column(db.String(20), index=True)
    alternative_position = db.Column(db.String(20), index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    clash_team = db.relationship('ClashTeam', backref='host', lazy='dynamic')
    reported = db.relationship('ReportPlayer', backref='Reported', lazy='dynamic',
                              cascade="all, delete, delete-orphan")  # powiązanie z reportowanym profilem

    # dodać metodę repr, która odeśle na serwer np nexusblitz..
    def __repr__(self):
        pass
        # return '<User {}>'.format(self.username)


# stworzyć klasy - tworzenie drużyn - na konkretną datę oraz godzinę, która umożliwia wysyłanie zgłoszeń do dołączenia lub zapraszanie
    # klasa stworzona, wysyłanie zaproszeń lub dołączanie za pomocą formularza
# czyli trzeba stworzyć formularze do tworzenia spotkań oraz do wystawiania "siebie" na rynku

# tworzenie drużyny
class ClashTeam(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    clash_date = db.Column(db.DateTime, nullable=False, default=None)
    division = db.Column(db.String(64), index=True, default=None)
    toplane = db.Column(db.String(64), index=True, default=None)
    jungle = db.Column(db.String(64), index=True, default=None)
    midlane = db.Column(db.String(64), index=True, default=None)
    adcarry = db.Column(db.String(64), index=True, default=None)
    support = db.Column(db.String(64), index=True, default=None)
    host_id = db.Column(db.Integer, db.ForeignKey('profile.id'))


    # def __init__(self, role, clash_date=None):
    #     self.clash_date = clash_date
    #     self.toplane = None if role != "toplane" else Profile.nickname
    #     self.jungle = None if role != "jungle" else Profile.nickname
    #     self.midlane = None if role != "midlane" else Profile.nickname
    #     self.adcarry = None if role != "adcarry" else Profile.nickname
    #     self.support = None if role != "support" else Profile.nickname
    #     if clash_date != None:
    #         if datetime.now() < self.clash_date:
    #             self.clash_date = clash_date
    #         else:
    #             raise Exception("Pick correct date")

    def add_top(self, top_name):
        if self.toplane is None:
            self.toplane = top_name
        else:
            raise Exception("The top position is already taken.")

    def add_jungle(self, jungle_name):
        if self.jungle is None:
            self.jungle = jungle_name
        else:
            raise Exception("The jungle position is already taken.")

    def add_midlane(self, mid_name):
        if self.midlane is None:
            self.midlane = mid_name
        else:
            raise Exception("The midlane position is already taken.")

    def add_adcarry(self, adcarry_name):
        if self.adcarry is None:
            self.adcarry = adcarry_name
        else:
            raise Exception("The bot position is already taken.")

    def add_support(self, support_name):
        if self.support is None:
            self.support = support_name
        else:
            raise Exception("The support position is already taken.")


# Klasa do zgłaszania użytkowników
class ReportPlayer(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(64), nullable=False)
    text = db.Column(db.String(256), nullable=False)
    reporter_id = db.Column(
        db.Integer, db.ForeignKey('user.id'), nullable=False)
    reported_id = db.Column(
        db.Integer, db.ForeignKey('profile.id'), nullable=False)


@login.user_loader
def load_user(id):
    return User.query.get(int(id))


'''
class Post():
    id = db.Column(db.Integer, primary_key=True)
    city = db.Column(db.String(140))
    country = db.Column(db.String(140))
    description = db.Column(db.String(140))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self):
        return '<Post {}>'.format(self.description)

    '''
