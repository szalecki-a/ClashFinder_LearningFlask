from app import app, db, login
from flask import request, render_template, flash, redirect, url_for
from models import User, Profile, ClashTeam, ReportPlayer
from forms import RegistrationForm, LoginForm, ProfileForm, SearchingTeam, CreatingTeam, month_dict
from werkzeug.urls import url_parse
from flask_login import LoginManager, UserMixin, login_required, login_user, logout_user, current_user
from datetime import datetime

# stworzyć model strony z profilem (w zawartości nazwa konta, email, lista profili)
# stworzyć model strony profilu (serwer, dywizja, preferowana pozycja)
# stworzyć model strony z tworzeniem profilu, może warto stworzyć to poniżej listy z profilami

@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    # sprawdzam czy current_user jest zalogowany, jeżeli jest przekierowywujego na stronę startową
    if current_user.is_authenticated:
        return redirect(url_for('index'))
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
    # sprawdzam czy current_user jest zalogowany, jeżeli jest przekierowywuję go na stronę startową
    if current_user.is_authenticated:
        return redirect(url_for('user', username=current_user.username))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            next_page = request.args.get('next')
            if not next_page or url_parse(next_page).netloc != '':
                next_page = url_for('user', username = user.username)
            return redirect(next_page)
        else:
            flash('Invalid username or password')

    return render_template('login.html', form=form)


@app.route('/user/<username>', methods=['GET', 'POST'])
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    profiles = Profile.query.filter_by(user_id=user.id).all()
    if len(profiles) == 0:
        profiles = []
    form = ProfileForm()
    # if form.validate_on_submit():
    #     existing_profile = Profile.query.filter_by(nickname=form.nickname.data, server=form.server.data).first()
    #     if existing_profile is not None:
    #         print("profil istnieje")
    #         flash('A profile with this nickname already exists on this server.')
    #     else:
    #         print("tworze profil")
    #         new_profile = Profile(
    #             nickname=form.nickname.data, 
    #             server=form.server.data, 
    #             division=form.division.data,
    #             best_position=form.pref_role.data, 
    #             alternative_position=form.alternative_role.data, 
    #             user_id=current_user.id
    #         )
    #         db.session.add(new_profile)
    #         print("dodaje profil")
    #         db.session.commit()
    #         flash('Your profile has been created successfully.')

    #         # Przekierowanie użytkownika na stronę z listą profili po dodaniu nowego profilu
    #         return redirect(url_for('user', username=current_user.username))
    # else:
    #     print("validacja niepoprawna")
    return render_template('user.html', profiles=profiles, form=form, user=current_user, title='User Profile')


@app.route('/user/<username>/create_profile', methods=['GET', 'POST'])
@login_required
def create_profile(username):
    user = User.query.filter_by(username=username).first_or_404()
    form = ProfileForm()
    if form.validate_on_submit():
        existing_profile = Profile.query.filter_by(nickname=form.nickname.data, server=form.server.data).first()
        if existing_profile is not None:
            flash('A profile with this nickname already exists on this server.')
        else:
            print("dodaje profil")
            new_profile = Profile(
                nickname=form.nickname.data, 
                server=form.server.data, 
                division=form.division.data,
                best_position=form.pref_role.data, 
                alternative_position=form.alternative_role.data, 
                user_id=user.id
            )
            db.session.add(new_profile)
            db.session.commit()
            flash('Your profile has been created successfully.')
    return redirect(url_for('user', username=user.username))


@app.route('/user/<username>/teams', methods=['GET', 'POST'])
@login_required
def yourteams(username):
    user = User.query.filter_by(username=username).first_or_404()
    profiles = Profile.query.filter_by(user_id=user.id).all()
    if len(profiles) == 0:
        profiles = []
    your_clash_teams = []
    for profile in profiles:
        profile_teams = ClashTeam.query.filter_by(host_id=profile.id).all()
        if profile_teams:
            your_clash_teams.extend(profile_teams)
    form = CreatingTeam(user_id = user.id)
    return render_template('yourteams.html', your_clash_teams=your_clash_teams, form=form, user=user)


@app.route('/user/<username>/create_team', methods=['GET', 'POST'])
@login_required
def create_team(username):
    user = User.query.filter_by(username=username).first_or_404()
    user_profiles = Profile.query.filter_by(user_id=user.id).all()
    user_teams = []
    for profile in user_profiles:
        teams = ClashTeam.query.filter_by(host_id=profile.id).all()
        user_teams.extend(teams)
    form = CreatingTeam(user_id = user.id)
    if form.validate_on_submit():
        current_profile = Profile.query.filter_by(nickname=form.profile.data, user_id = user.id).first()
        game_date = datetime(year=datetime.now().year, month=int(form.month.data), day=int(form.day.data))
        # for team in user_teams:
        #     if game_date in team.clash_date:
        #         flash('A profile with this nickname already exists on this server.')
        # if existing_profile is not None:
        #     flash('A profile with this nickname already exists on this server.')
        # else:
        new_team = ClashTeam(
            host_id = current_profile.id,
            clash_date = game_date,
            division = current_profile.division,            
        )
        if form.role.data == 'Toplane':
            new_team.add_top(current_profile.nickname)
        elif form.role.data == 'Jungle':
            new_team.add_jungle(current_profile.nickname)
        elif form.role.data == 'Midlane':
            new_team.add_midlane(current_profile.nickname)
        elif form.role.data == 'Bottom':
            new_team.add_adcarry(current_profile.nickname)
        else:
            new_team.add_support(current_profile.nickname)
        db.session.add(new_team)
        db.session.commit()
        flash('Your Team has been created successfully.')
    return redirect(url_for('yourteams', username=user.username))







@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))
