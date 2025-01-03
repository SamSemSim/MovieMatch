# MovieMatch

A movie and TV show recommendation platform that helps users discover content based on their preferences.

## Features

- User authentication and profile management
- Movie and TV show search
- Personalized recommendations based on user ratings
- Trailer viewing functionality
- Responsive design for mobile and desktop

## Tech Stack

- Python 3.11
- Flask web framework
- SQLite database
- TMDB API for movie/TV data
- Bootstrap 5 for UI
- JavaScript for frontend interactivity

## Prerequisites

- Python 3.11 or higher
- pip (Python package manager)
- TMDB API key

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/moviematch.git
cd moviematch
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the root directory with the following variables:
```
FLASK_ENV=development
SECRET_KEY=your-secret-key
TMDB_API_KEY=your-tmdb-api-key
```

5. Initialize the database:
```bash
flask db upgrade
```

## Development

Run the development server:
```bash
python app.py
```

The application will be available at `http://localhost:5000`

## Deployment

### Prerequisites for Deployment

- Git
- Python 3.11
- PostgreSQL (for production)
- Gunicorn

### Deployment Steps

1. Set up environment variables in your production environment:
   - `FLASK_ENV=production`
   - `SECRET_KEY`
   - `TMDB_API_KEY`
   - `DATABASE_URL` (if using PostgreSQL)

2. Install production dependencies:
```bash
pip install -r requirements.txt
```

3. Initialize the database:
```bash
flask db upgrade
```

4. Run with Gunicorn:
```bash
gunicorn -c gunicorn_config.py app:app
```

## API Documentation

### Authentication Endpoints

#### POST /auth/register
Register a new user.
- Request body:
  ```json
  {
    "username": "string",
    "email": "string",
    "password": "string"
  }
  ```

#### POST /auth/login
Login a user.
- Request body:
  ```json
  {
    "username": "string",
    "password": "string"
  }
  ```

### Media Endpoints

#### GET /search
Search for movies and TV shows.
- Query parameters:
  - `query`: Search term
  - `media_type`: "movie" or "tv"

#### POST /add_preference
Add or update a media rating.
- Request body:
  ```json
  {
    "media_type": "string",
    "tmdb_id": "integer",
    "rating": "integer",
    "title": "string"
  }
  ```

#### GET /get_recommendations
Get personalized recommendations.
- Requires authentication
- Returns recommended movies and TV shows based on user preferences

## Error Handling

The application includes custom error pages and logging:
- 404 Not Found
- 500 Internal Server Error
- All errors are logged to `logs/error.log`
- General application logs in `logs/info.log`

## Caching

The application implements caching for API responses:
- Search results: 5 minutes
- Media details: 1 hour
- Recommendations: 1 hour

## Security

- CSRF protection enabled
- Secure session configuration
- Password hashing
- XSS protection
- Content Security Policy
- Rate limiting on API endpoints

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 
