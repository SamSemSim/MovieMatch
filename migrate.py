from app import app, db
from migrations.add_profile_fields import upgrade

if __name__ == '__main__':
    print("Running database migration...")
    with app.app_context():
        upgrade()
    print("Migration completed successfully!") 