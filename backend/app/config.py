'''Configuration file for the Flask application.'''

import pathlib

HOST = '0.0.0.0'
PORT = 5000
DEBUG = True

# File upload settings
ROOT_DIR = pathlib.Path(__file__).resolve().parent.parent
UPLOAD_FOLDER = ROOT_DIR / 'var' / 'uploads'
# Ensure the upload folder exists
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)

OUTPUT_FOLDER = ROOT_DIR / 'var' / 'outputs'
OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)

# Allowed file extensions
