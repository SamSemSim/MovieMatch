import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
import os
import json

def init_firebase():
    """Initialize Firebase Admin SDK"""
    try:
        # Check if already initialized
        firebase_admin.get_app()
    except ValueError:
        # Initialize with credentials
        if os.environ.get('FIREBASE_CREDENTIALS'):
            # For production: use environment variable
            cred_dict = json.loads(os.environ.get('FIREBASE_CREDENTIALS'))
            cred = credentials.Certificate(cred_dict)
        else:
            # For development: use local file
            cred = credentials.Certificate('firebase-credentials.json')
        
        firebase_admin.initialize_app(cred)
    
    return firestore.client()

class FirebaseService:
    def __init__(self):
        self.db = init_firebase()
    
    def create_user(self, user_data):
        """Create a new user document"""
        user_ref = self.db.collection('users').document(user_data['username'])
        user_data['created_at'] = datetime.utcnow()
        user_ref.set(user_data)
        return user_data
    
    def get_user_by_username(self, username):
        """Get user by username"""
        user_ref = self.db.collection('users').document(username)
        user = user_ref.get()
        return user.to_dict() if user.exists else None
    
    def get_user_by_id(self, user_id):
        """Get user by ID"""
        users = self.db.collection('users').where('id', '==', user_id).limit(1).get()
        return users[0].to_dict() if users else None
    
    def update_user(self, username, update_data):
        """Update user data"""
        user_ref = self.db.collection('users').document(username)
        user_ref.update(update_data)
        
    def add_user_preference(self, username, preference_data):
        """Add or update user preference"""
        pref_ref = self.db.collection('users').document(username).collection('preferences').document(str(preference_data['tmdb_id']))
        preference_data['updated_at'] = datetime.utcnow()
        pref_ref.set(preference_data, merge=True)
        
    def get_user_preferences(self, username):
        """Get all preferences for a user"""
        prefs = self.db.collection('users').document(username).collection('preferences').get()
        return [pref.to_dict() for pref in prefs] 