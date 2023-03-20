from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.urls import url_parse
from app import app, db, login_manager
from app.models import User, TextResource, Vote
from app.forms import RegistrationForm, LoginForm, TextResourceForm, FilterLanguageForm
from sqlalchemy.sql import func


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('text_resources'))

    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data)
        user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()

        flash(f'Account created for {form.username.data}! You are now able to log in', 'success')
        return redirect(url_for('login'))

    return render_template('register.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).one_or_none()
        if user is not None and check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember_me.data)
            next_page = request.args.get('next')
            if not next_page or url_parse(next_page).netloc != '':
                next_page = url_for('index')
            return redirect(next_page)
        else:
            flash('Invalid email or password')
            return redirect(url_for('login'))
    return render_template('login.html', title='Sign In', form=form)



@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

@app.route('/text_resources/new', methods=['GET', 'POST'])
@login_required
def new_text_resource():
    form = TextResourceForm()

    if form.validate_on_submit():
        text_resource = TextResource(title=form.title.data, content=form.content.data, user_id=current_user.id, language=form.language_choice.data)
        db.session.add(text_resource)
        db.session.commit()

        flash('Text resource uploaded successfully!', 'success')
        return redirect(url_for('text_resources'))
    else:
        print(form.errors)

    return render_template('new_text_resource.html', form=form)



@app.route('/text_resources', methods=['GET', 'POST'])
def text_resources():
    filter_form = FilterLanguageForm()
    language_filter = 'all'

    if filter_form.validate_on_submit():
        language_filter = filter_form.language.data

    query = db.session.query(TextResource, func.sum(Vote.vote_value).label('vote_sum')) \
        .outerjoin(Vote, TextResource.id == Vote.text_resource_id) \
        .group_by(TextResource.id) \
        .order_by(TextResource.id.desc())

    if language_filter != 'all':
        query = query.filter(TextResource.language == language_filter)

    resources = query.all()

    return render_template('text_resources.html', resources=resources, filter_form=filter_form)

@app.route('/text_resources/<int:text_resource_id>')
@login_required
def view_text_resource(text_resource_id):
    text_resource = TextResource.query.get_or_404(text_resource_id)
    if text_resource.user_id != current_user.id:
        abort(403)
    return render_template('view_text_resource.html', text_resource=text_resource)

from flask import jsonify

# ...

@app.route('/text_resources/vote/<int:text_resource_id>/<int:vote_value>', methods=['POST'])
@login_required
def vote_text_resource(text_resource_id, vote_value):
    text_resource = TextResource.query.get(text_resource_id)
    if not text_resource:
        return jsonify(error="Text resource not found."), 404

    vote = Vote.query.filter_by(user_id=current_user.id, text_resource_id=text_resource_id).first()

    if vote:
        # Update the existing vote
        vote.vote_value = vote_value
    else:
        # Create a new vote
        vote = Vote(user_id=current_user.id, text_resource_id=text_resource_id, vote_value=vote_value)
        db.session.add(vote)

    db.session.commit()

    vote_sum = db.session.query(func.sum(Vote.vote_value)).filter(Vote.text_resource_id == text_resource_id).scalar()

    return jsonify(vote_sum=vote_sum if vote_sum else 0)


@app.route('/my_collections')
@login_required
def my_collections():
    resources = TextResource.query.filter_by(user_id=current_user.id).order_by(TextResource.id.desc()).all()
    return render_template('my_collections.html', resources=resources)
