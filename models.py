from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from app import db, login
from flask_login import LoginManager, UserMixin, login_required


# klasa z kontem użytkownika
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), unique=True, index=True)
    password_hash = db.Column(db.String(128))
    profiles = db.relationship('Profile', backref='User', lazy='dynamic',
                               cascade="all, delete, delete-orphan")  # powiązanie z kontem uzytkownika
    reports = db.relationship('ReportPlayer', backref='Report', lazy='dynamic',
                              cascade="all, delete, delete-orphan")
    invitation_out = db.relationship('ClashInvitation', backref='teamleader', lazy='dynamic',
                                     cascade="all, delete, delete-orphan")
    request_in = db.relationship('ClashRequest', backref='team_creator', lazy='dynamic',
                                 cascade="all, delete, delete-orphan")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return '<User {}>'.format(self.username)


# klasa z profilem, przypisywanym do konta użytkownika, w relacji jeden do wielu (1 uzytkownik wiele profili)
class Profile(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nickname = db.Column(db.String(64), index=True, unique=True)
    server = db.Column(db.String(10), index=True)
    division = db.Column(db.String(20), index=True)
    best_position = db.Column(db.String(20), index=True)
    alternative_position = db.Column(db.String(20), index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    clash_team = db.relationship('ClashTeam', backref='host', lazy='dynamic')
    invitation_in = db.relationship('ClashInvitation', backref='invitedguest', lazy='dynamic',
                                    cascade="all, delete, delete-orphan")
    request_out = db.relationship('ClashRequest', backref='candidate', lazy='dynamic',
                                  cascade="all, delete, delete-orphan")
    reported = db.relationship('ReportPlayer', backref='Reported', lazy='dynamic',
                               cascade="all, delete, delete-orphan")


# Klasa przedstawiająca tworzenie dużyny Clash
class ClashTeam(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    clash_date = db.Column(db.DateTime, nullable=False, default=None)
    division = db.Column(db.String(64), index=True, default=None)
    toplane = db.Column(db.String(64), index=True, default=None)
    jungle = db.Column(db.String(64), index=True, default=None)
    midlane = db.Column(db.String(64), index=True, default=None)
    bottom = db.Column(db.String(64), index=True, default=None)
    support = db.Column(db.String(64), index=True, default=None)
    host_id = db.Column(db.Integer, db.ForeignKey('profile.id'))
    invitation = db.relationship('ClashInvitation', backref='futureteam', lazy='dynamic',
                                 cascade="all, delete, delete-orphan")
    request = db.relationship('ClashRequest', backref='desired_team', lazy='dynamic',
                              cascade="all, delete, delete-orphan")

    def formatted_clash_date(self):
        return self.clash_date.strftime('%Y-%m-%dT%H:%M')

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

    def add_bottom(self, bottom_name):
        if self.bottom is None:
            self.bottom = bottom_name
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


# Klasa zaproszeń
class ClashInvitation(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    role = db.Column(db.String(20), index=True)
    futureteam_id = db.Column(
        db.Integer, db.ForeignKey('clash_team.id'), nullable=False)
    lider_id = db.Column(
        db.Integer, db.ForeignKey('user.id'), nullable=False)
    guestprofile_id = db.Column(
        db.Integer, db.ForeignKey('profile.id'), nullable=False)

# Klasa prósb


class ClashRequest(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    role = db.Column(db.String(20), index=True)
    desired_team_id = db.Column(
        db.Integer, db.ForeignKey('clash_team.id'), nullable=False)
    team_host = db.Column(
        db.Integer, db.ForeignKey('user.id'), nullable=False)
    candidate_id = db.Column(
        db.Integer, db.ForeignKey('profile.id'), nullable=False)


@login.user_loader
def load_user(id):
    return User.query.get(int(id))