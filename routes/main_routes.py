from datetime import datetime
from flask import render_template, request, jsonify, redirect, url_for, flash
from app import app
from models.user_preference import UserPreference
from models.user import User
from services.tmdb_service import search_media, fetch_movie_details, get_media_details, TMDB_API_KEY, TMDB_BASE_URL, get_recommendations_for_item
from services.anime_service import search_anime, get_anime_details, format_anime_result, JIKAN_BASE_URL
from services.recommendation_service import get_recommendations
from flask_login import login_required, current_user
import requests

@app.route('/')
def home():
    try:
        # Fetch top-rated movies
        movie_response = requests.get(
            f'{TMDB_BASE_URL}/movie/top_rated',
            params={
                'api_key': TMDB_API_KEY,
                'language': 'en-US',
                'page': 1
            }
        )
        movies = movie_response.json().get('results', [])[:8]  # Get top 8 movies

        # Fetch top-rated TV shows
        tv_response = requests.get(
            f'{TMDB_BASE_URL}/tv/top_rated',
            params={
                'api_key': TMDB_API_KEY,
                'language': 'en-US',
                'page': 1
            }
        )
        tv_shows = tv_response.json().get('results', [])[:8]  # Get top 8 TV shows

        # Get user's ratings if logged in
        user_ratings = {}
        if current_user.is_authenticated:
            ratings = UserPreference.get_user_preferences(current_user.username)
            for rating in ratings:
                if rating.media_type == 'movie' or rating.media_type == 'tv':
                    user_ratings[f"{rating.media_type}_{rating.tmdb_id}"] = rating.rating

        # Process movies
        processed_movies = [{
            'id': movie['id'],
            'title': movie['title'],
            'overview': movie['overview'],
            'poster_path': movie['poster_path'],
            'vote_average': movie['vote_average'],
            'release_date': movie['release_date'],
            'media_type': 'movie',
            'user_rating': user_ratings.get(f"movie_{movie['id']}")
        } for movie in movies]

        # Process TV shows
        processed_tv_shows = [{
            'id': show['id'],
            'title': show['name'],
            'overview': show['overview'],
            'poster_path': show['poster_path'],
            'vote_average': show['vote_average'],
            'release_date': show['first_air_date'],
            'media_type': 'tv',
            'user_rating': user_ratings.get(f"tv_{show['id']}")
        } for show in tv_shows]

        # Combine and sort by rating
        top_rated = sorted(
            processed_movies + processed_tv_shows,
            key=lambda x: x['vote_average'],
            reverse=True
        )

        return render_template('index.html', top_rated=top_rated)
    except Exception as e:
        print(f"Error fetching top rated media: {str(e)}")
        return render_template('index.html', top_rated=[])

@app.route('/search', methods=['POST'])
def search():
    try:
        data = request.get_json()
        print(f"Search request data: {data}")  # Debug log
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        query = data.get('query')
        
        if not query:
            return jsonify({'error': 'No search query provided'}), 400
            
        all_results = []

        # Get user's ratings if logged in
        user_ratings = {}
        if current_user.is_authenticated:
            ratings = UserPreference.get_user_preferences(current_user.username)
            for rating in ratings:
                if rating.media_type == 'movie' or rating.media_type == 'tv':
                    user_ratings[f"{rating.media_type}_{rating.tmdb_id}"] = rating.rating

        # Search for movies
        try:
            movie_results = search_media(query, 'movie')
            if movie_results:
                for item in movie_results:
                    if item and isinstance(item, dict):
                        processed_item = {
                            'id': item.get('id', 0),
                            'title': item.get('title', 'Unknown Title'),
                            'overview': item.get('overview', ''),
                            'poster_path': item.get('poster_path', ''),
                            'vote_average': float(item.get('vote_average', 0)),
                            'release_date': item.get('release_date', ''),
                            'media_type': 'movie',
                            'user_rating': user_ratings.get(f"movie_{item.get('id')}")
                        }
                        all_results.append(processed_item)
        except Exception as e:
            print(f"Movie search error: {str(e)}")
        
        # Search for TV shows
        try:
            tv_results = search_media(query, 'tv')
            if tv_results:
                for item in tv_results:
                    if item and isinstance(item, dict):
                        processed_item = {
                            'id': item.get('id', 0),
                            'title': item.get('name', 'Unknown Title'),
                            'overview': item.get('overview', ''),
                            'poster_path': item.get('poster_path', ''),
                            'vote_average': float(item.get('vote_average', 0)),
                            'release_date': item.get('first_air_date', ''),
                            'media_type': 'tv',
                            'user_rating': user_ratings.get(f"tv_{item.get('id')}")
                        }
                        all_results.append(processed_item)
        except Exception as e:
            print(f"TV search error: {str(e)}")

        # Sort results by vote average
        all_results.sort(key=lambda x: float(x.get('vote_average', 0)), reverse=True)
        
        print(f"Total results found: {len(all_results)}")  # Debug log
        return jsonify({'results': all_results})
        
    except Exception as e:
        print(f"Search error: {str(e)}")  # Error log
        return jsonify({'error': f'Search failed: {str(e)}'}), 400

@app.route('/add_preference', methods=['POST'])
@login_required
def add_preference():
    try:
        data = request.json
        print(f"Add preference request data: {data}")  # Debug log
        
        media_type = data['media_type']
        tmdb_id = data['tmdb_id']
        title = data['title']
        rating = data['rating']

        # Create new preference
        preference = UserPreference.create(
            username=current_user.username,
            tmdb_id=tmdb_id,
            media_type=media_type,
            rating=rating,
            title=title
        )
        
        return jsonify({'message': 'Rating added successfully'})
        
    except Exception as e:
        print(f"Error adding preference: {str(e)}")
        return jsonify({'error': str(e)}), 400

@app.route('/get_recommendations')
@login_required
def get_recommendations():
    try:
        # Get user's preferences
        user_preferences = UserPreference.get_user_preferences(current_user.username)
        
        if not user_preferences:
            return jsonify({'message': 'No ratings found. Rate some movies or TV shows to get recommendations.'})

        # Process preferences
        recommendations = []
        for pref in user_preferences:
            if pref.rating >= 4:  # Only use highly rated items for recommendations
                similar_items = get_recommendations_for_item(pref.tmdb_id, pref.media_type)
                if similar_items:
                    recommendations.extend(similar_items)

        # Remove duplicates and sort by vote average
        seen = set()
        unique_recommendations = []
        for item in recommendations:
            item_key = f"{item['media_type']}_{item['id']}"
            if item_key not in seen:
                seen.add(item_key)
                unique_recommendations.append(item)

        sorted_recommendations = sorted(
            unique_recommendations,
            key=lambda x: float(x.get('vote_average', 0)),
            reverse=True
        )

        return jsonify({'recommendations': sorted_recommendations[:20]})  # Return top 20 recommendations

    except Exception as e:
        print(f"Error getting recommendations: {str(e)}")
        return jsonify({'error': str(e)}), 400

@app.route('/my_ratings')
@login_required
def my_ratings():
    try:
        # Get user's ratings
        ratings = UserPreference.get_user_preferences(current_user.username)
        
        # Convert to list of dictionaries and fetch media details
        ratings_list = []
        for rating in ratings:
            rating_dict = rating.to_dict()
            
            # Get media details from TMDB
            if rating.media_type in ['movie', 'tv']:
                details = get_media_details(rating.tmdb_id, rating.media_type)
                if details:
                    rating_dict.update({
                        'poster_path': details.get('poster_path'),
                        'overview': details.get('overview'),
                        'vote_average': details.get('vote_average', 0),
                        'release_date': details.get('first_air_date' if rating.media_type == 'tv' else 'release_date'),
                        'genres': ' '.join(genre['name'] for genre in details.get('genres', []))
                    })
            
            ratings_list.append(rating_dict)
        
        # Sort by created_at (most recent first)
        ratings_list.sort(key=lambda x: x['created_at'], reverse=True)
        
        return render_template('my_ratings.html', ratings=ratings_list)
    except Exception as e:
        print(f"Error fetching ratings: {str(e)}")
        flash('Error fetching ratings', 'error')
        return redirect(url_for('home'))

@app.route('/recommendations')
@login_required
def recommendations():
    return render_template('recommendations.html')

@app.route('/get_details', methods=['POST'])
def get_details():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        media_type = data.get('media_type')
        tmdb_id = data.get('tmdb_id')
        
        if not media_type or not tmdb_id:
            return jsonify({'error': 'Missing media_type or tmdb_id'}), 400
            
        details = get_media_details(tmdb_id, media_type)
        if not details:
            return jsonify({'error': 'Failed to fetch media details'}), 404
            
        # Get runtime safely
        runtime = None
        if media_type == 'tv':
            episode_run_time = details.get('episode_run_time', [])
            runtime = episode_run_time[0] if episode_run_time else None
        else:
            runtime = details.get('runtime')
            
        # Get videos and filter for YouTube trailers
        videos = details.get('videos', {}).get('results', [])
        filtered_videos = []
        for video in videos:
            if video.get('site') == 'YouTube' and video.get('type') == 'Trailer':
                filtered_videos.append(video)
        
        # Process the response based on media type
        response = {
            'id': details.get('id'),
            'title': details.get('name' if media_type == 'tv' else 'title'),
            'overview': details.get('overview'),
            'poster_path': details.get('poster_path'),
            'vote_average': details.get('vote_average', 0),
            'release_date': details.get('first_air_date' if media_type == 'tv' else 'release_date'),
            'genres': details.get('genres', []),
            'runtime': runtime,
            'status': details.get('status'),
            'videos': {
                'results': filtered_videos
            }
        }
        
        return jsonify(response)
        
    except Exception as e:
        print(f"Error getting media details: {str(e)}")
        return jsonify({'error': str(e)}), 400 