from datetime import datetime
from flask import render_template, request, jsonify, redirect, url_for
from app import app, db
from models.user_preference import UserPreference
from models.user import User
from services.tmdb_service import search_media, fetch_movie_details, get_media_details, TMDB_API_KEY, TMDB_BASE_URL
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
            ratings = UserPreference.query.filter_by(user_id=current_user.id).all()
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
@login_required
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
            ratings = UserPreference.query.filter_by(user_id=current_user.id).all()
            for rating in ratings:
                if rating.media_type == 'movie' or rating.media_type == 'tv':
                    user_ratings[f"{rating.media_type}_{rating.tmdb_id}"] = rating.rating
                elif rating.media_type == 'anime':
                    user_ratings[f"anime_{rating.mal_id}"] = rating.rating
        
        # Search for anime
        try:
            anime_results = search_anime(query)
            if anime_results:
                for item in anime_results:
                    if item and isinstance(item, dict):
                        item['user_rating'] = user_ratings.get(f"anime_{item.get('id')}")
                all_results.extend(anime_results)
        except Exception as e:
            print(f"Anime search error: {str(e)}")
        
        # Search for movies
        try:
            movie_results = search_media(query, 'movie')
            if movie_results:
                for item in movie_results:
                    if item and isinstance(item, dict):
                        processed_item = {
                            'title': item.get('title') or item.get('name', 'Unknown Title'),
                            'name': item.get('name') or item.get('title', 'Unknown Title'),
                            'vote_average': float(item.get('vote_average', 0)),
                            'id': item.get('id', 0),
                            'poster_path': item.get('poster_path', ''),
                            'overview': item.get('overview', ''),
                            'release_date': item.get('release_date', ''),
                            'first_air_date': item.get('first_air_date', ''),
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
                            'title': item.get('name') or item.get('title', 'Unknown Title'),
                            'name': item.get('name') or item.get('title', 'Unknown Title'),
                            'vote_average': float(item.get('vote_average', 0)),
                            'id': item.get('id', 0),
                            'poster_path': item.get('poster_path', ''),
                            'overview': item.get('overview', ''),
                            'release_date': item.get('first_air_date', ''),
                            'first_air_date': item.get('first_air_date', ''),
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
        
        # Check if this item is already rated by the current user
        if media_type == 'anime':
            existing_rating = UserPreference.query.filter_by(
                mal_id=tmdb_id,
                media_type='anime',
                user_id=current_user.id
            ).first()
        else:
            existing_rating = UserPreference.query.filter_by(
                tmdb_id=tmdb_id,
                media_type=media_type,
                user_id=current_user.id
            ).first()
        
        if existing_rating:
            # Update existing rating
            existing_rating.rating = rating
            existing_rating.created_at = datetime.utcnow()
            db.session.commit()
            return jsonify({'message': 'Rating updated successfully'})
        
        # Fetch additional details
        if media_type == 'anime':
            details = get_anime_details(tmdb_id)
            if details:
                anime_data = details.get('data', {})
                preference = UserPreference(
                    user_id=current_user.id,
                    title=title,
                    media_type='anime',
                    rating=rating,
                    mal_id=tmdb_id,
                    genres=' '.join([genre['name'] for genre in anime_data.get('genres', [])]),
                    overview=anime_data.get('synopsis', 'No overview available'),
                    keywords=' '.join([genre['name'] for genre in anime_data.get('genres', [])]),
                    vote_average=float(anime_data.get('score', 0)) / 2,  # Convert 10-point scale to 5-point
                    popularity=float(anime_data.get('popularity', 0)),
                    image_url=anime_data.get('images', {}).get('jpg', {}).get('large_image_url', ''),
                    release_date=anime_data.get('aired', {}).get('from', '').split('T')[0] if anime_data.get('aired', {}).get('from') else None
                )
        else:
            details = fetch_movie_details(tmdb_id, media_type)
            if details:
                preference = UserPreference(
                    user_id=current_user.id,
                    title=title,
                    media_type=media_type,
                    rating=rating,
                    tmdb_id=tmdb_id,
                    genres=' '.join([genre['name'] for genre in details.get('genres', [])]),
                    overview=details.get('overview', 'No overview available'),
                    keywords=details.get('keywords', ''),
                    vote_average=float(details.get('vote_average', 0)),
                    popularity=float(details.get('popularity', 0)),
                    poster_path=details.get('poster_path', ''),
                    release_date=details.get('release_date') or details.get('first_air_date')
                )
            else:
                # Create a basic preference if details fetch fails
                preference = UserPreference(
                    user_id=current_user.id,
                    title=title,
                    media_type=media_type,
                    rating=rating,
                    tmdb_id=tmdb_id,
                    overview='No overview available',
                    vote_average=0,
                    popularity=0,
                    release_date=None
                )
        
        print(f"Adding new preference: {preference.title} ({preference.media_type})")  # Debug log
        db.session.add(preference)
        db.session.commit()
        return jsonify({'message': 'Preference added successfully'})
            
    except Exception as e:
        print(f"Error adding preference: {str(e)}")  # Error log
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/get_recommendations')
@login_required
def get_recommendations_route():
    try:
        # Get user's ratings
        user_ratings = {}
        if current_user.is_authenticated:
            ratings = UserPreference.query.filter_by(user_id=current_user.id).all()
            for rating in ratings:
                if rating.media_type == 'movie' or rating.media_type == 'tv':
                    user_ratings[f"{rating.media_type}_{rating.tmdb_id}"] = rating.rating
                elif rating.media_type == 'anime':
                    user_ratings[f"anime_{rating.mal_id}"] = rating.rating

        # Get recommendations
        recommendations = get_recommendations()

        # Add user ratings to recommendations
        for rec in recommendations:
            if rec.get('media_type') == 'anime':
                rec['user_rating'] = user_ratings.get(f"anime_{rec.get('id')}")
            else:
                rec['user_rating'] = user_ratings.get(f"{rec.get('media_type')}_{rec.get('id')}")

            # Ensure title is set
            if not rec.get('title'):
                rec['title'] = rec.get('name', 'Unknown Title')

            # Ensure release_date is set
            if not rec.get('release_date'):
                rec['release_date'] = rec.get('first_air_date', 'N/A')

            # Ensure overview is set
            if not rec.get('overview'):
                rec['overview'] = 'No overview available'

            # Normalize vote_average to 5-point scale
            if rec.get('vote_average'):
                rec['vote_average'] = float(rec['vote_average'])

        return jsonify(recommendations)
    except Exception as e:
        print(f"Error getting recommendations: {str(e)}")
        return jsonify([]), 500

@app.route('/get_details', methods=['POST'])
def get_details():
    try:
        data = request.json
        media_type = data.get('media_type')
        tmdb_id = data.get('tmdb_id')

        if not media_type or not tmdb_id:
            return jsonify({'error': 'Missing media_type or tmdb_id'}), 400

        # Get user's rating if they're logged in
        user_rating = None
        if current_user.is_authenticated:
            if media_type == 'anime':
                existing_rating = UserPreference.query.filter_by(
                    mal_id=tmdb_id,
                    media_type='anime',
                    user_id=current_user.id
                ).first()
            else:
                existing_rating = UserPreference.query.filter_by(
                    tmdb_id=tmdb_id,
                    media_type=media_type,
                    user_id=current_user.id
                ).first()
            if existing_rating:
                user_rating = existing_rating.rating

        try:
            if media_type == 'anime':
                # Get anime details from Jikan API
                response = requests.get(f'https://api.jikan.moe/v4/anime/{tmdb_id}')
                if response.status_code == 200:
                    details = response.json()
                    anime_data = details.get('data', {})
                    return jsonify({
                        'genres': [{'name': genre.get('name', '')} for genre in anime_data.get('genres', []) if genre.get('name')],
                        'episodes': anime_data.get('episodes', 'Unknown'),
                        'aired': anime_data.get('aired', {}).get('string', 'Unknown air date'),
                        'studios': [studio.get('name', '') for studio in anime_data.get('studios', []) if studio.get('name')],
                        'poster_path': anime_data.get('images', {}).get('jpg', {}).get('large_image_url', ''),
                        'videos': {'results': []},  # Anime doesn't have trailer data in the same format
                        'overview': anime_data.get('synopsis', 'No overview available'),
                        'title': anime_data.get('title', 'Unknown Title'),
                        'vote_average': float(anime_data.get('score', 0)) / 2 if anime_data.get('score') else 0,  # Convert 10-point scale to 5-point
                        'release_date': anime_data.get('aired', {}).get('string', 'Unknown release date'),
                        'user_rating': user_rating
                    })
            else:
                # Get movie/TV show details from TMDB
                endpoint = 'movie' if media_type == 'movie' else 'tv'
                response = requests.get(
                    f'{TMDB_BASE_URL}/{endpoint}/{tmdb_id}',
                    params={
                        'api_key': TMDB_API_KEY,
                        'language': 'en-US',
                        'append_to_response': 'videos,keywords'
                    }
                )
                
                if response.status_code == 200:
                    details = response.json()
                    
                    # Handle runtime for TV shows (use first episode runtime if available)
                    if media_type == 'tv':
                        runtime = details.get('episode_run_time', [])
                        runtime = runtime[0] if runtime else None
                    else:
                        runtime = details.get('runtime')

                    return jsonify({
                        'genres': details.get('genres', []),
                        'runtime': runtime,
                        'release_date': details.get('release_date') or details.get('first_air_date', 'Unknown release date'),
                        'poster_path': details.get('poster_path', ''),
                        'videos': details.get('videos', {'results': []}),
                        'overview': details.get('overview', 'No overview available'),
                        'title': details.get('title') or details.get('name', 'Unknown Title'),
                        'vote_average': float(details.get('vote_average', 0)) / 2,  # Convert to 5-point scale
                        'keywords': details.get('keywords', {}).get('keywords', []),
                        'user_rating': user_rating
                    })
                
        except Exception as e:
            print(f"Error fetching details: {str(e)}")
            return jsonify({'error': str(e)}), 500

    except Exception as e:
        print(f"Error in get_details: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/my_ratings')
@login_required
def my_ratings():
    try:
        # Get all user preferences for the current user ordered by rating and created_at
        ratings = UserPreference.query.filter_by(user_id=current_user.id).order_by(
            UserPreference.rating.desc(),
            UserPreference.created_at.desc()
        ).all()
        
        # Convert ratings to dictionary format and fetch additional details
        ratings_list = []
        for rating in ratings:
            rating_dict = rating.to_dict()
            
            # Fetch additional details for each item
            if rating.media_type == 'anime':
                details = get_anime_details(rating.mal_id)
                if details:
                    anime_data = details.get('data', {})
                    rating_dict['release_date'] = anime_data.get('aired', {}).get('from', '').split('T')[0] if anime_data.get('aired', {}).get('from') else None
            else:
                details = fetch_movie_details(rating.tmdb_id, rating.media_type)
                if details:
                    rating_dict['release_date'] = details.get('release_date') or details.get('first_air_date')
            
            ratings_list.append(rating_dict)
        
        # Group ratings by media type for filtering
        media_types = set(rating.media_type for rating in ratings)
        
        return render_template(
            'my_ratings.html',
            ratings=ratings_list,
            media_types=media_types
        )
    except Exception as e:
        print(f"Error fetching ratings: {str(e)}")
        return render_template('my_ratings.html', ratings=[], media_types=set())

@app.route('/delete_rating/<int:rating_id>', methods=['DELETE'])
@login_required
def delete_rating(rating_id):
    rating = UserPreference.query.get_or_404(rating_id)
    # Check if the rating belongs to the current user
    if rating.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    db.session.delete(rating)
    db.session.commit()
    return jsonify({'message': 'Rating deleted successfully'})

@app.route('/recommendations')
@login_required
def recommendations_page():
    return render_template('recommendations.html')

@app.route('/top_rated/<media_type>')
def top_rated(media_type):
    try:
        print(f"Fetching top rated {media_type}")  # Debug log
        
        if media_type == 'anime':
            # Get top anime from Jikan API
            print("Fetching from Jikan API")  # Debug log
            response = requests.get(
                f'{JIKAN_BASE_URL}/top/anime',
                params={'page': 1, 'limit': 20},
                headers={'Accept': 'application/json'}
            )
            print(f"Jikan API response status: {response.status_code}")  # Debug log
            
            if response.status_code == 200:
                data = response.json().get('data', [])
                print(f"Found {len(data)} anime results")  # Debug log
                results = []
                for item in data:
                    formatted_item = format_anime_result(item)
                    if formatted_item:
                        results.append(formatted_item)
                print(f"Formatted {len(results)} anime results")  # Debug log
                return jsonify(results)
        else:
            # Get top rated from TMDB
            print(f"Fetching from TMDB API with key: {TMDB_API_KEY[:4]}...")  # Debug log
            response = requests.get(
                f'{TMDB_BASE_URL}/{media_type}/top_rated',
                params={
                    'api_key': TMDB_API_KEY,
                    'language': 'en-US',
                    'page': 1
                }
            )
            print(f"TMDB API response status: {response.status_code}")  # Debug log
            
            if response.status_code == 200:
                data = response.json()
                results = []
                for item in data.get('results', [])[:20]:  # Limit to 20 items
                    if item:
                        item['media_type'] = media_type
                        results.append(item)
                print(f"Found {len(results)} {media_type} results")  # Debug log
                return jsonify(results)
            else:
                print(f"TMDB API error response: {response.text}")  # Debug log
        
        return jsonify([])
    except Exception as e:
        print(f"Error fetching top rated {media_type}: {str(e)}")
        print(f"Full error: {repr(e)}")  # More detailed error info
        return jsonify([]) 