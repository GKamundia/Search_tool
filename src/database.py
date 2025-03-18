import os
from flask import Flask
from flask_migrate import Migrate
from src.models import db

def init_db(app: Flask):
    """Initialize the database with the Flask app"""
    # Configure SQLAlchemy
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///alerts.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize SQLAlchemy with the app
    db.init_app(app)
    
    # Initialize Flask-Migrate
    migrate = Migrate(app, db)
    
    # Create tables if they don't exist
    with app.app_context():
        db.create_all()
    
    return db
