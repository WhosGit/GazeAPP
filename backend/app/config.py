'''Configuration file for the Flask application.'''

import pathlib

HOST = '0.0.0.0'
PORT = 5000
DEBUG = True

SECRET_KEY = 'cc6a27b7d3208ef55d640dea54a5d35d0f7eb1b61e22ff3d96054abf4ded5c9d'

# File upload settings
ROOT_DIR = pathlib.Path(__file__).resolve().parent.parent
UPLOAD_FOLDER = ROOT_DIR / 'var' / 'uploads'
# Ensure the upload folder exists
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)

OUTPUT_FOLDER = ROOT_DIR / 'var' / 'outputs'
OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)

# Allowed file extensions
