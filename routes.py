from app import app, db
from flask import request, render_template, flash, redirect, url_for
from models import User, Profile, ClashTeam, ReportPlayer
from forms import RegistrationForm, LoginForm, ProfileForm, SearchingTeam, SendReport
from werkzeug.urls import url_parse
from flask_login import LoginManager, UserMixin, login_required, login_user, logout_user, current_user


# stworzyć model strony z profilem (w zawartości nazwa konta, email, lista profili)
# stworzyć model strony profilu (serwer, dywizja, preferowana pozycja)
# stworzyć model strony z tworzeniem profilu, może warto stworzyć to poniżej listy z profilami

@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    # sprawdzam czy current_user jest zalogowany, jeżeli jest przekierowywujego na stronę startową
    # if current_user.is_authenticated:
    # return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('index'))
    return render_template('register.html', title='Register', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    # sprawdzam czy current_user jest zalogowany, jeżeli jest przekierowywujego na stronę startową
    if current_user.is_authenticated:
        return redirect(url_for('user'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember.data)
        next_page = request.args.get('user')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('login.html', form=form)


@app.route('/user/<username>', methods=['GET', 'POST'])
@login_required
def user(username):
    user = current_user
    user = User.query.filter_by(username=user.username).first()
    profiles = Profile.query.filter_by(user_id=user.id)
    if profiles is None:
        profiles = []
    form = ProfileForm()
    if request.method == 'POST' and form.validate():
        new_profile = Profile(nickname=form.nickname.data, server=form.server.data, division=form.division.data,
                              best_position=form.pref_role.data, alternative_position=form.alternative_role.data, user_id=current_user.id)
        db.session.add(new_profile)
        db.session.commit()
    # else:
        # flash(form.errors)
    return render_template('user.html', username=user.username, email=user.email, profiles=profiles, form=form)


'''
@app.route('/user/<username>/profiles',methods=['GET', 'POST'])
@login_required
def profiles(username):
	user = current_user
	user = User.query.filter_by(username=user.username).first_or_404()
	profiles = Profile.query.filter_by(user_id=user.id)
	return render_template('profile.html', user = user, profiles=profiles)
'''


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))
