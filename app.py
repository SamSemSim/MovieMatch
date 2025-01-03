from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
import os
from dotenv import load_dotenv
from datetime import datetime
from config import setup_logging, init_cache

# Load environment variables
load_dotenv()

# Create Flask app with configuration
app = Flask(__name__)

# Ensure instance directory exists with proper permissions
instance_path = os.path.join(app.root_path, 'instance')
os.makedirs(instance_path, exist_ok=True)
os.chmod(instance_path, 0o777)  # Give full permissions to the instance directory

# Load configuration
class Config:
    # Basic Flask configuration
    DEBUG = os.environ.get('FLASK_ENV') != 'production'  # Debug mode if not in production
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-please-change'
    
    # Database configuration
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or f'sqlite:///{os.path.join(instance_path, "moviematch.db")}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # API Keys
    TMDB_API_KEY = os.environ.get('TMDB_API_KEY')
    
    # Security configurations
    SESSION_COOKIE_SECURE = os.environ.get('FLASK_ENV') == 'production'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Cache configuration
    CACHE_TYPE = 'simple'
    CACHE_DEFAULT_TIMEOUT = 300

app.config.from_object(Config)

# Set up logging
setup_logging(app)

# Initialize cache
cache = init_cache(app)

# Additional security headers
@app.after_request
def add_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; img-src 'self' https://image.tmdb.org data:; font-src 'self' https://cdnjs.cloudflare.com; frame-src 'self' https://www.youtube.com;"
    return response

# Initialize database
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Create tables if they don't exist
with app.app_context():
    try:
        db.create_all()
        app.logger.info("Database tables created successfully")
    except Exception as e:
        app.logger.error(f"Error creating database tables: {str(e)}")

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    from models.user import User
    return User.query.get(int(user_id))

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    app.logger.error(f'Page not found: {request.url}')
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    app.logger.error(f'Server Error: {error}')
    return render_template('errors/500.html'), 500

# Add datetime filter
@app.template_filter('datetime')
def format_datetime(value):
    if isinstance(value, str):
        try:
            value = datetime.fromisoformat(value.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            return value
    return value.strftime('%B %d, %Y at %I:%M %p')

# Import routes after db initialization to avoid circular imports
from routes.main_routes import *
from routes.auth_routes import *

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000))) 