from flask import Blueprint, render_template, request, flash, redirect, url_for
from .models import User
from . import db #comes from init.py file
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, login_required, logout_user, current_user


auth = Blueprint('auth', __name__)

# login, logout, sign-up

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first() # how to search the database for a specific thing, here looking for users w this email (should be 1 here since email must be unique in signup)
        print(username, password, user.username, user.password)
        if user:
            if check_password_hash(user.password, password):
                flash('Logged in successfully!', category='success')
                login_user(user, remember=True) # all we need to do to login the user, stores in the flask web session(the remember true variable)
                return redirect(url_for('views.home'))
            else:
                flash('Incorrect username or password.', category='error')
        else:
            flash('Incorrect username or password.', category='error')

    return render_template('login.html', user=current_user)

@auth.route('/logout')
@login_required # cant access this root unless user is logged in
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

@auth.route('/sign-up', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        password1 = request.form.get('password1')
        password2 = request.form.get('password2')
        
            # validation + message-flashing (flask functionality) on screen if something is wrong
        user = User.query.filter_by(username=username).first()
        if user:
            flash('Username already exists', category='error')
        elif len(username) < 4:
            flash('Username must be greater than 3 characters', category='error')
        elif len(username) < 2:
            flash('Username must be greater than 1 character', category='error')
        elif password1 != password2:
            flash('Your passwords don\'t match idiot lmao', category='error')
        elif len(password1) < 2:
            flash('Password must be greater than 1 character', category='error')
        else: # add user to database
            new_user = User(username=username, password=generate_password_hash(password1, method='pbkdf2:sha256', salt_length=16))
            db.session.add(new_user)
            db.session.commit()

            flash('Account Created', category='success')
            return redirect(url_for('views.home')) # redirects to the views.py home() function >> way to make it so if i ever want to change home url function, can just change the root (in views.py)

    return render_template('signup.html', user=current_user)