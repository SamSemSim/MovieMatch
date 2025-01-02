from datetime import datetime
from flask import render_template, request, jsonify
from app import app, db
from models.user_preference import UserPreference
from services.tmdb_service import search_media, fetch_movie_details, get_media_details, TMDB_API_KEY, TMDB_BASE_URL
from services.anime_service import search_anime, get_anime_details, format_anime_result, JIKAN_BASE_URL
from services.recommendation_service import get_recommendations
import requests

@app.route('/')
def home():
    return render_template('index.html')

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
        
        # Search for anime
        try:
            anime_results = search_anime(query)
            if anime_results:
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
                            'media_type': 'movie'
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
                            'media_type': 'tv'
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
def add_preference():
    try:
        data = request.json
        print(f"Add preference request data: {data}")  # Debug log
        
        media_type = data['media_type']
        tmdb_id = data['tmdb_id']
        title = data['title']
        rating = data['rating']
        
        # Check if this item is already rated
        if media_type == 'anime':
            existing_rating = UserPreference.query.filter_by(
                mal_id=tmdb_id,
                media_type='anime'
            ).first()
        else:
            existing_rating = UserPreference.query.filter_by(
                tmdb_id=tmdb_id,
                media_type=media_type
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
                    title=title,
                    media_type='anime',
                    rating=rating,
                    mal_id=tmdb_id,
                    genres=' '.join([genre['name'] for genre in anime_data.get('genres', [])]),
                    overview=anime_data.get('synopsis', 'No overview available'),
                    keywords=' '.join([genre['name'] for genre in anime_data.get('genres', [])]),
                    vote_average=float(anime_data.get('score', 0)) / 2,  # Convert 10-point scale to 5-point
                    popularity=float(anime_data.get('popularity', 0)),
                    image_url=anime_data.get('images', {}).get('jpg', {}).get('large_image_url', '')
                )
        else:
            details = fetch_movie_details(tmdb_id, media_type)
            if details:
                preference = UserPreference(
                    title=title,
                    media_type=media_type,
                    rating=rating,
                    tmdb_id=tmdb_id,
                    genres=' '.join([genre['name'] for genre in details.get('genres', [])]),
                    overview=details.get('overview', 'No overview available'),
                    keywords=details.get('keywords', ''),
                    vote_average=float(details.get('vote_average', 0)),
                    popularity=float(details.get('popularity', 0)),
                    poster_path=details.get('poster_path', '')
                )
            else:
                # Create a basic preference if details fetch fails
                preference = UserPreference(
                    title=title,
                    media_type=media_type,
                    rating=rating,
                    tmdb_id=tmdb_id,
                    overview='No overview available',
                    vote_average=0,
                    popularity=0
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
def get_recommendations_route():
    recommendations = get_recommendations()
    return jsonify(recommendations)

@app.route('/get_details', methods=['POST'])
def get_details():
    try:
        data = request.json
        media_type = data.get('media_type')
        tmdb_id = data.get('tmdb_id')

        if not media_type or not tmdb_id:
            return jsonify({'error': 'Missing media_type or tmdb_id'}), 400

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
                        'release_date': anime_data.get('aired', {}).get('string', 'Unknown release date')
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
                        'vote_average': float(details.get('vote_average', 0)),
                        'keywords': details.get('keywords', {}).get('keywords', [])
                    })
                
                print(f"TMDB API error: {response.status_code}")
                return jsonify({
                    'error': f'Failed to fetch details from TMDB API: {response.status_code}'
                }), response.status_code

        except (IndexError, KeyError, ValueError, TypeError) as e:
            print(f"Error processing details: {str(e)}")
            # Return a valid response with default values instead of failing
            return jsonify({
                'genres': [],
                'runtime': None,
                'release_date': 'Unknown release date',
                'poster_path': '',
                'videos': {'results': []},
                'overview': 'No overview available',
                'title': 'Unknown Title',
                'vote_average': 0,
                'keywords': []
            })

    except Exception as e:
        print(f"Error fetching details: {str(e)}")
        return jsonify({
            'error': f'Failed to fetch details: {str(e)}'
        }), 500

@app.route('/my_ratings')
def my_ratings():
    try:
        # Get all user preferences ordered by rating and created_at
        ratings = UserPreference.query.order_by(
            UserPreference.rating.desc(),
            UserPreference.created_at.desc()
        ).all()
        
        # Convert ratings to dictionary format
        ratings_list = [rating.to_dict() for rating in ratings]
        
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
def delete_rating(rating_id):
    rating = UserPreference.query.get_or_404(rating_id)
    db.session.delete(rating)
    db.session.commit()
    return jsonify({'message': 'Rating deleted successfully'})

@app.route('/recommendations')
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