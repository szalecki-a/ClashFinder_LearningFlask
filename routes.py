from app import app, db, login
from flask import request, render_template, flash, redirect, url_for
from models import User, Profile, ClashTeam, ReportPlayer, ClashInvitation, ClashRequest
from forms import RegistrationForm, LoginForm, ProfileForm, SearchingTeam, CreatingTeam, SearchingProfile, InvitePlayer, AnswerForm, RequestForm, EditProfileForm, DeleteProfileForm, positions, divisions, ROLES_DICT, get_server_short_name, get_server_name_from_short
from werkzeug.urls import url_parse
from flask_login import LoginManager, UserMixin, login_required, login_user, logout_user, current_user
from sqlalchemy import or_, and_, inspect, func
from datetime import datetime, time
from apscheduler.schedulers.background import BackgroundScheduler


@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html', user=current_user)


@app.route('/about', methods=['GET', 'POST'])
def about():
    return render_template('about.html', user=current_user)


@app.route('/register', methods=['GET', 'POST'])
def register():
    # sprawdzam czy current_user jest zalogowany, TRUE przekierowywuje na stronę użytkownika
    if current_user.is_authenticated:
        return redirect(url_for('user', username=current_user.username))
    form = RegistrationForm()
    if form.validate_on_submit():
        existing_username = User.query.filter_by(
            username=form.username.data).first()
        if existing_username is not None:
            flash('A account with this username already exists on this server.', 'error')
        
        existing_email = User.query.filter_by(email=form.email.data).first()
        if existing_email is not None:
            flash('This email has already been used', 'error')
        
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


# ścieżka edycji profilu
@app.route('/user/<username>/<int:profile_id>/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile(username, profile_id):
    user = User.query.filter_by(username=username).first_or_404()
    profile = Profile.query.filter_by(id=profile_id).first_or_404()
    form1 = EditProfileForm()
    form2 = DeleteProfileForm()
    if form1.validate_on_submit():
        existing_profile = Profile.query.filter_by(
            nickname=form1.nickname.data, server=form1.server.data).first()
        if existing_profile is not None:
            flash('A profile with this nickname already exists on this server.', 'error')
        else:
            profile.nickname = form1.nickname.data
            profile.server = form1.server.data
            profile.division = form1.division.data
            profile.best_position = form1.pref_role.data
            profile.alternative_position = form1.alternative_role.data

            db.session.add(profile)
            db.session.commit()
            flash('Your profile has been updated.', 'success')
        return redirect(url_for('user', username=user.username))
    
    if form2.delete_button.data:
        db.session.delete(profile)
        db.session.commit()
        flash('Your profile has been deleted.', 'message')
        return redirect(url_for('user', username=user.username))
    
    return render_template('profile_edit.html', profile=profile, form1=form1, form2=form2, user=user)


# ścieżka strony profilu
@app.route('/profile/<server>/<nickname>', methods=['GET', 'POST'])
@login_required
def profile(server, nickname):
    user = User.query.join(Profile).filter(Profile.nickname == nickname,
                                           Profile.server == get_server_name_from_short(server.upper())).first()
    serv = get_server_name_from_short(server.upper())
    profile = Profile.query.filter_by(
        server=serv, nickname=nickname).first_or_404()
    return render_template('profile.html', server=server, profile=profile, user=user, get_server_short_name=get_server_short_name)


# ścieżka drużyn stworzonych przez użytkownika,
@app.route('/user/<username>/teams', methods=['GET', 'POST'])
@login_required
def yourteams(username):
    user = User.query.filter_by(username=username).first_or_404()
    user_profiles = Profile.query.filter(Profile.user_id == user.id)
    user_clashteams = ClashTeam.query.join(Profile).filter(
        Profile.id == ClashTeam.host_id, Profile.user_id == user.id).all()
    user_profiles_data = {
        user_profile.nickname: user_profile.server for user_profile in user_profiles}
    guest_teams = []
    for key, value in user_profiles_data.items():
        guest_teams.extend(ClashTeam.query.join(Profile).filter(and_(or_(ClashTeam.toplane == key, ClashTeam.jungle == key, ClashTeam.midlane ==
                           key, ClashTeam.bottom == key, ClashTeam.support == key), Profile.server == value, Profile.user_id != user.id)).all())
    if len(user_clashteams) == 0:
        user_clashteams = []

    form = CreatingTeam(user_id=user.id, timerighnow=datetime.now())
    return render_template('yourteams.html', get_server_short_name=get_server_short_name, user_clashteams=user_clashteams, guest_teams=guest_teams, form=form, user=user)


# ścieżka pozwalająca tworzyć drużyny i przekierowywuje spowrotem na stronę drużyn użytkownika
@app.route('/user/<username>/createteam', methods=['GET', 'POST'])
@login_required
def createteam(username):
    user = User.query.filter_by(username=username).first_or_404()
    form = CreatingTeam(user_id=user.id)
    if form.validate_on_submit():
        current_profile = Profile.query.filter_by(
            nickname=form.profile.data, user_id=user.id).first()
        new_team = ClashTeam(
            host_id=current_profile.id,
            clash_date=form.clash_date.data,
            division=current_profile.division,
        )
        position_to_function = {
            'Toplane': new_team.add_top,
            'Jungle': new_team.add_jungle,
            'Midlane': new_team.add_midlane,
            'Bottom': new_team.add_bottom,
            'Support': new_team.add_support,
        }

        if form.role.data not in position_to_function:
            raise ValueError('Invalid role selected')

        add_player = position_to_function[form.role.data]
        add_player(current_profile.nickname)
        db.session.add(new_team)
        db.session.commit()
        flash('Your Team has been created successfully.', 'success')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'Invalid date field: {error}', 'error')
    return redirect(url_for('yourteams', username=user.username))


# funkcja usuwania członków drużyny
@app.route('/user/<username>/team/<int:team_id>/<position>/delete', methods=['GET', 'POST'])
@login_required
def delete_teammate(username, team_id, position):
    user = User.query.filter_by(username=username).first_or_404()
    team_to_update = ClashTeam.query.filter_by(id=team_id).first_or_404()
    role = position.title()
    if role not in ROLES_DICT:
        flash('Invalid role.', 'error')
        return redirect(url_for('team', teamid=team_id))
    
    setattr(team_to_update, ROLES_DICT[role], None)
    db.session.add(team_to_update)
    db.session.commit()
    flash('Teammate deleted successfully.', 'success')
    return redirect(url_for('team', teamid=team_id))

# funkcja odejścia z drużyny


@app.route('/user/<username>/team/<int:team_id>/<profile>/leave', methods=['GET', 'POST'])
@login_required
def leave_team(username, team_id, profile):
    user = User.query.filter_by(username=username).first_or_404()
    team_to_leave = ClashTeam.query.filter_by(id=team_id).first_or_404()
    leaving_profile = Profile.query.filter_by(
        nickname=profile, user_id=user.id).first_or_404()
    if not any(getattr(team_to_leave, role) == leaving_profile.nickname for role in ROLES_DICT.values()):
        flash('You are not a member of this team.', 'error')
        return redirect(url_for('user', username=user.username))
    for role, column in ROLES_DICT.items():
        if getattr(team_to_leave, column) == leaving_profile.nickname:
            setattr(team_to_leave, column, None)
            db.session.add(team_to_leave)
            db.session.commit()
            flash('You have left the team.', 'success')
            break
    return redirect(url_for('user', username=user.username))


# ścieżka strony drużyny
@app.route('/team/<int:teamid>', methods=['GET', 'POST'])
@login_required
def team(teamid):
    team = ClashTeam.query.filter_by(id=teamid).first_or_404()
    return render_template('team.html', team=team, user=current_user)


# ścieżka skrzynki pocztowej uzytkownika,
@app.route('/user/<username>/mailbox', methods=['GET', 'POST'])
@login_required
def mailbox(username):
    user = User.query.filter_by(username=username).first_or_404()
    profiles = Profile.query.filter_by(user_id=user.id).all()
    profiles_id = [profile.id for profile in profiles]
    in_invitations = ClashInvitation.query.filter(
        ClashInvitation.guestprofile_id.in_(profiles_id)).all() or []
    in_requests = ClashRequest.query.filter_by(team_host=user.id).all() or []
    out_invitations = ClashInvitation.query.filter_by(
        lider_id=user.id).all() or []
    out_requests = ClashRequest.query.filter(
        ClashRequest.candidate_id.in_(profiles_id)).all() or []
    form = AnswerForm()
    return render_template('mailbox.html', form=form, in_invitations=in_invitations, in_requests=in_requests, out_invitations=out_invitations, out_requests=out_requests, get_server_short_name=get_server_short_name, user=user)


# ścieżka pozwalająca zapraszać zawodników cd
@app.route('/invitation/<int:user_id>/<int:guest_id>', methods=['GET', 'POST'])
@login_required
def sendinvitation(user_id, guest_id):
    user = User.query.filter_by(id=current_user.id).first_or_404()
    user_teams = []
    user_role_in_team = []
    role_columns = ['toplane', 'jungle', 'midlane', 'bottom', 'support']
    for profile in Profile.query.filter_by(user_id=user.id).all():
        user_teams.extend(ClashTeam.query.filter_by(host_id=profile.id).all())
    inv_guest = Profile.query.filter_by(id=guest_id).first_or_404()
    form = InvitePlayer(user_teams)
    if form.validate_on_submit():
        inv_for_team = ClashTeam.query.filter_by(
            id=form.clashteam.data).first_or_404()
        inv_for_position = getattr(inv_for_team, form.role.data.lower())
        existing_invitation = ClashInvitation.query.join(Profile).filter(
            ClashInvitation.futureteam_id == inv_for_team.id, Profile.user_id == inv_guest.user_id).all()
        existing_request = ClashRequest.query.filter(
            ClashRequest.desired_team_id == inv_for_team.id, ClashRequest.team_host == user.id).all()
        guests_profiles_on_serwer = Profile.query.filter_by(
            user_id=inv_guest.user_id, server=inv_for_team.host.server).all()
        for profile in guests_profiles_on_serwer:
            role_in_team = [role for role in role_columns if getattr(
                inv_for_team, role) == profile.nickname]
            if role_in_team:
                user_role_in_team.extend(role_in_team)
        if inv_for_position is not None:
            flash('This position in your team is already taken', 'error')
            return redirect(url_for('inviteteammates', user_id=user_id, guest_id=guest_id))
        elif len(existing_invitation) > 0:
            flash("You have already sent an invitation to this team for this user's profile.", 'error')
        elif len(existing_request) > 0:
            flash("You have received a request to join this team from this user", 'error')
        elif len(user_role_in_team) > 0:
            flash("This user's profile is already a member of this team", 'error')
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


# ścieżka odpowiedzi na wpływające zaproszenia,
@app.route('/user/<username>/mailbox/invitations/answer', methods=['GET', 'POST'])
@login_required
def inv_answer(username):
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
            join_position = getattr(
                team_to_join, reviewd_invitation.role.lower())
            new_teammember = Profile.query.filter_by(
                id=reviewd_invitation.guestprofile_id).first_or_404()
            if join_position is not None:
                flash('This position is already taken', 'error')
            else:
                setattr(team_to_join, reviewd_invitation.role.lower(), new_teammember.nickname)
                flash('You have joined the team successfully.', 'success')
                db.session.delete(reviewd_invitation)
                db.session.add(team_to_join)
                db.session.commit()
    return redirect(url_for('mailbox', username=user.username))


# ścieżka wycofywania wysłanych zaproszeń,
@app.route('/user/<username>/mailbox/invitations/answer/withdrawal', methods=['GET', 'POST'])
@login_required
def inv_withdrawal(username):
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


# ścieżka wysyłania prośby o dołączenie do drużyny 1/2
@app.route('/jointeam/<int:team_id>', methods=['GET', 'POST'])
@login_required
def jointeam(team_id):
    user = User.query.filter_by(username=current_user.username).first_or_404()
    req_team = ClashTeam.query.filter_by(id=team_id).first_or_404()
    profiles = Profile.query.filter(
        Profile.user_id == user.id, Profile.server == req_team.host.server).all()
    clash_columns = [column.key for column in inspect(ClashTeam).columns]
    none_attrs = [attr for attr in clash_columns if getattr(
        req_team, attr) is None]
    form = RequestForm(roles=none_attrs, profiles=profiles)
    return render_template('jointeam.html', form=form, user=user, req_team=req_team, profiles=profiles)


# ścieżka wysyłania prośby o dołączenie do drużyny 2/2
@app.route('/join/team/<int:team_id>', methods=['GET', 'POST'])
@login_required
def requests(team_id):
    user = User.query.filter_by(username=current_user.username).first_or_404()
    req_team = ClashTeam.query.filter_by(id=team_id).first_or_404()
    profiles = Profile.query.filter(
        Profile.user_id == user.id, Profile.server == req_team.host.server).all()
    clash_columns = [column.key for column in inspect(ClashTeam).columns]
    role_columns = ['toplane', 'jungle', 'midlane', 'bottom', 'support']
    none_attrs = [attr for attr in clash_columns if getattr(req_team, attr) is None]
    user_role_in_team = []
    for profile in profiles:
        role_in_team = [role for role in role_columns if getattr(
            req_team, role) == profile.nickname]
        if role_in_team:
            user_role_in_team.extend(role_in_team)
    form = RequestForm(roles=none_attrs, profiles=profiles)
    if form.validate_on_submit():
        candidate_profile = Profile.query.filter_by(
            id=form.profile.data).first_or_404()
        existing_request = ClashRequest.query.join(Profile).filter(
            ClashRequest.desired_team_id == request.form['req_team_id'], Profile.user_id == candidate_profile.user_id).all()
        existing_invitation = ClashInvitation.query.filter(
            ClashInvitation.futureteam_id == request.form['req_team_id'], ClashInvitation.lider_id == req_team.host.user_id).all()
        if len(existing_request) > 0:
            flash("You have already sent a request to join this team.", 'error')
        elif len(existing_invitation) > 0:
            flash(
                "You have received an invitation from a user to join this team.", 'error')
        elif len(user_role_in_team) > 0:
            flash("You are already a member of this team", 'error')
        else:
            new_req = ClashRequest(
                role=form.role.data,
                desired_team_id=request.form['req_team_id'],
                team_host=request.form['team_host_id'],
                candidate_id=candidate_profile.id)
            db.session.add(new_req)
            db.session.commit()
            flash('Your request has been sent', 'success')
    return redirect(url_for('findteam'))


# ścieżka odpowiedzi na wpływające prośby,
@app.route('/user/<username>/mailbox/requests/answer', methods=['GET', 'POST'])
@login_required
def req_answer(username):
    user = User.query.filter_by(username=username).first_or_404()
    form = AnswerForm()
    if form.validate_on_submit():
        in_req_id = request.form['id_in']
        reviewd_req = ClashRequest.query.filter_by(id=in_req_id).first_or_404()
        team_to_join = ClashTeam.query.filter_by(id=reviewd_req.desired_team_id).first_or_404()
        new_teammember = Profile.query.filter_by(id=reviewd_req.candidate_id).first_or_404()
        
        if form.reject_button.data:
            db.session.delete(reviewd_req)
            db.session.commit()
            flash('The request has been rejected.', 'message')
        
        if form.accept_button.data:
            join_position = getattr(team_to_join, reviewd_req.role.lower())
            
            if join_position is not None:
                flash('This position is already taken', 'error')
            else:
                team_roles = ['Toplane', 'Jungle', 'Midlane', 'Bottom', 'Support']
                role_index = team_roles.index(reviewd_req.role.title())
                setattr(team_to_join, team_roles[role_index].lower(), new_teammember.nickname)

                flash('You have joined the team successfully.', 'success')
                db.session.delete(reviewd_req)
                db.session.add(team_to_join)
                db.session.commit()
    return redirect(url_for('mailbox', username=user.username))


# ścieżka wycofywania wysłanych próśb,
@app.route('/user/<username>/mailbox/requests/answer/withdrawal', methods=['GET', 'POST'])
@login_required
def req_withdrawal(username):
    user = User.query.filter_by(username=username).first_or_404()
    form = AnswerForm()
    if form.validate_on_submit():
        if form.delete_button.data:
            out_req_id = request.form['id_out']
            del_req = ClashRequest.query.filter_by(
                id=out_req_id).first_or_404()
            db.session.delete(del_req)
            db.session.commit()
            flash('Invitation deleted successfully.', 'success')
    return redirect(url_for('mailbox', username=user.username))


# ścieżka pozwalająca wyszukać drużyny
@app.route('/findteam', methods=['GET', 'POST'])
@login_required
def findteam():
    user = User.query.filter_by(username=current_user.username).first_or_404()
    user_profiles = Profile.query.filter_by(user_id=user.id).all()

    user_clashteams = ClashTeam.query.join(Profile).filter(Profile.id == ClashTeam.host_id, Profile.user_id == user.id).all()
    user_profiles_data = {user_profile.nickname: user_profile.server for user_profile in user_profiles}
    guest_teams = []
    for key, value in user_profiles_data.items():
        guest_teams.extend(ClashTeam.query.join(Profile).filter(and_(or_(ClashTeam.toplane == key, ClashTeam.jungle == key, ClashTeam.midlane ==
                           key, ClashTeam.bottom == key, ClashTeam.support == key), Profile.server == value, Profile.user_id != user.id)).all())
    if len(user_clashteams) == 0:
        user_clashteams = []
    all_user_teams = user_clashteams + guest_teams
    all_user_teams_id = [team.id for team in all_user_teams]

    roles = {'Toplane': ClashTeam.toplane, 'Jungle': ClashTeam.jungle,
             'Midlane': ClashTeam.midlane, 'Bottom': ClashTeam.bottom, 'Support': ClashTeam.support}

    clash_teams = ClashTeam.query.filter(or_(*(role == None for role in roles.values())), ClashTeam.id.notin_(all_user_teams_id)).order_by(ClashTeam.clash_date)
    clash_teams_list = clash_teams.all()
    if len(clash_teams_list) == 0:
        clash_teams = []

    form = SearchingTeam(user_id=user.id)
    if form.validate_on_submit():
        if form.division.data == 'None':
            div = ['Iron', 'Bronze', 'Silver', 'Gold', 'Platinum',
                   'Diamond', 'Master', 'Grandmaster', 'Challenger']
        else:
            div = [form.division.data]

        if form.date.data == None:
            start_date = ClashTeam.query.order_by(ClashTeam.clash_date).first().clash_date
            end_date = ClashTeam.query.order_by(ClashTeam.clash_date.desc()).first().clash_date
        else:
            date = form.date.data
            start_date = datetime.combine(date, time.min)
            end_date = datetime.combine(date, time.max)

        role_data = form.role.data.lower()

        if role_data not in {'toplane', 'jungle', 'midlane', 'bottom', 'support'}:
            clash_teams = clash_teams.join(Profile).filter(
                Profile.division.in_(div), ClashTeam.clash_date >= start_date, ClashTeam.clash_date <= end_date).order_by(ClashTeam.clash_date).all()
        else:
            column = getattr(ClashTeam, role_data)
            clash_teams = clash_teams.join(Profile).filter(Profile.division.in_(
                div), column.is_(None), ClashTeam.clash_date >= start_date, ClashTeam.clash_date <= end_date).order_by(ClashTeam.clash_date).all()

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


# ścieżka wylogowywująca użytkownika
@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('index'))


def delete_expired_clashes():
    current_time = datetime.now()
    expired_clashes = ClashTeam.query.filter(
        ClashTeam.clash_date < current_time).all()
    for clash in expired_clashes:
        db.session.delete(clash)
    db.session.commit()


def delete_expired_invitations():
    current_time = datetime.now()
    expired_invitations = ClashInvitation.query.join(
        ClashTeam).filter(ClashTeam.clash_date < current_time).all()
    for invitation in expired_invitations:
        db.session.delete(invitation)
    db.session.commit()


def delete_expired_requests():
    current_time = datetime.now()
    expired_invitations = ClashRequest.query.join(
        ClashTeam).filter(ClashTeam.clash_date < current_time).all()
    for invitation in expired_invitations:
        db.session.delete(invitation)
    db.session.commit()

# scheduler = BackgroundScheduler()
# scheduler.add_job(delete_expired_invitations, 'interval', minutes=1)
# scheduler.add_job(delete_expired_requests, 'interval', minutes=1)
# scheduler.add_job(delete_expired_clashes, 'interval', minutes=1)
# scheduler.start()
