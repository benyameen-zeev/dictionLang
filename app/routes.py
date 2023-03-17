from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash

from app import app, db, login_manager
from app.models import User, TextResource
from app.forms import RegistrationForm, LoginForm, TextResourceForm

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    form = RegistrationForm()

    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data, method='sha256')
        user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()

        flash('Registration successful! You can now log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    form = LoginForm()

    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user)
            flash('Login successful!', 'success')

            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('index'))
        else:
            flash('Login failed. Please check your email and password.', 'danger')

    return render_template('login.html', form=form)

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
        text_resource = TextResource(title=form.title.data, content=form.content.data, user_id=current_user.id)
        db.session.add(text_resource)
        db.session.commit()

        flash('Text resource uploaded successfully!', 'success')
        return redirect(url_for('text_resources'))

    return render_template('new_text_resource.html', form=form)

@app.route('/text_resources')
@login_required
def text_resources():
    resources = TextResource.query.filter_by(user_id=current_user.id).all()
    return render_template('text_resources.html', resources=resources)

@app.route('/text_resources/<int:text_resource_id>')
@login_required
def view_text_resource(text_resource_id):
    text_resource = TextResource.query.get_or_404(text_resource_id)
    if text_resource.user_id != current_user.id:
        abort(403)
    return render_template('view_text_resource.html', text_resource=text_resource)

