from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo
from models import User, Profile, ClashTeam, ReportPlayer

servers = [('North America', 'NA'), ('West Europe', 'EUW'), ('North and Eeat Europe', 'EUNE')]
positions = [('Toplane', 'Toplane'), ('Jungle', 'Jungle'), ('Midlane', 'Midlane'), ('Bottom', 'Bottom'), ('Support', 'Support')]
divisions = [('Iron', 'Iron'), ('Bronze', 'Bronze'), ('Silver', 'Silver'), ('Gold', 'Gold'), ('Platinum', 'Platinum'), ('Diamond', 'Diamond'), ('higher', 'higher')]
months = [(1, 'January'), (2, 'February'), (3, 'March'), (4, 'April'), (5, 'May'), (6, 'June'), (7, 'July'), (8, 'August'), (9, 'September'), (10, 'October'), (11, 'November'), (12, 'December')]

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField('Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')


class ProfileForm(FlaskForm):
    nickname = StringField('Nickname', validators=[DataRequired()])
    server = SelectField('Server', choices=servers, validators=[DataRequired()])
    division = SelectField('Division', choices=divisions, validators=[DataRequired()])
    pref_role = SelectField('Prefer Role', choices=positions, validators=[DataRequired()])
    alternative_role = SelectField('Alternative Role', choices=positions, validators=[DataRequired(), EqualTo('pref_role', message='Secondary position must be different from main position')])
    submit = SubmitField('Add Profile')


#klasa wyszukiwania do utworzonych drużyn 
class SearchingTeam(FlaskForm):
    profile = SelectField('Profile', coerce=int, validators=[DataRequired()])
    role = SelectField('Select Role', choices=positions)
    month = SelectField('Month', choices=months)
    day_options = [(i, str(i)) for i in range(1, 32)]  # lista opcji od 1 do 31
    day = SelectField('Day', choices=day_options)
    submit = SubmitField('Search')

    def __init__(self, user_id, *args, **kwargs):
        super(SearchingTeam, self).__init__(*args, **kwargs)
        self.profile.choices = [(p.id, p.name) for p in Profile.query.filter_by(user_id=user_id)]



#wysyłanie raportów
class SendReport(FlaskForm):
    title = StringField('Reason for reporting', validators=[DataRequired()])
    text = StringField('Short description', validators=[DataRequired()])
    submit = SubmitField('Send Report')








'''class DestinationForm(FlaskForm):
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
            raise ValidationError('Please use a different email address.')'''