from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import os
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Database configuration
if os.environ.get('DATABASE_URL'):
    # Use PostgreSQL in production
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL').replace('postgres://', 'postgresql://')
else:
    # Use SQLite in development
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///movies.db'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-here')

# Initialize database
db = SQLAlchemy(app)
migrate = Migrate(app, db)

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

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000))) 