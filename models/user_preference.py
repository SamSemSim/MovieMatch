from datetime import datetime
from services.firebase_service import FirebaseService

firebase_service = FirebaseService()

class UserPreference:
    def __init__(self, username, tmdb_id, media_type, rating, title=None, created_at=None, updated_at=None, **kwargs):
        self.username = username
        self.tmdb_id = tmdb_id
        self.media_type = media_type
        self.rating = rating
        self.title = title
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or self.created_at

    @staticmethod
    def create(username, tmdb_id, media_type, rating, title=None):
        """Create a new user preference"""
        now = datetime.utcnow()
        pref_data = {
            'username': username,
            'tmdb_id': tmdb_id,
            'media_type': media_type,
            'rating': rating,
            'title': title,
            'created_at': now,
            'updated_at': now
        }
        firebase_service.add_user_preference(username, pref_data)
        return UserPreference(**pref_data)

    @staticmethod
    def get_user_preferences(username):
        """Get all preferences for a user"""
        prefs = firebase_service.get_user_preferences(username)
        return [UserPreference(**pref) for pref in prefs]

    def to_dict(self):
        """Convert preference to dictionary"""
        return {
            'username': self.username,
            'tmdb_id': self.tmdb_id,
            'media_type': self.media_type,
            'rating': self.rating,
            'title': self.title,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        } 