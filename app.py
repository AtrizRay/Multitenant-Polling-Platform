import os
import json
import webbrowser
import argparse
import pandas as pd
from flask import Flask, render_template, redirect, url_for, request, flash, jsonify
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from config import Config
from flask_login import current_user
from models import db, User, Poll, Vote  # Ensure the Vote model is imported
from collections.abc import MutableMapping
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)

# Initialize the Flask app
app = Flask(__name__)
app.config.from_object(Config)  # Load configuration

# Initialize extensions
db.init_app(app)
migrate = Migrate(app, db)
login_manager = LoginManager(app)
login_manager.login_view = 'choose_login'

def load_data_from_csv():
    """Load data from CSV files."""
    csv_path = r'D:\IIT jodhpur\SDE Mini Project\polling_platform\Database'
    try:
        global_admin = pd.read_csv(os.path.join(csv_path, 'global_admin.csv'))
        local_admin_1 = pd.read_csv(os.path.join(csv_path, 'local_admin_institute_1.csv'))
        local_admin_2 = pd.read_csv(os.path.join(csv_path, 'local_admin_institute_2.csv'))
        student_data_1 = pd.read_csv(os.path.join(csv_path, 'student_data_institute_1.csv'))
        student_data_2 = pd.read_csv(os.path.join(csv_path, 'student_data_institute_2.csv'))
        polls_1 = pd.read_csv(os.path.join(csv_path, 'polls_institute_1.csv'))
        polls_2 = pd.read_csv(os.path.join(csv_path, 'polls_institute_2.csv'))
        logging.info("CSV files loaded successfully.")
        return global_admin, local_admin_1, local_admin_2, student_data_1, student_data_2, polls_1, polls_2
    except Exception as e:
        logging.error("Error loading CSV files: %s", e)
        return None

def initialize_data():
    """Initialize data in the database from CSV files."""
    data = load_data_from_csv()
    if data is None:
        return

    global_admin, local_admin_1, local_admin_2, student_data_1, student_data_2, polls_1, polls_2 = data

    # Add users and polls
    for df in [global_admin, local_admin_1, local_admin_2, student_data_1, student_data_2]:
        add_users_from_dataframe(df)
    for polls_df in [polls_1, polls_2]:
        add_polls_from_dataframe(polls_df)

    db.session.commit()

def add_users_from_dataframe(df):
    """Add users from a DataFrame to the database."""
    for index, row in df.iterrows():
        logging.debug("Processing user: %s", row.to_dict())
        existing_user = User.query.filter_by(username=row['username']).first()
        
        if existing_user:
            existing_user.password = generate_password_hash(row['password'], method='pbkdf2:sha256')
            existing_user.user_type = row['user_type']
            existing_user.institute_id = str(row.get('institute_id', ''))  # Ensure institute_id is stored as string
            logging.debug("User %s updated.", row['username'])
        else:
            user = User(
                username=row['username'],
                name=row.get('name', row['username']),
                password=generate_password_hash(row['password'], method='pbkdf2:sha256'),
                user_type=row['user_type'],
                institute_id=str(row.get('institute_id', ''))  # Ensure institute_id is stored as string
            )
            db.session.add(user)
            logging.debug("User %s added.", row['username'])

def add_polls_from_dataframe(polls_df):
    """Add polls from a DataFrame to the database."""
    for index, row in polls_df.iterrows():
        existing_poll = Poll.query.filter_by(question=row['question'], institute_id=str(row['institute_id'])).first()
        if not existing_poll:
            # Split the options by commas and strip whitespace
            options = [option.strip() for option in row['options'].split(',')]
            new_poll = Poll(
                question=row['question'],
                options=json.dumps(options),  # Store options as JSON string
                institute_id=str(row['institute_id']),
                institute=row['institute'],
                responses={}  # Initialize with an empty dictionary
            )
            db.session.add(new_poll)
            logging.debug("Poll %s added.", row['question'])

@login_manager.user_loader
def load_user(user_id):
    """Load a user by ID."""
    return db.session.get(User, int(user_id))

@app.route('/')
def home():
    """Home page route.""" 
    return redirect(url_for('choose_login'))

@app.route('/choose_login', methods=['GET'])
def choose_login():
    """Route for selecting login type (student/admin)."""
    return render_template('login.html')

def login_user_by_type(user_type, redirect_view):
    """Generic user login logic."""
    username = request.form['username']
    password = request.form['password']
    user = User.query.filter_by(username=username).first()
    
    if user and user.user_type == user_type and check_password_hash(user.password, password):
        login_user(user)
        return redirect(url_for(redirect_view))
    else:
        flash('Invalid credentials')
    return render_template('login.html', login_type=user_type)

@app.route('/login/admin', methods=['GET', 'POST'])
def admin_login():
    """Admin login route.""" 
    if request.method == 'POST':
        return login_user_by_type('master_admin', 'master_admin_dashboard')
    return render_template('login.html', login_type='admin')

@app.route('/login/local_admin', methods=['GET', 'POST'])
def local_admin_login():
    """Local admin login route."""
    if request.method == 'POST':
        return login_user_by_type('local_admin', 'local_admin_dashboard')
    return render_template('login.html', login_type='local_admin')

@app.route('/login/student', methods=['GET', 'POST'])
def student_login():
    """Student login route."""
    if request.method == 'POST':
        return login_user_by_type('student', 'landing')
    return render_template('login.html', login_type='student')

@app.route('/logout')
@login_required
def logout():
    """Logout the current user."""
    logout_user()
    return redirect(url_for('landing'))

@app.route('/admin_dashboard')
@login_required
def admin_dashboard():
    """Admin dashboard route."""
    if current_user.user_type == 'master_admin':
        return redirect(url_for('master_admin_dashboard'))
    elif current_user.user_type == 'local_admin':
        return redirect(url_for('local_admin_dashboard'))
    else:
        return redirect(url_for('landing'))

@app.route('/master_admin_dashboard')
@login_required
def master_admin_dashboard():
    """Master admin dashboard route.""" 
    if current_user.user_type != 'master_admin':
        return redirect(url_for('landing'))
    polls = Poll.query.all()
    users = User.query.all()
    options = {poll.id: poll.responses for poll in polls}
    return render_template('admin.html', admin_type='master', polls=polls, users=users, options=options)

@app.route('/local_admin_dashboard')
@login_required
def local_admin_dashboard():
    """Local admin dashboard route.""" 
    if current_user.user_type != 'local_admin':
        return redirect(url_for('landing'))
    polls = Poll.query.filter_by(institute_id=current_user.institute_id).all()
    options = {poll.id: poll.responses for poll in polls}
    return render_template('admin.html', admin_type='local', polls=polls, options=options)

def get_current_poll():
    """Fetch the current active poll.""" 
    current_poll = Poll.query.filter_by(active=True).first()  # Adjust this logic based on how you define 'current'
    return current_poll if current_poll else None

@app.route('/results', methods=['GET'])
@login_required
def results():
    poll = get_current_poll()  # Fetch the current poll
    
    if not poll:
        return jsonify({'error': 'No current poll found.'}), 404

    # Convert MutableDict to JSON string if necessary
    responses_data = poll.responses
    if isinstance(responses_data, MutableMapping):
        responses_data = json.dumps(responses_data)  # Convert to JSON string

    try:
        responses = json.loads(responses_data)  # Now this should work
    except json.JSONDecodeError as e:
        app.logger.error("JSON decode error: %s", str(e))
        return jsonify({'error': 'Invalid responses format.'}), 400

    # Continue with your existing logic
    return render_template('results.html', responses=responses)

@app.route('/landing')
@login_required
def landing():
    """Landing page for students after logging in."""
    institute_id = current_user.institute_id

    # Fetch all polls for the user's institute
    all_polls = Poll.query.filter_by(institute_id=institute_id).all()

    # Separate unvoted and voted polls
    unvoted_polls = []
    voted_polls = []

    for poll in all_polls:
        if str(current_user.id) not in poll.responses:  # User has not voted
            unvoted_polls.append(poll)
        else:  # User has voted
            voted_polls.append(poll)

    return render_template('landing.html', unvoted_polls=unvoted_polls, voted_polls=voted_polls)



@app.route('/vote/<int:poll_id>', methods=['POST'])
@login_required
def vote(poll_id):
    """Vote on a poll."""
    poll = Poll.query.get(poll_id)
    
    if not poll:
        flash('Poll not found')
        return redirect(url_for('landing'))

    option = request.form.get('option')
    
    if not option:
        flash('No option selected')
        return redirect(url_for('landing'))

    # Check if the user has already voted
    if str(current_user.id) in poll.responses:
        flash('You have already voted on this poll')
        return redirect(url_for('landing'))

    # Store the vote
    poll.responses[str(current_user.id)] = option
    db.session.commit()
    flash('Thank you for voting!')
    return redirect(url_for('landing'))

if __name__ == '__main__':
    # Set up argument parsing
    parser = argparse.ArgumentParser(description='Run the Flask application.')
    parser.add_argument('--port', type=int, default=5000, help='Port to run the Flask app on.')
    parser.add_argument('--tenant', type=str, default='default', help='Tenant identifier.')
    args = parser.parse_args()

    # Initialize the database with CSV data inside the application context
    with app.app_context():
        initialize_data()
    
    # Automatically open the app in Chrome
    webbrowser.open_new(f'http://127.0.0.1:{args.port}')
    
    # Run the app
    app.run(port=args.port)
