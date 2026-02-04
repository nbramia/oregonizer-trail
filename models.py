# models.py

from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
import bcrypt
import json

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(128), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=True)  # Password can be nullable for OAuth users
    high_score = db.Column(db.Integer, default=0)
    games_played = db.Column(db.Integer, default=0)
    games_started = db.Column(db.Integer, default=0)
    last_game_played = db.Column(db.DateTime, default=None)

    def __repr__(self):
        return f'<User {self.email}>'

    @staticmethod
    def get_or_create(user_info):
        email = user_info['email']
        user = User.query.filter_by(email=email).first()
        if not user:
            user = User(
                email=email,
                password=bcrypt.hashpw(user_info['sub'].encode(), bcrypt.gensalt()).decode()  # Hash Google user ID as password
            )
            db.session.add(user)
            db.session.commit()
        return user

class Scenario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), unique=True, nullable=False)
    mode = db.Column(db.String(128), nullable=False)
    type = db.Column(db.String(128), nullable=False)  # 'decision' or 'informational'
    text = db.Column(db.Text, nullable=False)
    metrics = db.Column(db.Text, nullable=False)  # Store metrics as JSON string
    response = db.Column(db.Text, nullable=True)  # Only for decision scenarios, store responses as JSON string
    community = db.Column(db.Boolean, default=False)
    
    def __repr__(self):
        return f'<Scenario {self.name}>'

