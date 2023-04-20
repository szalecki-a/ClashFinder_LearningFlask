from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField, SelectMultipleField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo
from models import Profile

servers = [('NA', 'NA'), ('EUW', 'EUW'),
           ('EUNE', 'EUNE')]
positions = [(None, ''), ('Toplane', 'Toplane'), ('Jungle', 'Jungle'),
             ('Midlane', 'Midlane'), ('Bottom', 'Bottom'), ('Support', 'Support')]
divisions = [(None, ''), ('Iron', 'Iron'), ('Bronze', 'Bronze'), ('Silver', 'Silver'), ('Gold','Gold'), ('Platinum', 'Platinum'), 
             ('Diamond', 'Diamond'), ('Master', 'Master'), ('Grandmaster', 'Grandmaster'), ('Challenger', 'Challenger')]
months = [(1, 'January'), (2, 'February'), (3, 'March'), (4, 'April'), (5, 'May'), (6, 'June'),
          (7, 'July'), (8, 'August'), (9, 'September'), (10, 'October'), (11, 'November'), (12, 'December')]
months_days = {'January': 31, 'February': 28, 'March': 31, 'April': 30, 'May': 31, 'June': 30,
               'July': 31, 'August': 31, 'September': 30, 'October': 31, 'November': 30, 'December': 31}
month_dict = {month_name: month_num for month_num, month_name in months}
month_dict2 = {month_num: month_name for month_num, month_name in months}

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


class CreatingTeam(FlaskForm):
    profile = SelectField('Profile', validators=[DataRequired()], choices=[])
    role = SelectField('Select Role', validators=[DataRequired()], choices=positions)
    month = SelectField('Month', choices=months)
    day_options = [(i, i) for i in range(1, 32)]
    day = SelectField('Day', choices=day_options)
    submit = SubmitField('Create Team')

    def __init__(self, user_id, *args, **kwargs):
        super(CreatingTeam, self).__init__(*args, **kwargs)
        self.profile.choices = [(p.nickname) for p in Profile.query.filter_by(user_id=user_id)]


# klasa wyszukiwania do utworzonych drużyn
class SearchingTeam(FlaskForm):
    profile = SelectField('Profile', validators=[DataRequired()], choices=[], default=None)
    role = SelectField('Select Role', choices=positions)
    division = SelectField('Host Division', choices=divisions)
    submit = SubmitField('Search')

    def __init__(self, user_id, *args, **kwargs):
        super(SearchingTeam, self).__init__(*args, **kwargs)
        self.profile.choices = [(p.nickname) for p in Profile.query.filter_by(user_id=user_id)]


# klasa wyszukiwania członków drużyny
class SearchingProfile(FlaskForm):
    profile = SelectField('For Profile', validators=[DataRequired()], choices=[], default=None)
    divisions = SelectField('Player Division', choices=divisions)
    role = SelectField('For Positions', choices=positions)
    submit = SubmitField('Search')

    def __init__(self, user_id, *args, **kwargs):
        super(SearchingProfile, self).__init__(*args, **kwargs)
        self.profile.choices = [(p.id, p.nickname) for p in Profile.query.filter_by(user_id=user_id)]


# klasa wyszukiwania członków drużyny
class InvitePlayer(FlaskForm):
    clashteam = SelectField('Clash Date', validators=[DataRequired()], choices=[], default=None)
    role = SelectField('For Positions', choices=positions)
    submit = SubmitField('Invite')

    def __init__(self, user_profiles, *args, **kwargs):
        super(InvitePlayer, self).__init__(*args, **kwargs)
        self.clashteam.choices = [(p.id, f'{p.clash_date} - {p.host.server}') for p in user_profiles]


class AnswerForm(FlaskForm):
    answer = BooleanField('Akceptuję', validators=[DataRequired()])
    accept_button = SubmitField('Accept')
    reject_button = SubmitField('Reject')

    def validate(self):
        if not FlaskForm.validate(self):
            return False

        if self.accept_button.data:
            self.accept.data = True
        elif self.reject_button.data:
            self.accept.data = False
        else:
            self.accept.errors.append('Musisz wybrać jedno z dwóch')

        return True


'''
# wysyłanie raportów
class SendReport(FlaskForm):
    title = StringField('Reason for reporting', validators=[DataRequired()])
    text = StringField('Short description', validators=[DataRequired()])
    submit = SubmitField('Send Report')


class DestinationForm(FlaskForm):
    city = StringField('city')
    country = StringField('country')
    description = StringField('description')
    submit = SubmitField('Post')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Please use a different username.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Please use a different email address.')
'''
