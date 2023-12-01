"""
This module sets up the Flask application configuration, including the database setup and 
OAuth integration.
"""

import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from authlib.integrations.flask_client import OAuth
from dotenv import find_dotenv, load_dotenv

# .env file initialization
ENV_FILE = find_dotenv()
if ENV_FILE:
    load_dotenv(ENV_FILE)

# Initialize Flask Application
app = Flask(__name__)
app.secret_key = os.environ.get("APP_SECRET_KEY")

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///hackernews.db'

# Initialize SQLAlchemy
db = SQLAlchemy(app)

# OAuth configuration
oauth = OAuth(app)
oauth.register(
    "auth0",
    client_id=os.environ.get("AUTH0_CLIENT_ID"),
    client_secret=os.environ.get("AUTH0_CLIENT_SECRET"),
    client_kwargs={"scope": "openid profile email"},
    server_metadata_url=f'https://{os.environ.get("AUTH0_DOMAIN")}/.well-known/openid-configuration'
)
