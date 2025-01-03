import requests
import os
from flask import current_app
from config.cache_config import cache

TMDB_API_KEY = os.environ.get('TMDB_API_KEY')
if not TMDB_API_KEY:
    raise ValueError("TMDB_API_KEY not found in environment variables")

TMDB_BASE_URL = 'https://api.themoviedb.org/3'

def get_endpoint_type(media_type):
    """Convert internal media type to TMDB API endpoint type"""
    if media_type == 'tv':
        return 'tv'
    return 'movie'

@cache.memoize(timeout=300)  # Cache for 5 minutes
def search_media(query, media_type='movie'):
    try:
        endpoint_type = get_endpoint_type(media_type)
        response = requests.get(
            f'{TMDB_BASE_URL}/search/{endpoint_type}',
            params={
                'api_key': TMDB_API_KEY,
                'query': query,
                'language': 'en-US',
                'page': 1
            }
        )
        response.raise_for_status()
        results = response.json().get('results', [])
        # Add media_type to each result
        for result in results:
            result['media_type'] = media_type
        return results
    except Exception as e:
        current_app.logger.error(f"Error searching {media_type}: {str(e)}")
        return []

@cache.memoize(timeout=3600)  # Cache for 1 hour
def fetch_movie_details(movie_id, media_type='movie'):
    try:
        endpoint_type = get_endpoint_type(media_type)
        response = requests.get(
            f'{TMDB_BASE_URL}/{endpoint_type}/{movie_id}',
            params={
                'api_key': TMDB_API_KEY,
                'language': 'en-US',
                'append_to_response': 'keywords,videos'
            }
        )
        response.raise_for_status()
        details = response.json()
        
        # Add keywords as a string
        if 'keywords' in details:
            keywords = details['keywords'].get('keywords', [])
            details['keywords'] = ' '.join([k['name'] for k in keywords])
        
        return details
    except Exception as e:
        current_app.logger.error(f"Error fetching {media_type} details: {str(e)}")
        return None

@cache.memoize(timeout=3600)  # Cache for 1 hour
def get_recommendations_for_item(item_id, media_type):
    try:
        endpoint_type = get_endpoint_type(media_type)
        current_app.logger.info(f"Getting recommendations for {endpoint_type} {item_id}")
        
        # Log the full URL being requested
        url = f'{TMDB_BASE_URL}/{endpoint_type}/{item_id}/recommendations'
        current_app.logger.info(f"Making request to: {url}")
        
        response = requests.get(
            url,
            params={
                'api_key': TMDB_API_KEY,
                'language': 'en-US',
                'page': 1
            }
        )
        
        # Log the response status and URL
        current_app.logger.info(f"Response status: {response.status_code}")
        current_app.logger.info(f"Full URL with params: {response.url}")
        
        if response.status_code == 404:
            current_app.logger.error(f"404 error: Item not found for {endpoint_type} {item_id}")
            return []
            
        response.raise_for_status()
        results = response.json().get('results', [])
        
        current_app.logger.info(f"Found {len(results)} recommendations")
        
        # Process results
        processed_results = []
        for item in results:
            if item:  # Only process valid items
                processed_item = {
                    'id': item.get('id'),
                    'title': item.get('title') if media_type == 'movie' else item.get('name'),
                    'overview': item.get('overview', ''),
                    'poster_path': item.get('poster_path', ''),
                    'vote_average': float(item.get('vote_average', 0)),
                    'release_date': item.get('release_date') if media_type == 'movie' else item.get('first_air_date'),
                    'media_type': media_type,
                    'genres': item.get('genre_ids', [])
                }
                processed_results.append(processed_item)
        
        current_app.logger.info(f"Processed {len(processed_results)} valid recommendations")
        return processed_results
        
    except requests.exceptions.RequestException as e:
        current_app.logger.error(f"Request error getting recommendations for {media_type} {item_id}: {str(e)}")
        return []
    except Exception as e:
        current_app.logger.error(f"Error getting recommendations for {media_type} {item_id}: {str(e)}")
        return []

@cache.memoize(timeout=3600)  # Cache for 1 hour
def get_media_details(media_id, media_type):
    try:
        endpoint_type = get_endpoint_type(media_type)
        response = requests.get(
            f'{TMDB_BASE_URL}/{endpoint_type}/{media_id}',
            params={
                'api_key': TMDB_API_KEY,
                'language': 'en-US',
                'append_to_response': 'videos,credits'
            }
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        current_app.logger.error(f"Error getting media details: {str(e)}")
        return None 