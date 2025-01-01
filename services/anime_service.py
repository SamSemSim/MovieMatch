import requests
import time
import json

JIKAN_BASE_URL = 'https://api.jikan.moe/v4'
RATE_LIMIT_DELAY = 1  # Delay between API calls to respect rate limits

def search_anime(query):
    """Search for anime using the Jikan API"""
    if not query:
        print("No query provided for anime search")
        return []
        
    try:
        print(f"Searching anime: {query}")  # Debug log
        
        # Ensure the query is properly encoded
        params = {
            'q': query,
            'sfw': True,
            'limit': 20,  # Limit results to 20 items
            'page': 1
        }
        print(f"Request params: {params}")  # Debug log
        
        response = requests.get(
            f'{JIKAN_BASE_URL}/anime',
            params=params,
            timeout=10,
            headers={'Accept': 'application/json'}
        )
        
        print(f"Jikan API Response Status: {response.status_code}")  # Debug log
        print(f"Jikan API Response Headers: {dict(response.headers)}")  # Debug log
        print(f"Jikan API Response: {response.text[:500]}")  # Debug log (first 500 chars)
        
        if response.status_code == 200:
            try:
                data = response.json()
                results = data.get('data', [])
                print(f"Found {len(results)} anime results")  # Debug log
                
                if not results:
                    print("No anime results found")
                    return []
                
                formatted_results = []
                for item in results:
                    try:
                        formatted_item = format_anime_result(item)
                        if formatted_item:
                            formatted_results.append(formatted_item)
                            print(f"Successfully formatted anime: {formatted_item.get('title')}")  # Debug log
                    except Exception as e:
                        print(f"Error formatting individual anime: {str(e)}")
                        continue
                
                print(f"Formatted {len(formatted_results)} anime results")  # Debug log
                return formatted_results
                
            except json.JSONDecodeError as e:
                print(f"JSON decode error: {str(e)}")
                print(f"Response content: {response.text}")
                return []
            
        if response.status_code == 429:  # Rate limit error
            print("Rate limit reached, waiting longer...")
            print(f"Rate limit headers: {response.headers.get('X-RateLimit-Remaining')} remaining")
            time.sleep(2)  # Wait longer for rate limit
            return search_anime(query)  # Retry the search
            
        print(f"Jikan API error: Status {response.status_code}")
        return []
        
    except requests.exceptions.Timeout:
        print("Jikan API timeout")
        return []
    except requests.exceptions.RequestException as e:
        print(f"Jikan API request error: {str(e)}")
        return []
    except Exception as e:
        print(f"Error searching anime: {str(e)}")
        print(f"Full error: {repr(e)}")  # More detailed error info
        return []

def get_anime_details(mal_id):
    """Get detailed anime information"""
    try:
        response = requests.get(f'{JIKAN_BASE_URL}/anime/{mal_id}/full')
        time.sleep(RATE_LIMIT_DELAY)  # Respect rate limit
        
        if response.status_code == 200:
            data = response.json().get('data', {})
            return format_anime_details(data)
        return None
    except Exception as e:
        print(f"Error fetching anime details: {str(e)}")
        return None

def get_anime_recommendations(mal_id):
    """Get anime recommendations based on a specific anime"""
    try:
        response = requests.get(f'{JIKAN_BASE_URL}/anime/{mal_id}/recommendations')
        time.sleep(RATE_LIMIT_DELAY)  # Respect rate limit
        
        if response.status_code == 200:
            data = response.json().get('data', [])
            return [format_anime_result(item['entry']) for item in data[:20]]  # Limit to 20 recommendations
        return []
    except Exception as e:
        print(f"Error fetching anime recommendations: {str(e)}")
        return []

def format_anime_result(item):
    """Format anime search result to match TMDB format"""
    if not item:
        return None
        
    try:
        # Get the best available image
        images = item.get('images', {})
        poster_url = (images.get('jpg', {}).get('large_image_url') or 
                     images.get('jpg', {}).get('image_url') or 
                     images.get('webp', {}).get('large_image_url') or 
                     '')
        
        # Get the start date
        aired = item.get('aired', {})
        start_date = aired.get('from', '').split('T')[0] if aired.get('from') else ''
        
        # Get the score and normalize it to match TMDB's 10-point scale
        score = item.get('score', 0)
        if score:
            try:
                score = float(score)
            except (ValueError, TypeError):
                score = 0.0
        
        # Get the synopsis/overview
        overview = item.get('synopsis', '')
        if overview and overview.lower() == 'none':
            overview = ''
        
        formatted_result = {
            'id': item.get('mal_id', 0),
            'title': item.get('title', 'Unknown Anime'),
            'name': item.get('title', 'Unknown Anime'),
            'original_title': item.get('title_japanese', ''),
            'overview': overview,
            'poster_path': poster_url,
            'vote_average': score,
            'popularity': float(item.get('members', 0)) / 10000,  # Normalize popularity
            'media_type': 'anime',
            'release_date': start_date,
            'first_air_date': start_date,
            'genres': [genre.get('name', '') for genre in item.get('genres', []) if genre]
        }
        
        print(f"Formatted anime result: {formatted_result['title']}")  # Debug log
        return formatted_result
        
    except Exception as e:
        print(f"Error formatting anime result: {str(e)}")
        print(f"Problematic item: {json.dumps(item, indent=2)}")  # Debug log
        return None

def format_anime_details(item):
    """Format detailed anime information"""
    videos = []
    if item.get('trailer', {}).get('youtube_id'):
        videos.append({
            'key': item['trailer']['youtube_id'],
            'site': 'YouTube',
            'type': 'Trailer'
        })
    
    return {
        'id': item.get('mal_id'),
        'title': item.get('title'),
        'original_title': item.get('title_japanese'),
        'overview': item.get('synopsis', ''),
        'poster_path': item.get('images', {}).get('jpg', {}).get('image_url'),
        'vote_average': item.get('score', 0) or 0,
        'popularity': item.get('members', 0) / 10000,
        'genres': [{'name': genre['name']} for genre in item.get('genres', [])],
        'runtime': item.get('duration', '').split(' ')[0] if item.get('duration') else None,
        'status': item.get('status'),
        'episodes': item.get('episodes'),
        'aired': item.get('aired', {}).get('string'),
        'studios': [studio['name'] for studio in item.get('studios', [])],
        'rating': item.get('rating'),
        'videos': {'results': videos}
    } 