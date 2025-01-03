from app import db
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from flask_login import UserMixin
import os
from flask import url_for

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    profile_picture = db.Column(db.String(500), default='default-avatar.png')
    bio = db.Column(db.Text, default='')
    location = db.Column(db.String(100), default='')
    favorite_movie = db.Column(db.String(200), default='')
    favorite_tv_show = db.Column(db.String(200), default='')
    ratings = db.relationship('UserPreference', 
                            backref=db.backref('rater', lazy=True),
                            lazy='dynamic',
                            order_by='desc(UserPreference.created_at)',
                            overlaps="user")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_ratings_count(self):
        return self.ratings.count()

    def get_profile_picture_url(self):
        if not self.profile_picture or not os.path.exists(os.path.join('static/images/profile', self.profile_picture)):
            return url_for('static', filename='images/default-avatar.png')
        return url_for('static', filename=f'images/profile/{self.profile_picture}')

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'created_at': self.created_at.isoformat(),
            'profile_picture': self.get_profile_picture_url(),
            'bio': self.bio,
            'location': self.location,
            'favorite_movie': self.favorite_movie,
            'favorite_tv_show': self.favorite_tv_show
        } 