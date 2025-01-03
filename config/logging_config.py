import os
import logging
from logging.handlers import RotatingFileHandler

def setup_logging(app):
    # Create logs directory if it doesn't exist
    if not os.path.exists('logs'):
        os.makedirs('logs')

    # Set up file handler for error logging
    error_handler = RotatingFileHandler(
        'logs/error.log',
        maxBytes=10000000,  # 10MB
        backupCount=10
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(logging.Formatter(
        '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
    ))

    # Set up file handler for general logging
    info_handler = RotatingFileHandler(
        'logs/info.log',
        maxBytes=10000000,  # 10MB
        backupCount=10
    )
    info_handler.setLevel(logging.INFO)
    info_handler.setFormatter(logging.Formatter(
        '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
    ))

    # Add handlers to the app logger
    app.logger.addHandler(error_handler)
    app.logger.addHandler(info_handler)
    app.logger.setLevel(logging.INFO)

    # Log startup message
    app.logger.info('MovieMatch startup') 