from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

db = SQLAlchemy()

class SavedSearch(db.Model):
    """Model for saved searches"""
    __tablename__ = 'saved_searches'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    query = db.Column(db.String(500), nullable=False)
    parameters = db.Column(db.Text, nullable=False)  # JSON string of search parameters
    databases = db.Column(db.String(100), nullable=False)  # Comma-separated list of databases
    last_check_timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    frequency = db.Column(db.String(20), default='monthly')  # daily, weekly, monthly
    active = db.Column(db.Boolean, default=True)
    user_email = db.Column(db.String(100), nullable=True)  # For future user integration
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship with search results
    results = db.relationship('SearchResult', backref='search', lazy=True, cascade="all, delete-orphan")
    
    def get_parameters_dict(self):
        """Convert parameters JSON string to dictionary"""
        try:
            return json.loads(self.parameters)
        except:
            return {}
    
    def set_parameters_dict(self, params_dict):
        """Convert parameters dictionary to JSON string"""
        self.parameters = json.dumps(params_dict)
    
    def get_databases_list(self):
        """Convert databases string to list"""
        return self.databases.split(',')
    
    def set_databases_list(self, databases_list):
        """Convert databases list to string"""
        self.databases = ','.join(databases_list)


class SearchResult(db.Model):
    """Model for search results"""
    __tablename__ = 'search_results'
    
    id = db.Column(db.Integer, primary_key=True)
    saved_search_id = db.Column(db.Integer, db.ForeignKey('saved_searches.id'), nullable=False)
    paper_id = db.Column(db.String(100), nullable=False)  # PMID or arXiv ID
    database = db.Column(db.String(20), nullable=False)  # pubmed, arxiv, etc.
    title = db.Column(db.String(500), nullable=True)
    authors = db.Column(db.Text, nullable=True)
    abstract = db.Column(db.Text, nullable=True)
    url = db.Column(db.String(500), nullable=True)
    publication_date = db.Column(db.DateTime, nullable=True)
    found_date = db.Column(db.DateTime, default=datetime.utcnow)
    is_new = db.Column(db.Boolean, default=True)
    is_notified = db.Column(db.Boolean, default=False)
    is_read = db.Column(db.Boolean, default=False)  # Add this column
    
    def __repr__(self):
        return f"<SearchResult {self.id}: {self.title[:30]}...>"
