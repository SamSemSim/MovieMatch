import os
import requests
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

TMDB_API_KEY = os.getenv('TMDB_API_KEY')
if not TMDB_API_KEY:
    raise ValueError("TMDB_API_KEY not found in environment variables. Please add it to your .env file.")

TMDB_BASE_URL = 'https://api.themoviedb.org/3'

def search_media(query, media_type):
    """Search for movies or TV shows using TMDB API"""
    if not query:
        print("No query provided")
        return []
        
    try:
        response = requests.get(
            f'{TMDB_BASE_URL}/search/{media_type}',
            params={
                'api_key': TMDB_API_KEY,
                'query': query,
                'language': 'en-US',
                'append_to_response': 'videos'
            }
        )
        
        print(f"TMDB API Response Status: {response.status_code}")  # Debug log
        
        if response.status_code == 200:
            data = response.json()
            results = data.get('results', [])
            print(f"TMDB found {len(results)} results")  # Debug log
            
            # Add media_type to each result
            for result in results:
                result['media_type'] = media_type
                
            return results
            
        print(f"TMDB API error: {response.status_code}")
        return []
        
    except requests.exceptions.Timeout:
        print("TMDB API timeout")
        return []
    except requests.exceptions.RequestException as e:
        print(f"TMDB API request error: {str(e)}")
        return []
    except Exception as e:
        print(f"Error searching {media_type}: {str(e)}")
        return []

def fetch_movie_details(tmdb_id, media_type):
    """Fetch detailed movie information including keywords and genres"""
    try:
        # Get basic details
        endpoint = 'movie' if media_type == 'movie' else 'tv'
        response = requests.get(
            f'{TMDB_BASE_URL}/{endpoint}/{tmdb_id}',
            params={
                'api_key': TMDB_API_KEY,
                'language': 'en-US',
                'append_to_response': 'videos,keywords'
            }
        )
        
        if response.status_code != 200:
            print(f"Error fetching details: {response.status_code}")
            return None
            
        details = response.json()
        
        # Extract genres
        genres = details.get('genres', [])
        
        # Extract keywords
        keywords = []
        if 'keywords' in details:
            if media_type == 'movie':
                keywords = [kw['name'] for kw in details['keywords'].get('keywords', [])]
            else:
                keywords = [kw['name'] for kw in details['keywords'].get('results', [])]
        
        return {
            'genres': genres,
            'overview': details.get('overview', ''),
            'keywords': ' '.join(keywords),
            'vote_average': float(details.get('vote_average', 0)),
            'popularity': float(details.get('popularity', 0)),
            'poster_path': details.get('poster_path', ''),
            'videos': details.get('videos', {'results': []}),
            'runtime': details.get('runtime'),
            'release_date': details.get('release_date') or details.get('first_air_date')
        }
    except Exception as e:
        print(f"Error fetching details: {str(e)}")
        return None

def get_media_details(media_type, tmdb_id):
    """Get detailed information including videos"""
    try:
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
            # Add media_type to the response
            details['media_type'] = media_type
            return details
        print(f"Error getting media details: {response.status_code}")
        return None
    except Exception as e:
        print(f"Error getting media details: {str(e)}")
        return None

def get_recommendations_for_item(media_type, tmdb_id):
    """Get TMDB recommendations for a specific item"""
    try:
        response = requests.get(
            f'{TMDB_BASE_URL}/{media_type}/{tmdb_id}/recommendations',
            params={
                'api_key': TMDB_API_KEY,
                'language': 'en-US',
                'page': 1
            }
        )
        
        if response.status_code == 200:
            results = response.json().get('results', [])
            # Add media_type to each result
            for result in results:
                result['media_type'] = media_type
            return results
            
        print(f"Error getting recommendations: {response.status_code}")
        return []
    except Exception as e:
        print(f"Error getting recommendations: {str(e)}")
        return [] 