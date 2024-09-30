from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

class User(db.Model, UserMixin):
    """User model representing the users of the application."""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    name = db.Column(db.String(150), nullable=False)
    password = db.Column(db.String(256), nullable=False)
    user_type = db.Column(db.String(50), nullable=False)  # e.g., 'master_admin', 'local_admin', 'student'
    institute_id = db.Column(db.Integer, nullable=True)  # Change to Integer if applicable
    voted_poll_ids = db.Column(db.JSON, default=list)  # Store IDs of polls user has voted on

    def __repr__(self):
        return f'<User {self.username}>'

class Option(db.Model):
    """Option model representing the options for each poll."""
    __tablename__ = 'options'

    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(255), nullable=False)
    poll_id = db.Column(db.Integer, db.ForeignKey('polls.id'), nullable=False)

    poll = db.relationship('Poll', backref='options')

    def __repr__(self):
        return f'<Option {self.text}>'

class Poll(db.Model):
    """Poll model representing the polls created in the application."""
    __tablename__ = 'polls'

    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.String(255))
    institute_id = db.Column(db.String, nullable=False)
    institute = db.Column(db.String, nullable=False)
    responses = db.Column(db.JSON, default=dict)  # Store responses as a JSON object

    def __repr__(self):
        return f'<Poll {self.question}>'

    def get_responses(self):
        """Return responses as a dictionary."""
        return self.responses

    def add_response(self, option):
        """Add a response to the poll."""
        responses = self.get_responses()
        responses[option] = responses.get(option, 0) + 1
        self.responses = responses  # Keep it as a dictionary

class Vote(db.Model):
    """Vote model representing the votes cast by users on polls."""
    __tablename__ = 'votes'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    poll_id = db.Column(db.Integer, db.ForeignKey('polls.id'), nullable=False)

    user = db.relationship('User', backref='votes')
    poll = db.relationship('Poll', backref='votes')

    def __repr__(self):
        return f'<Vote user_id={self.user_id}, poll_id={self.poll_id}>'
