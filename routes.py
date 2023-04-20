from app import app, db, login
from flask import request, render_template, flash, redirect, url_for
from models import User, Profile, ClashTeam, ReportPlayer, ClashInvitation
from forms import RegistrationForm, LoginForm, ProfileForm, SearchingTeam, CreatingTeam, SearchingProfile, InvitePlayer, positions, divisions
from werkzeug.urls import url_parse
from flask_login import LoginManager, UserMixin, login_required, login_user, logout_user, current_user
from sqlalchemy import or_
from datetime import datetime


@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html', user=current_user)


@app.route('/register', methods=['GET', 'POST'])
def register():
    # sprawdzam czy current_user jest zalogowany, TRUE przekierowywuje na stronę użytkownika
    if current_user.is_authenticated:
        return redirect(url_for('user', username=current_user.username))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('index'))
    return render_template('register.html', title='Register', form=form, user=current_user)


@app.route('/login', methods=['GET', 'POST'])
def login():
    # sprawdzam czy current_user jest zalogowany, TRUE przekierowywuje na stronę użytkownika
    if current_user.is_authenticated:
        return redirect(url_for('user', username=current_user.username))
    user = current_user
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
    return render_template('login.html', form=form, user=user)


# ścieżka strony użytkownika, która pokazuje dane konta, profile oraz pozwala tworzyć profile
@app.route('/user/<username>', methods=['GET', 'POST'])
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    profiles = Profile.query.filter_by(user_id=user.id).all()
    if len(profiles) == 0:
        profiles = []
    form = ProfileForm()
    return render_template('user.html', profiles=profiles, form=form, user=user)


# ścieżka pozwalająca tworzyć profile i przekierowywuje spowrotem na stronę użytkownika
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


# ścieżka strony drużyny
@app.route('/team/<int:teamid>', methods=['GET', 'POST'])
@login_required
def team(teamid):
    team = ClashTeam.query.filter_by(id=teamid).first_or_404()
    return render_template('team.html', team=team, user=current_user)


# ścieżka strony profilu
@app.route('/profile/<int:profid>', methods=['GET', 'POST'])
@login_required
def profile(profid):
    profile = Profile.query.filter_by(id=profid).first_or_404()
    return render_template('profile.html', profile=profile, user=current_user)


# ścieżka drużyn stworzonych przez użytkownika, 
#warto rozszerzyć ścieżkę o listę drużyn, których jest członkiem, ale to po stworzeniu mechanizmu dołączania do drużyn
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

# ścieżka pozwalająca tworzyć drużyny i przekierowywuje spowrotem na stronę drużyn użytkownika
# rozszerzyć o sprawdzanie daty tworzenia drużyny, może dodać pole z rokiem...
@app.route('/user/<username>/createteam', methods=['GET', 'POST'])
@login_required
def createteam(username):
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


#ścieżka pozwalająca wyszukać drużyny
@app.route('/findteam', methods=['GET', 'POST'])
@login_required
def findteam():
    user = User.query.filter_by(username=current_user.username).first_or_404()
    clash_teams = ClashTeam.query.filter(or_(ClashTeam.toplane==None, ClashTeam.jungle==None, ClashTeam.midlane==None, ClashTeam.adcarry==None, ClashTeam.support==None)).order_by(ClashTeam.clash_date).all()
    if len(clash_teams) == 0:
        clash_teams = []
    form = SearchingTeam(user_id = user.id)
    if form.validate_on_submit():
        if form.division.data=='None':
            div = ['Iron', 'Bronze', 'Silver', 'Gold', 'Platinum', 'Diamond', 'Master', 'Grandmaster', 'Challenger']
        else:
            div = [form.division.data]
        if form.role.data == 'Toplane':
            clash_teams = ClashTeam.query.join(Profile).filter(Profile.division.in_(div), ClashTeam.toplane.is_(None)).order_by(ClashTeam.clash_date).all()
        elif form.role.data == 'Jungle':
          clash_teams = ClashTeam.query.join(Profile).filter(Profile.division.in_(div), ClashTeam.jungle.is_(None)).order_by(ClashTeam.clash_date).all()
        elif form.role.data == 'Midlane':
          clash_teams = ClashTeam.query.join(Profile).filter(Profile.division.in_(div), ClashTeam.midlane.is_(None)).order_by(ClashTeam.clash_date).all()
        elif form.role.data == 'Bottom':
          clash_teams = ClashTeam.query.join(Profile).filter(Profile.division.in_(div), ClashTeam.adcarry.is_(None)).order_by(ClashTeam.clash_date).all()
        elif form.role.data == 'Support':
          clash_teams = ClashTeam.query.join(Profile).filter(Profile.division.in_(div), ClashTeam.support.is_(None)).order_by(ClashTeam.clash_date).all()
        else:
            clash_teams = ClashTeam.query.join(Profile).filter(Profile.division.in_(div)).order_by(ClashTeam.clash_date).all()
    return render_template('findteam.html', clash_teams=clash_teams, form=form, user=user)


#ścieżka pozwalająca wyszukać zawodników
@app.route('/findteammates', methods=['GET', 'POST'])
@login_required
def findteammates():
    user = User.query.filter_by(username=current_user.username).first_or_404()
    user_profiles = Profile.query.filter_by(user_id=user.id).all()
    find_teammates = Profile.query.all()
    if len(find_teammates) == 0:
        find_teammates = []
    form = SearchingProfile(user_id = user.id)
    if form.validate_on_submit():
        current_profile = Profile.query.filter_by(id=form.profile.data).first_or_404()
        if form.role.data == 'None':
            roles = ['Toplane', 'Jungle', 'Midlane', 'Bottom', 'Support']
        else:
            roles = [form.role.data]
        if form.divisions.data == 'None':
            div = ['Iron', 'Bronze', 'Silver', 'Gold', 'Platinum', 'Diamond', 'Master', 'Grandmaster', 'Challenger']
        else:
            div = [form.divisions.data]   
        find_teammates = Profile.query.filter(or_(Profile.best_position.in_(roles), Profile.alternative_position.in_(roles)), Profile.division.in_(div), Profile.server==current_profile.server)
    return render_template('findteammates.html', find_teammates=find_teammates, form=form, user=user, user_profiles=user_profiles)


#ścieżka pozwalająca zapraszać zawodników
#ZWRÓCIĆ UWAGĘ, ZE BĘDZIEMY ZAPRASZAĆ PROFILE
@app.route('/invite/<int:user_id>/<int:guest_id>', methods=['GET', 'POST'])
@login_required
def inviteteammates(user_id, guest_id):
    user = User.query.filter_by(id=current_user.id).first_or_404()
    user_profiles = Profile.query.filter_by(user_id=user.id).all()
    inv_guest = Profile.query.filter_by(id=guest_id).first_or_404()
    form = InvitePlayer(user_profiles)
    return render_template('invitations.html', form=form, user=user, user_profiles=user_profiles, inv_guest=inv_guest)
        

#ścieżka pozwalająca zapraszać zawodników cd
#ZWRÓCIĆ UWAGĘ, ZE BĘDZIEMY ZAPRASZAĆ PROFILE
@app.route('/sendinvitation/<int:user_id>/<int:guest_id>', methods=['GET', 'POST'])
@login_required
def sendinvitation(user_id, guest_id):
    user = User.query.filter_by(id=current_user.id).first_or_404()
    user_profiles = Profile.query.filter_by(user_id=user.id).all()
    inv_guest = Profile.query.filter_by(id=guest_id).first_or_404()
    form = InvitePlayer(user_profiles)
    if form.validate_on_submit():
        inv_for_team = ClashTeam.query.filter_by(id=form.clashteam.data).first_or_404()
        new_inv = ClashInvitation(
            team_id = inv_for_team.id,
            role = form.role.data,
            host = user.id,
            guestprofile = inv_guest.id,
        )
        db.session.add(new_inv)
        db.session.commit()
    return redirect(url_for('inviteteammates', user_id=user.id, guest_id=inv_guest.id))
 

# ścieżka drużyn stworzonych przez użytkownika, 
#warto rozszerzyć ścieżkę o listę drużyn, których jest członkiem, ale to po stworzeniu mechanizmu dołączania do drużyn
@app.route('/user/<username>/inbox', methods=['GET', 'POST'])
@login_required
def inbox(username):
    user = User.query.filter_by(username=username).first_or_404()
    profiles = Profile.query.filter_by(user_id=user.id).all()
    profiles_id = []
    for profile in profiles:
        profiles_id.extend(profile.id)
    invitations = ClashInvitation.query.filter(ClashInvitation.guestprofile.in_(profiles_id)).all()
    if len(invitations) == 0:
        invitations = []
    return render_template('inbox.html', invitations=invitations, user=user)


#ścieżka wylogowywująca użytkownika
@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))