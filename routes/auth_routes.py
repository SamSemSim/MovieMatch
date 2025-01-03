from flask import render_template, request, redirect, url_for, flash, jsonify, current_app
from app import app, db
from models.user import User
from flask_login import login_user, logout_user, login_required, current_user
import os
from werkzeug.utils import secure_filename
from PIL import Image
import secrets

def save_picture(picture_file):
    # Check if the file is one of the allowed types/extensions
    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
    if not ('.' in picture_file.filename and picture_file.filename.rsplit('.', 1)[1].lower() in allowed_extensions):
        return None
        
    # Generate unique filename
    random_hex = secrets.token_hex(8)
    _, file_extension = os.path.splitext(picture_file.filename)
    filename = random_hex + file_extension
    
    # Create directory if it doesn't exist
    picture_dir = os.path.join(current_app.root_path, 'static/images/profile')
    os.makedirs(picture_dir, exist_ok=True)
    
    picture_path = os.path.join(picture_dir, filename)
    
    try:
        # Resize image
        output_size = (400, 400)
        i = Image.open(picture_file)
        i.thumbnail(output_size)
        i.save(picture_path)
        return filename
    except Exception as e:
        print(f"Error saving image: {e}")
        return None

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        username = data.get('username')
        password = data.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            next_page = request.args.get('next')
            
            if request.is_json:
                return jsonify({'success': True, 'redirect': next_page or url_for('home')})
            return redirect(next_page or url_for('home'))
        
        if request.is_json:
            return jsonify({'success': False, 'error': 'Invalid username or password'}), 401
        flash('Invalid username or password', 'error')
        
    return render_template('auth/login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        confirm_password = data.get('confirm_password')
        
        if password != confirm_password:
            if request.is_json:
                return jsonify({'success': False, 'error': 'Passwords do not match'}), 400
            flash('Passwords do not match', 'error')
            return redirect(url_for('register'))
        
        if User.query.filter_by(username=username).first():
            if request.is_json:
                return jsonify({'success': False, 'error': 'Username already exists'}), 400
            flash('Username already exists', 'error')
            return redirect(url_for('register'))
            
        if User.query.filter_by(email=email).first():
            if request.is_json:
                return jsonify({'success': False, 'error': 'Email already registered'}), 400
            flash('Email already registered', 'error')
            return redirect(url_for('register'))
        
        user = User(username=username, email=email)
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        login_user(user)
        
        if request.is_json:
            return jsonify({'success': True, 'redirect': url_for('home')})
        return redirect(url_for('home'))
        
    return render_template('auth/register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/profile')
@login_required
def profile():
    # Get all ratings
    ratings = current_user.ratings.all()
    
    # Calculate average rating
    avg_rating = sum(float(r.rating) for r in ratings) / len(ratings) if ratings else 0
    
    # Get recent activity (last 10 ratings)
    recent_activity = ratings[:10] if ratings else []
    
    # Get favorite genres
    genre_counts = {}
    for rating in ratings:
        if rating.genres:
            for genre in rating.genres.split(','):
                genre = genre.strip()
                if genre:  # Only count non-empty genres
                    genre_counts[genre] = genre_counts.get(genre, 0) + 1
    
    favorite_genres = sorted(genre_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    
    return render_template('auth/profile.html', 
                         user=current_user,
                         avg_rating=avg_rating,
                         recent_activity=recent_activity,
                         favorite_genres=favorite_genres) 

@app.route('/update_profile', methods=['POST'])
@login_required
def update_profile():
    if request.method == 'POST':
        current_user.bio = request.form.get('bio', '')
        current_user.location = request.form.get('location', '')
        current_user.favorite_movie = request.form.get('favorite_movie', '')
        current_user.favorite_tv_show = request.form.get('favorite_tv_show', '')
        
        db.session.commit()
        return jsonify({'success': True})
    
    return jsonify({'success': False})

@app.route('/update_profile_picture', methods=['POST'])
@login_required
def update_profile_picture():
    if 'profile_picture' not in request.files:
        return jsonify({'success': False, 'error': 'No file uploaded'})
    
    picture_file = request.files['profile_picture']
    if picture_file.filename == '':
        return jsonify({'success': False, 'error': 'No file selected'})
    
    try:
        # Save new picture
        picture_filename = save_picture(picture_file)
        if not picture_filename:
            return jsonify({'success': False, 'error': 'Invalid file type. Please upload a valid image file (PNG, JPG, JPEG, GIF).'})
        
        # Delete old profile picture if it's not the default
        if current_user.profile_picture != 'default-avatar.png':
            old_picture_path = os.path.join(current_app.root_path, 'static/images/profile', current_user.profile_picture)
            if os.path.exists(old_picture_path):
                os.remove(old_picture_path)
        
        current_user.profile_picture = picture_filename
        db.session.commit()
        
        return jsonify({'success': True})
    except Exception as e:
        print(f"Error updating profile picture: {e}")
        return jsonify({'success': False, 'error': 'An error occurred while updating your profile picture'}) 