import os
from datetime import timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    # Security
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-default-secret-key-change-in-production'
    CSRF_ENABLED = True
    
    # Session Configuration
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    
    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///moviematch.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # API Keys
    TMDB_API_KEY = os.environ.get('TMDB_API_KEY')
    
    # Cache Configuration
    SEND_FILE_MAX_AGE_DEFAULT = 31536000  # 1 year in seconds

class DevelopmentConfig(Config):
    DEBUG = True
    SESSION_COOKIE_SECURE = False  # Allow HTTP in development

class ProductionConfig(Config):
    DEBUG = False
    # Add any production-specific settings here

# Create config dictionary
config_dict = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

# Function to get config
def get_config(env_name='development'):
    return config_dict.get(env_name, config_dict['default']) 