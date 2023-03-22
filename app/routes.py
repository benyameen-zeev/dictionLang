from flask import render_template, redirect, url_for, flash, request, jsonify, abort
from flask_login import login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.urls import url_parse
from app import app, db, login_manager
from app.models import User, TextResource, Vote, WordBank, Word
from app.forms import RegistrationForm, LoginForm, TextResourceForm, FilterLanguageForm
from sqlalchemy.sql import func
import re
from collections import Counter


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

@app.route('/view_text_resource/<int:text_resource_id>', methods=['GET'])
@login_required
def view_text_resource(text_resource_id):
    resource = TextResource.query.get(text_resource_id)

    if not resource:
        flash("Resource not found.", "warning")
        return redirect(url_for('index'))

    word_objects = WordBank.query.filter_by(collection_id=text_resource_id).all()
    words = [{'word': word.word, 'translation': word.translation} for word in word_objects]

    return render_template('view_text_resource.html', resource=resource, words=words)


from flask import jsonify

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

@app.route('/learn/<int:text_resource_id>', methods=['GET'])
@login_required
def learn(text_resource_id):
    resource = TextResource.query.get_or_404(text_resource_id)
    return render_template('learn.html', resource=resource)

from app.models import WordBank


# Remove the add_words_to_word_bank route
@app.route('/generate_vocabulary/<int:text_resource_id>', methods=['GET'])
@login_required
def generate_vocabulary_route(text_resource_id):
    text_resource = TextResource.query.get(text_resource_id)
    print("text_resource:", text_resource)

    if not text_resource.words.all():
        generate_vocabulary(text_resource)

    words = [{'id': word.id, 'word': word.word, 'translation': word.translation, 'language': word.language, 'frequency': word.frequency} for word in text_resource.words]
    print("words:", words)

    return jsonify(words=words)


def generate_vocabulary(text_resource):
    content = text_resource.content.lower()
    words = re.findall(r'\b\w+\b', content)
    word_counts = Counter(words)

    existing_words = {word.word: word for word in text_resource.words}

    for word, frequency in word_counts.items():
        if word not in existing_words:
            new_word = Word(word=word, translation="", language=text_resource.language, frequency=frequency, text_resource_id=text_resource.id)
            db.session.add(new_word)
        else:
            existing_words[word].frequency = frequency

    db.session.commit()

    # Add words to the user's WordBank
    for word in text_resource.words:
        existing_word_bank_entry = WordBank.query.filter_by(word=word.word, user_id=current_user.id).first()
        if not existing_word_bank_entry:
            new_word_bank_entry = WordBank(word=word.word, strength=0, collection_id=text_resource.id, language=text_resource.language)
            new_word_bank_entry.user = current_user
            new_word_bank_entry.collection = text_resource
            db.session.add(new_word_bank_entry)

    db.session.commit()
