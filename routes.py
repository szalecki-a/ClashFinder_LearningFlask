from app import app, db, login
from flask import request, render_template, flash, redirect, url_for
from models import User, Profile, ClashTeam, ReportPlayer, ClashInvitation
from forms import RegistrationForm, LoginForm, ProfileForm, SearchingTeam, CreatingTeam, SearchingProfile, InvitePlayer, AnswerForm, positions, divisions, get_server_short_name, get_server_name_from_short
from werkzeug.urls import url_parse
from flask_login import LoginManager, UserMixin, login_required, login_user, logout_user, current_user
from sqlalchemy import or_, and_
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
        flash('Congratulations, you are now a registered user!', 'success')
        login_user(user)
        return redirect(url_for('user', username=user.username))
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
                next_page = url_for('user', username=user.username)
            flash('You are logged in', 'success')
            return redirect(next_page)
        else:
            flash('Invalid username or password', 'error')
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
    return render_template('user.html', profiles=profiles, form=form, user=user, get_server_short_name=get_server_short_name)


# ścieżka pozwalająca tworzyć profile i przekierowywuje spowrotem na stronę użytkownika
@app.route('/user/<username>/create_profile', methods=['GET', 'POST'])
@login_required
def create_profile(username):
    user = User.query.filter_by(username=username).first_or_404()
    form = ProfileForm()
    if form.validate_on_submit():
        existing_profile = Profile.query.filter_by(
            nickname=form.nickname.data, server=form.server.data).first()
        if existing_profile is not None:
            flash('A profile with this nickname already exists on this server.', 'error')
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
            flash('Your profile has been created successfully.', 'success')
    return redirect(url_for('user', username=user.username))


# ścieżka strony drużyny
@app.route('/team/<int:teamid>', methods=['GET', 'POST'])
@login_required
def team(teamid):
    team = ClashTeam.query.filter_by(id=teamid).first_or_404()
    return render_template('team.html', team=team, user=current_user)


# ścieżka strony profilu
@app.route('/profile/<server>/<nickname>', methods=['GET', 'POST'])
@login_required
def profile(server, nickname):
    serv = get_server_name_from_short(server.upper())
    profile = Profile.query.filter_by(server=serv, nickname=nickname).first_or_404()
    return render_template('profile.html', server=server, profile=profile, user=current_user, get_server_short_name=get_server_short_name)


# ścieżka drużyn stworzonych przez użytkownika,
# warto rozszerzyć ścieżkę o listę drużyn, których jest członkiem, ale to po stworzeniu mechanizmu dołączania do drużyn
@app.route('/user/<username>/teams', methods=['GET', 'POST'])
@login_required
def yourteams(username):
    user = User.query.filter_by(username=username).first_or_404()
    user_profiles = Profile.query.filter(Profile.user_id == user.id)
    user_clashteams = ClashTeam.query.join(Profile).filter(Profile.id == ClashTeam.host_id, Profile.user_id == user.id).all()
    user_profiles_data = {user_profile.nickname: user_profile.server for user_profile in user_profiles}

    for key, value in user_profiles_data.items():
        guest_teams = ClashTeam.query.join(Profile).filter(and_(or_(ClashTeam.toplane == key, ClashTeam.jungle == key, ClashTeam.midlane == key, ClashTeam.bottom == key, ClashTeam.support == key), Profile.server == value, Profile.user_id != user.id)).all()
    if len(guest_teams)==0:
        guest_teams = []
    if len(user_clashteams)==0:
        user_clashteams = []

    form = CreatingTeam(user_id=user.id)
    return render_template('yourteams.html', get_server_short_name=get_server_short_name, user_clashteams=user_clashteams, guest_teams=guest_teams, form=form, user=user)


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
    form = CreatingTeam(user_id=user.id)
    if form.validate_on_submit():
        current_profile = Profile.query.filter_by(
            nickname=form.profile.data, user_id=user.id).first()
        game_date = datetime(year=datetime.now().year, month=int(
            form.month.data), day=int(form.day.data))
        # for team in user_teams:
        #     if game_date in team.clash_date:
        #         flash('A profile with this nickname already exists on this server.')
        # if existing_profile is not None:
        #     flash('A profile with this nickname already exists on this server.')
        # else:
        new_team = ClashTeam(
            host_id=current_profile.id,
            clash_date=game_date,
            division=current_profile.division,
        )
        if form.role.data == 'Toplane':
            new_team.add_top(current_profile.nickname)
        elif form.role.data == 'Jungle':
            new_team.add_jungle(current_profile.nickname)
        elif form.role.data == 'Midlane':
            new_team.add_midlane(current_profile.nickname)
        elif form.role.data == 'Bottom':
            new_team.add_bottom(current_profile.nickname)
        else:
            new_team.add_support(current_profile.nickname)
        db.session.add(new_team)
        db.session.commit()
        flash('Your Team has been created successfully.', 'success')
    return redirect(url_for('yourteams', username=user.username))


# ścieżka pozwalająca wyszukać drużyny
@app.route('/findteam', methods=['GET', 'POST'])
@login_required
def findteam():
    user = User.query.filter_by(username=current_user.username).first_or_404()
    user_profiles = Profile.query.filter_by(user_id=user.id).all()
    user_clashteams_id = [profile_team.id for user_profile in user_profiles for profile_team in ClashTeam.query.filter_by(host_id=user_profile.id)]
    user_profiles_data = {user_profile.nickname: user_profile.server for user_profile in user_profiles}
    roles = {'Toplane': ClashTeam.toplane, 'Jungle': ClashTeam.jungle, 'Midlane': ClashTeam.midlane, 'Bottom': ClashTeam.bottom, 'Support': ClashTeam.support}

    clash_teams = ClashTeam.query.filter(or_(*(role == None for role in roles.values())), ClashTeam.id.notin_(user_clashteams_id)).order_by(ClashTeam.clash_date)
    for key, value in user_profiles_data.items():
        clash_teams = clash_teams.filter(and_(or_(ClashTeam.toplane.isnot(key), ClashTeam.jungle.isnot(key), ClashTeam.midlane.isnot(key), ClashTeam.bottom.isnot(key), ClashTeam.support.isnot(key)), ClashTeam.host.has(server=value)))
    clash_teams_list = clash_teams.all()
    if len(clash_teams_list)==0:
        clash_teams = []

    form = SearchingTeam(user_id=user.id)
    if form.validate_on_submit():
        if form.division.data == 'None':
            div = ['Iron', 'Bronze', 'Silver', 'Gold', 'Platinum',
                   'Diamond', 'Master', 'Grandmaster', 'Challenger']
        else:
            div = [form.division.data]
        if form.role.data == 'Toplane':
            clash_teams = ClashTeam.query.join(Profile).filter(Profile.division.in_(
                div), ClashTeam.toplane.is_(None)).order_by(ClashTeam.clash_date).all()
        elif form.role.data == 'Jungle':
            clash_teams = ClashTeam.query.join(Profile).filter(Profile.division.in_(
                div), ClashTeam.jungle.is_(None)).order_by(ClashTeam.clash_date).all()
        elif form.role.data == 'Midlane':
            clash_teams = ClashTeam.query.join(Profile).filter(Profile.division.in_(
                div), ClashTeam.midlane.is_(None)).order_by(ClashTeam.clash_date).all()
        elif form.role.data == 'Bottom':
            clash_teams = ClashTeam.query.join(Profile).filter(Profile.division.in_(
                div), ClashTeam.bottom.is_(None)).order_by(ClashTeam.clash_date).all()
        elif form.role.data == 'Support':
            clash_teams = ClashTeam.query.join(Profile).filter(Profile.division.in_(
                div), ClashTeam.support.is_(None)).order_by(ClashTeam.clash_date).all()
        else:
            clash_teams = ClashTeam.query.join(Profile).filter(
                Profile.division.in_(div)).order_by(ClashTeam.clash_date).all()
    return render_template('findteam.html', get_server_short_name=get_server_short_name, clash_teams=clash_teams, form=form, user=user)


# ścieżka pozwalająca wyszukać zawodników
@app.route('/findteammates', methods=['GET', 'POST'])
@login_required
def findteammates():
    user = User.query.filter_by(username=current_user.username).first_or_404()
    user_profiles = Profile.query.filter_by(user_id=user.id).all()
    user_profiles_id = []
    for user_profile in user_profiles:
        user_profiles_id.append(user_profile.id)
    find_teammates = Profile.query.filter(
        Profile.id.notin_(user_profiles_id)).all()
    if len(find_teammates) == 0:
        find_teammates = []
    form = SearchingProfile(user_id=user.id)
    if form.validate_on_submit():
        current_profile = Profile.query.filter_by(
            id=form.profile.data).first_or_404()
        if form.role.data == 'None':
            roles = ['Toplane', 'Jungle', 'Midlane', 'Bottom', 'Support']
        else:
            roles = [form.role.data]
        if form.divisions.data == 'None':
            div = ['Iron', 'Bronze', 'Silver', 'Gold', 'Platinum',
                   'Diamond', 'Master', 'Grandmaster', 'Challenger']
        else:
            div = [form.divisions.data]
        find_teammates = Profile.query.filter(or_(Profile.best_position.in_(roles), Profile.alternative_position.in_(
            roles)), Profile.division.in_(div), Profile.server == current_profile.server, Profile.id.notin_(user_profiles_id))
    return render_template('findteammates.html', get_server_short_name=get_server_short_name, find_teammates=find_teammates, form=form, user=user, user_profiles=user_profiles)


# ścieżka pozwalająca zapraszać zawodników
# ZWRÓCIĆ UWAGĘ, ZE BĘDZIEMY ZAPRASZAĆ PROFILE
@app.route('/invite/<int:user_id>/<int:guest_id>', methods=['GET', 'POST'])
@login_required
def inviteteammates(user_id, guest_id):
    user = User.query.filter_by(id=current_user.id).first_or_404()
    user_profiles = Profile.query.filter_by(user_id=user.id).all()
    user_teams = []
    for profile in user_profiles:
        teams = ClashTeam.query.filter_by(host_id=profile.id).all()
        user_teams.extend(teams)
    inv_guest = Profile.query.filter_by(id=guest_id).first_or_404()
    form = InvitePlayer(user_teams)
    return render_template('invitations.html', form=form, user=user, user_teams=user_teams, inv_guest=inv_guest)


# ścieżka pozwalająca zapraszać zawodników cd
# ZWRÓCIĆ UWAGĘ, ZE BĘDZIEMY ZAPRASZAĆ PROFILE
@app.route('/invitation/<int:user_id>/<int:guest_id>', methods=['GET', 'POST'])
@login_required
def sendinvitation(user_id, guest_id):
    user = User.query.filter_by(id=current_user.id).first_or_404()
    user_profiles = Profile.query.filter_by(user_id=user.id).all()
    user_teams = []
    for profile in user_profiles:
        teams = ClashTeam.query.filter_by(host_id=profile.id).all()
        user_teams.extend(teams)
    inv_guest = Profile.query.filter_by(id=guest_id).first_or_404()
    form = InvitePlayer(user_teams)
    if form.validate_on_submit():
        inv_for_team = ClashTeam.query.filter_by(
            id=form.clashteam.data).first_or_404()
        inv_for_position = getattr(inv_for_team, form.role.data.lower())
        if inv_for_position is not None:
            flash('This position in your team is already taken', 'error')
            return redirect(url_for('inviteteammates', user_id=user_id, guest_id=guest_id))
        else:
            new_inv = ClashInvitation(
                futureteam_id=inv_for_team.id,
                role=form.role.data,
                lider_id=user.id,
                guestprofile_id=inv_guest.id,
            )
            db.session.add(new_inv)
            db.session.commit()
            flash('Your invitation has been sent', 'success')
            return redirect(url_for('findteammates'))
    return redirect(url_for('findteammates'))


# ścieżka drużyn stworzonych przez użytkownika,
@app.route('/user/<username>/mailbox', methods=['GET', 'POST'])
@login_required
def mailbox(username):
    user = User.query.filter_by(username=username).first_or_404()
    profiles = Profile.query.filter_by(user_id=user.id).all()
    profiles_id = []
    for profile in profiles:
        profiles_id.append(profile.id)
    in_invitations = ClashInvitation.query.filter(
        ClashInvitation.guestprofile_id.in_(profiles_id)).all()
    if len(in_invitations) == 0:
        in_invitations = []
    out_invitations = ClashInvitation.query.filter_by(lider_id=user.id).all()
    if len(out_invitations) == 0:
        out_invitations = []
    form = AnswerForm()
    return render_template('mailbox.html', form=form, in_invitations=in_invitations, out_invitations=out_invitations, get_server_short_name=get_server_short_name, user=user)


@app.route('/user/<username>/mailbox/answer', methods=['GET', 'POST'])
@login_required
def answer(username):
    user = User.query.filter_by(username=username).first_or_404()
    form = AnswerForm()
    if form.validate_on_submit():
        in_invitation_id = request.form['id_in']
        reviewd_invitation = ClashInvitation.query.filter_by(
            id=in_invitation_id).first_or_404()
        if form.reject_button.data:
            db.session.delete(reviewd_invitation)
            db.session.commit()
            flash('The invitation has been rejected.', 'message')
        elif form.accept_button.data:
            team_to_join = ClashTeam.query.filter_by(
                id=reviewd_invitation.futureteam_id).first_or_404()
            join_position = getattr(team_to_join, reviewd_invitation.role.lower())
            new_teammember = Profile.query.filter_by(
                id=reviewd_invitation.guestprofile_id).first_or_404()
            if join_position is not None:
                flash('This position is already taken', 'error')
            else:
                if reviewd_invitation.role == 'Toplane':
                    team_to_join.add_top(new_teammember.nickname)
                elif reviewd_invitation.role == 'Jungle':
                    team_to_join.add_jungle(new_teammember.nickname)
                elif reviewd_invitation.role == 'Midlane':
                    team_to_join.add_midlane(new_teammember.nickname)
                elif reviewd_invitation.role == 'Bottom':
                    team_to_join.add_bottom(new_teammember.nickname)
                else:
                    reviewd_invitation.role.add_support(new_teammember.nickname)
                flash('You have joined the team successfully.', 'success')
                db.session.delete(reviewd_invitation)
                db.session.add(team_to_join)
                db.session.commit()
    return redirect(url_for('mailbox', username=user.username))

#wycofywanie zaproszeń
@app.route('/user/<username>/mailbox/answer/del', methods=['GET', 'POST'])
@login_required
def answerdel(username):
    user = User.query.filter_by(username=username).first_or_404()
    form = AnswerForm()
    if form.validate_on_submit():
        if form.delete_button.data:
            out_invitation_id = request.form['id_out']
            delsend_invitation = ClashInvitation.query.filter_by(
                id=out_invitation_id).first_or_404()
            db.session.delete(delsend_invitation)
            db.session.commit()
            flash('Invitation deleted successfully.', 'success')
            return redirect(url_for('mailbox', username=user.username))
    return redirect(url_for('mailbox', username=user.username))


# ścieżka wylogowywująca użytkownika
@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('index'))
