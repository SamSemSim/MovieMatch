from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from services.firebase_service import FirebaseService
from flask import url_for
import os

firebase_service = FirebaseService()

class User(UserMixin):
    def __init__(self, username, email, password_hash=None, id=None, **kwargs):
        self.username = username
        self.email = email
        self.password_hash = password_hash
        self.id = id or username  # Use username as ID if not provided
        self.profile_picture = kwargs.get('profile_picture', 'default-avatar.png')
        self.bio = kwargs.get('bio', '')
        self.location = kwargs.get('location', '')
        self.favorite_movie = kwargs.get('favorite_movie', '')
        self.favorite_tv_show = kwargs.get('favorite_tv_show', '')
        self.created_at = kwargs.get('created_at')

    @property
    def profile_picture_url(self):
        """Get profile picture URL"""
        if not self.profile_picture or self.profile_picture == 'default-avatar.png':
            return url_for('static', filename='images/default-avatar.png')
        return url_for('static', filename=f'images/profile/{self.profile_picture}')

    @staticmethod
    def create(username, email, password):
        """Create a new user"""
        user_data = {
            'username': username,
            'email': email,
            'password_hash': generate_password_hash(password),
            'id': username,
            'profile_picture': 'default-avatar.png',
            'bio': '',
            'location': '',
            'favorite_movie': '',
            'favorite_tv_show': ''
        }
        firebase_service.create_user(user_data)
        return User(**user_data)

    @staticmethod
    def get_by_username(username):
        """Get user by username"""
        user_data = firebase_service.get_user_by_username(username)
        return User(**user_data) if user_data else None

    @staticmethod
    def get_by_id(user_id):
        """Get user by ID"""
        user_data = firebase_service.get_user_by_id(user_id)
        return User(**user_data) if user_data else None

    def check_password(self, password):
        """Check password"""
        return check_password_hash(self.password_hash, password)

    def update_profile(self, update_data):
        """Update user profile"""
        firebase_service.update_user(self.username, update_data)
        for key, value in update_data.items():
            setattr(self, key, value)

    def to_dict(self):
        """Convert user object to dictionary"""
        return {
            'username': self.username,
            'email': self.email,
            'id': self.id,
            'profile_picture': self.profile_picture,
            'profile_picture_url': self.profile_picture_url,
            'bio': self.bio,
            'location': self.location,
            'favorite_movie': self.favorite_movie,
            'favorite_tv_show': self.favorite_tv_show,
            'created_at': self.created_at
        } 