from flask_caching import Cache

cache = Cache(config={
    'CACHE_TYPE': 'simple',  # Use in-memory cache for development
    'CACHE_DEFAULT_TIMEOUT': 300  # Cache timeout in seconds (5 minutes)
})

def init_cache(app):
    # Check if we're in production mode
    if not app.config.get('DEBUG', False):  # If DEBUG is False, we're in production
        # Use filesystem cache in production
        app.config['CACHE_TYPE'] = 'filesystem'
        app.config['CACHE_DIR'] = 'cache'
        app.config['CACHE_THRESHOLD'] = 1000  # Maximum number of items to store
    
    cache.init_app(app)
    return cache 