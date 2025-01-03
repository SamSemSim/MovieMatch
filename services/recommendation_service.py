from datetime import datetime
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from models.user_preference import UserPreference
from services.tmdb_service import get_recommendations_for_item
from services.anime_service import get_anime_recommendations
from flask import current_app

def create_content_matrix(items):
    """Create a content matrix from movie features"""
    # Combine all text features
    items['content'] = items['genres'] + ' ' + items['overview'] + ' ' + items['keywords']
    
    # Create TF-IDF matrix
    tfidf = TfidfVectorizer(stop_words='english')
    return tfidf.fit_transform(items['content'].fillna(''))

def get_recommendations():
    """Get recommendations based on user preferences"""
    try:
        # Get user's top rated items
        top_preferences = UserPreference.query.order_by(
            UserPreference.rating.desc()
        ).limit(5).all()
        
        if not top_preferences:
            return []
        
        recommendations = []
        seen_ids = set()  # To track unique recommendations
        
        for pref in top_preferences:
            try:
                # Get recommendations based on media type
                if pref.tmdb_id:  # For movies and TV shows
                    current_app.logger.info(f"Getting recommendations for {pref.media_type} {pref.tmdb_id}")
                    recs = get_recommendations_for_item(pref.tmdb_id, pref.media_type)
                    for rec in recs:
                        if rec and rec.get('id') not in seen_ids:
                            seen_ids.add(rec['id'])
                            recommendations.append(rec)
            except Exception as e:
                current_app.logger.error(f"Error getting recommendations for {pref.media_type} {pref.tmdb_id}: {str(e)}")
                continue
        
        # Sort by vote average and limit to 20 recommendations
        recommendations.sort(key=lambda x: float(x.get('vote_average', 0)), reverse=True)
        return recommendations[:20]
        
    except Exception as e:
        current_app.logger.error(f"Error in get_recommendations: {str(e)}")
        return [] 