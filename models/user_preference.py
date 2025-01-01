from datetime import datetime
from app import db

class UserPreference(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    media_type = db.Column(db.String(10), nullable=False)  # 'movie', 'tv', or 'anime'
    rating = db.Column(db.Integer, nullable=False)
    tmdb_id = db.Column(db.Integer)  # TMDB ID (for movies/TV shows)
    mal_id = db.Column(db.Integer)   # MyAnimeList ID (for anime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    genres = db.Column(db.String(500))
    overview = db.Column(db.Text)
    keywords = db.Column(db.String(500))
    vote_average = db.Column(db.Float)
    popularity = db.Column(db.Float)
    image_url = db.Column(db.String(500))  # For storing direct image URLs (especially for anime)
    poster_path = db.Column(db.String(500))  # For TMDB poster paths
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'media_type': self.media_type,
            'rating': self.rating,
            'tmdb_id': self.tmdb_id,
            'mal_id': self.mal_id,
            'created_at': self.created_at.isoformat(),
            'genres': self.genres,
            'overview': self.overview,
            'keywords': self.keywords,
            'vote_average': self.vote_average,
            'popularity': self.popularity,
            'image_url': self.image_url,
            'poster_path': self.poster_path
        } 