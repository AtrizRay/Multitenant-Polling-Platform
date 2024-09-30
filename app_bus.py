import os
import json
import webbrowser
from flask import Flask, render_template, redirect, url_for, request, flash
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from data_loader import load_data_from_csv  # Assuming you have a function to load your CSV data
from config import Config
from threading import Timer

# Import models from the models module
from models import db, User, Poll, Institute, Option, Vote   # Ensure Option is imported as well

# Initialize the Flask app
app = Flask(__name__)
app.config.from_object(Config)  # Load configuration

# Initialize extensions
db.init_app(app)
migrate = Migrate(app, db)
login_manager = LoginManager(app)
login_manager.login_view = 'choose_login'

# Data initialization function
def initialize_data():
    global_admin, local_admin_1, local_admin_2, student_data_1, student_data_2, polls_1, polls_2 = load_data_from_csv()

    def add_users_from_dataframe(df):
        for index, row in df.iterrows():
            existing_user = User.query.filter_by(username=row['username']).first()
            if existing_user:
                existing_user.password = row['password']  # Store password as plain text
                existing_user.user_type = row['user_type']
                existing_user.institute_id = row.get('institute_id', None)
            else:
                user = User(
                    username=row['username'], 
                    name=row['username'],
                    password=row['password'],  # Store password as plain text
                    user_type=row['user_type'],
                    institute_id=row.get('institute_id', None)
                )
                db.session.add(user)

def add_polls_from_dataframe(polls_df):
    for index, row in polls_df.iterrows():
        # Initialize responses for options with 0 votes
        responses = {}
        
        # Load options from the options column
        if 'options' in row and row['options']:
            options = row['options'].split(',')  # Split options by comma
            for option_text in options:
                responses[option_text.strip()] = 0  # Initialize vote count for each option
        
        # Check if the poll already exists
        existing_poll = Poll.query.filter_by(question=row['question'], institute_id=row['institute_id']).first()
        if existing_poll:
            print(f"Poll '{row['question']}' already exists. Skipping...")
            continue  # Skip if the poll already exists

        # Create the new poll since it doesn't exist
        new_poll = Poll(
            question=row['question'],
            institute_id=row['institute_id'],
            responses=json.dumps(responses)  # Store the initialized responses as JSON
        )
        db.session.add(new_poll)
        db.session.flush()  # Flush to get the poll ID

        # Add the options to the poll
        for option_text in options:
            option = Option(text=option_text.strip(), poll_id=new_poll.id)
            db.session.add(option)

    db.session.commit()


    # Add users and polls
    add_users_from_dataframe(global_admin)
    add_users_from_dataframe(local_admin_1)
    add_users_from_dataframe(local_admin_2)
    add_users_from_dataframe(student_data_1)
    add_users_from_dataframe(student_data_2)
    add_polls_from_dataframe(polls_1)
    add_polls_from_dataframe(polls_2)

    db.session.commit()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Route for selecting login type (student/admin)
@app.route('/choose_login', methods=['GET'])
def choose_login():
    return render_template('login.html')  # Assuming you have this template

# Add the admin_dashboard route
@app.route('/admin_dashboard')
@login_required
def admin_dashboard():
    if current_user.user_type != 'master_admin':
        return redirect(url_for('landing'))
    # Logic to fetch data for the dashboard
    return render_template('admin.html') 

@app.route('/login/admin', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.user_type == 'master_admin' and user.password == password:  # Compare plain text
            login_user(user)
            return redirect(url_for('master_admin_dashboard'))
        else:
            flash('Invalid admin credentials')
    return render_template('login.html', login_type='admin')

@app.route('/login/local_admin', methods=['GET', 'POST'])
def local_admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.user_type == 'local_admin' and user.password == password:  # Compare plain text
            login_user(user)
            return redirect(url_for('local_admin_dashboard'))
        else:
            flash('Invalid local admin credentials')
    return render_template('login.html', login_type='local_admin')

@app.route('/login/student', methods=['GET', 'POST'])
def student_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.user_type == 'student' and user.password == password:  # Compare plain text
            login_user(user)
            return redirect(url_for('landing'))
        else:
            flash('Invalid student credentials')
    return render_template('login.html', login_type='student')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('choose_login'))

@app.route('/master_admin_dashboard')
@login_required
def master_admin_dashboard():
    if current_user.user_type != 'master_admin':
        return redirect(url_for('landing'))
    polls = Poll.query.all()
    users = User.query.all()
    return render_template('admin.html', admin_type='master', polls=polls, users=users)

@app.route('/local_admin_dashboard')
@login_required
def local_admin_dashboard():
    if current_user.user_type != 'local_admin':
        return redirect(url_for('landing'))
    polls = Poll.query.filter_by(institute_id=current_user.institute_id).all()
    return render_template('admin.html', admin_type='local', polls=polls)

@app.route('/landing')
@login_required
def landing():
    polls = Poll.query.all()  # Get all polls
    options = {poll.id: poll.options for poll in polls}  # Create a dictionary of options by poll ID
    return render_template('landing.html', polls=polls, options=options)

@app.route('/vote/<int:poll_id>', methods=['POST'])
@login_required
def vote(poll_id):
    poll = Poll.query.get_or_404(poll_id)
    
    # Check if the current user has already voted on this poll
    existing_vote = Vote.query.filter_by(user_id=current_user.id, poll_id=poll_id).first()
    
    if existing_vote:
        flash('You have already voted on this poll.', 'warning')
        return redirect(url_for('landing'))

    # Get the selected option from the form
    selected_option_id = request.form.get('option')
    if not selected_option_id:
        flash('No option selected. Please select an option to vote.', 'danger')
        return redirect(url_for('landing'))

    # Record the user's vote
    vote = Vote(user_id=current_user.id, poll_id=poll_id, option_id=selected_option_id)
    db.session.add(vote)
    db.session.commit()

    flash('Your vote has been recorded. Thank you!', 'success')
    return redirect(url_for('landing'))


@app.route('/results')
@login_required
def results():
    if current_user.user_type in ['master_admin', 'local_admin']:
        if current_user.user_type == 'master_admin':
            all_polls = Poll.query.all()
            return render_template('results.html', polls=all_polls)
        else:
            all_polls = Poll.query.filter_by(institute_id=current_user.institute_id).all()
            return render_template('results.html', polls=all_polls)

    # Ensure the user is redirected to their respective dashboard
    if current_user.user_type == 'master_admin':
        return redirect(url_for('master_admin_dashboard'))
    elif current_user.user_type == 'local_admin':
        return redirect(url_for('local_admin_dashboard'))

    return redirect(url_for('landing'))

# Function to open the browser
def open_browser():
    chrome_path = 'C:/Program Files/Google/Chrome/Application/chrome.exe %s'  # Path to Chrome in Windows
    webbrowser.get(chrome_path).open_new("http://127.0.0.1:5000/choose_login")

# Main entry point
if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Create database tables
        initialize_data()  # Initialize data from CSVs
    Timer(1, open_browser).start()  # Open Chrome after 1 second
    app.run(debug=True)
