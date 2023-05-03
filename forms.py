from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField, SelectMultipleField, HiddenField, DateField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo, Optional
from models import Profile
from wtforms import DateTimeLocalField
from datetime import datetime, timedelta

servers = [('North America', 'NA'), ('West Europe', 'EUW'),
           ('North and Eeat Europe', 'EUNE')]
positions = [(None, ''), ('Toplane', 'Toplane'), ('Jungle', 'Jungle'),
             ('Midlane', 'Midlane'), ('Bottom', 'Bottom'), ('Support', 'Support')]
divisions = [(None, ''), ('Iron', 'Iron'), ('Bronze', 'Bronze'), ('Silver', 'Silver'), ('Gold', 'Gold'), ('Platinum', 'Platinum'),
             ('Diamond', 'Diamond'), ('Master', 'Master'), ('Grandmaster', 'Grandmaster'), ('Challenger', 'Challenger')]

ROLES_DICT = {
    'Toplane': 'toplane',
    'Jungle': 'jungle',
    'Midlane': 'midlane',
    'Bottom': 'bottom',
    'Support': 'support',
}


def get_server_short_name(server_name):
    for server in servers:
        if server[0] == server_name:
            return server[1]
    return None


def get_server_name_from_short(short_name):
    for server in servers:
        if server[1] == short_name:
            return server[0]
    return None


def validate_date(form, field):
    min_date = datetime.now()
    max_date = datetime.now() + timedelta(days=365)
    if field.data < min_date:
        raise ValidationError(
            'Date should be greater than or equal to current date')
    if field.data > max_date:
        raise ValidationError(
            'Date should be less than or equal to one year from now')

def optional_date(form, field):
    if field.data is None:
        pass

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField('Repeat Password', validators=[
                              DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me', default=False)
    submit = SubmitField('Sign In')


class DifferentRole(object):
    def __init__(self, fieldname):
        self.fieldname = fieldname

    def __call__(self, form, field):
        if field.data == form[self.fieldname].data:
            message = 'Secondary position must be different from main position'
            raise ValidationError(message)


class ProfileForm(FlaskForm):
    nickname = StringField('Nickname', validators=[DataRequired()])
    server = SelectField('Server', choices=servers,
                         validators=[DataRequired()])
    division = SelectField('Division', choices=divisions,
                           validators=[DataRequired()])
    pref_role = SelectField(
        'Prefer Role', choices=positions, validators=[DataRequired()])
    alternative_role = SelectField('Alternative Role', choices=positions, validators=[
                                   DataRequired(), DifferentRole('pref_role')])
    submit = SubmitField('Add Profile')


class EditProfileForm(FlaskForm):
    nickname = StringField('Nickname', validators=[DataRequired()])
    server = SelectField('Server', choices=servers,
                         validators=[DataRequired()])
    division = SelectField('Division', choices=divisions,
                           validators=[DataRequired()])
    pref_role = SelectField(
        'Prefer Role', choices=positions, validators=[DataRequired()])
    alternative_role = SelectField('Alternative Role', choices=positions, validators=[
                                   DataRequired(), DifferentRole('pref_role')])
    submit = SubmitField('Edit Profile')


class DeleteProfileForm(FlaskForm):
    delete_button = SubmitField('Delete Profile')


class CreatingTeam(FlaskForm):
    profile = SelectField('Profile', validators=[DataRequired()], choices=[])
    role = SelectField('Select Role', validators=[
                       DataRequired()], choices=positions)
    clash_date = DateTimeLocalField(
        'Clash Date', format='%Y-%m-%dT%H:%M', validators=[DataRequired(), validate_date])
    submit = SubmitField('Create Team')

    def __init__(self, user_id, *args, **kwargs):
        super(CreatingTeam, self).__init__(*args, **kwargs)
        self.profile.choices = [(p.nickname)
                                for p in Profile.query.filter_by(user_id=user_id)]


# klasa wyszukiwania do utworzonych drużyn
class SearchingTeam(FlaskForm):
    profile = SelectField('Profile', validators=[DataRequired()], choices=[])
    role = SelectField('Select Role', choices=positions)
    division = SelectField('Host Division', choices=divisions)
    date = DateField('Date', format='%Y-%m-%d', validators=[Optional()])
    submit = SubmitField('Search')

    def __init__(self, user_id, *args, **kwargs):
        super(SearchingTeam, self).__init__(*args, **kwargs)
        self.profile.choices = [(p.nickname)
                                for p in Profile.query.filter_by(user_id=user_id)]


# klasa wyszukiwania członków drużyny
class SearchingProfile(FlaskForm):
    profile = SelectField('For Profile', validators=[
                          DataRequired()], choices=[], default=None)
    divisions = SelectField('Player Division', choices=divisions)
    role = SelectField('For Positions', choices=positions)
    submit = SubmitField('Search')

    def __init__(self, user_id, *args, **kwargs):
        super(SearchingProfile, self).__init__(*args, **kwargs)
        self.profile.choices = [(p.id, p.nickname)
                                for p in Profile.query.filter_by(user_id=user_id)]


# klasa zapraszania członków drużyny
class InvitePlayer(FlaskForm):
    clashteam = SelectField('Clash Date', validators=[
                            DataRequired()], choices=[], default=None)
    role = SelectField('For Positions', choices=positions)
    submit = SubmitField('Invite')

    def __init__(self, user_teams, *args, **kwargs):
        super(InvitePlayer, self).__init__(*args, **kwargs)
        self.clashteam.choices = [
            (p.id, f'{p.clash_date} - {p.host.server}') for p in user_teams]


# klasa prośby o dołączanie do drużyny
class RequestForm(FlaskForm):
    profile = SelectField('Profile', validators=[
                          DataRequired()], choices=[], default=None)
    role = SelectField('For Positions', choices=[])
    submit = SubmitField('Send request')

    def __init__(self, roles, profiles, *args, **kwargs):
        super(RequestForm, self).__init__(*args, **kwargs)
        self.role.choices = [(r, r.title()) for r in roles]
        self.profile.choices = [(p.id, p.nickname) for p in profiles]


class AnswerForm(FlaskForm):
    accept_button = SubmitField('Accept')
    reject_button = SubmitField('Reject')
    delete_button = SubmitField('Withdraw invitation')