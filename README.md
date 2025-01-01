# MovieMatch - Movie and TV Show Recommendation App

A modern web application that provides personalized movie and TV show recommendations based on your viewing preferences. Built with Flask and powered by TMDB and Jikan APIs.



## Features

- 🎬 Search for movies, TV shows, and anime
- ⭐ Rate content you've watched
- 🎯 Get personalized recommendations based on your ratings
- 📱 Modern, responsive interface
- 🎨 Dark mode design
- 🎥 Watch trailers directly in the app
- 📊 Filter and sort your ratings
- 🔄 Real-time updates

## Tech Stack

- **Backend**: Python Flask
- **Database**: SQLite with SQLAlchemy
- **Frontend**: HTML, CSS, JavaScript
- **UI Framework**: Bootstrap 5
- **APIs**: 
  - TMDB (The Movie Database) for movies and TV shows
  - Jikan API for anime content

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- TMDB API key (get it from [TMDB website](https://www.themoviedb.org/))

## Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/moviematch.git
   cd moviematch
   ```

2. Create and activate a virtual environment:
   ```bash
   # Windows
   python -m venv venv
   venv\Scripts\activate

   # Linux/macOS
   python3 -m venv venv
   source venv/bin/activate
   ```

3. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up your environment variables:
   ```bash
   # Create .env file
   cp .env.example .env
   
   # Edit .env and add your TMDB API key
   TMDB_API_KEY=your_tmdb_api_key_here
   ```

5. Initialize the database:
   ```bash
   flask db upgrade
   ```

6. Run the application:
   ```bash
   python app.py
   ```

7. Open your browser and navigate to `http://localhost:5000`

## Project Structure

```
moviematch/
├── app.py              # Application entry point
├── config/            # Configuration files
├── models/            # Database models
├── routes/            # Route handlers
├── services/          # External API services
├── static/            # Static files (CSS, JS)
├── templates/         # HTML templates
├── migrations/        # Database migrations
├── requirements.txt   # Python dependencies
└── README.md         # Project documentation
```

## API Endpoints

- `GET /` - Home page
- `POST /search` - Search for movies, TV shows, and anime
- `GET /my_ratings` - View user ratings
- `POST /add_preference` - Add or update a rating
- `DELETE /delete_rating/<id>` - Delete a rating
- `GET /recommendations` - Get personalized recommendations
- `GET /top_rated/<media_type>` - Get top-rated content by media type

## Contributing

We welcome contributions to MovieMatch! Here's how you can help:

1. Fork the repository
2. Create a new branch (`git checkout -b feature/improvement`)
3. Make your changes
4. Run tests if available
5. Commit your changes (`git commit -am 'Add new feature'`)
6. Push to the branch (`git push origin feature/improvement`)
7. Create a Pull Request

## Development

To run the application in development mode with debug enabled:

```bash
export FLASK_ENV=development
export FLASK_DEBUG=1
python app.py
```

## Troubleshooting

Common issues and solutions:

1. **API Key Issues**
   - Ensure your TMDB API key is correctly set in the `.env` file
   - Verify the API key is active in your TMDB account dashboard

2. **Database Errors**
   - Make sure you have write permissions in the `instance` directory
   - Try deleting the database file and restarting the application

3. **Dependencies Issues**
   - Clear your Python cache: `python -m pip cache purge`
   - Ensure you're using Python 3.8 or higher
   - Try creating a new virtual environment

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [TMDB](https://www.themoviedb.org/) for their comprehensive movie and TV show database
- [Jikan API](https://jikan.moe/) for providing anime data
- [Bootstrap](https://getbootstrap.com/) for the UI framework
- [Font Awesome](https://fontawesome.com/) for the icons

## Contact

If you have any questions or suggestions, please open an issue or submit a pull request. 
