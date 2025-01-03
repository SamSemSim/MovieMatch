from app import db
from sqlalchemy import text

def upgrade():
    # Add new columns to user table one by one (SQLite limitation)
    with db.engine.connect() as conn:
        # Add profile_picture column
        conn.execute(text("ALTER TABLE user ADD COLUMN profile_picture VARCHAR(500) DEFAULT 'default-avatar.png'"))
        # Add bio column
        conn.execute(text("ALTER TABLE user ADD COLUMN bio TEXT DEFAULT ''"))
        # Add location column
        conn.execute(text("ALTER TABLE user ADD COLUMN location VARCHAR(100) DEFAULT ''"))
        # Add favorite_movie column
        conn.execute(text("ALTER TABLE user ADD COLUMN favorite_movie VARCHAR(200) DEFAULT ''"))
        # Add favorite_tv_show column
        conn.execute(text("ALTER TABLE user ADD COLUMN favorite_tv_show VARCHAR(200) DEFAULT ''"))
        conn.commit()

def downgrade():
    # SQLite doesn't support dropping columns, so we need to recreate the table
    # This is just a placeholder as SQLite requires complex table recreation to remove columns
    pass 