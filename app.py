import os
import logging
import pandas as pd
import json
from flask import Flask, render_template, request, send_file, redirect, url_for, jsonify, flash
from flask_cors import CORS
import asyncio
from concurrent.futures import ThreadPoolExecutor
from src.gim_search import GIMSearch
from src.pubmed_search import PubMedSearch
from src.arxiv_search import ArXivSearch
from src.query_builder import QueryBuilder
from src.database import init_db
from src.models import db, SavedSearch, SearchResult
from src.alert_service import AlertService
from src.email_service import EmailService
from src.scheduler import AlertScheduler
from dotenv import load_dotenv
import datetime
from logging.handlers import RotatingFileHandler

load_dotenv()

# Configure logging
log_dir = 'logs'
os.makedirs(log_dir, exist_ok=True)
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        RotatingFileHandler(
            os.path.join(log_dir, 'search.log'),
            maxBytes=10485760,  # 10MB
            backupCount=5
        ),
        logging.StreamHandler()  # Also log to console
    ]
)



app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'dev-secret')

# Configure email settings
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'localhost')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 25))
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER', 'noreply@example.com')
app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'False').lower() == 'true'


# Allow CORS for development
CORS(app, resources={
    r"/api/*": {"origins": "http://localhost:3000"}
})

# Initialize database
db = init_db(app)

# Initialize services
alert_service = AlertService(app)
email_service = EmailService(app)


# Add a sample API endpoint for testing
@app.route('/api/status', methods=['GET'])
def api_status():
    return jsonify({
        'status': 'online',
        'version': '1.0.0',
        'database_status': 'connected'
    })

@app.route('/', methods=['GET', 'POST'])
async def index():
    current_year = datetime.datetime.now().year
    if request.method == 'POST':
        try:
            # Build PubMed query from form data
            qb = QueryBuilder()
            terms = request.form.getlist('term')
            operators = request.form.getlist('boolean_operator')
            fields = request.form.getlist('field')
            
            # Build query with proper PubMed syntax
            query_parts = []
            for i, term in enumerate(terms):
                if term.strip():
                    field = fields[i] if i < len(fields) else ''
                    query_parts.append(qb.add_term(term, field).build())
                    if i < len(operators):
                        op = operators[i]
                        query_parts.append(op)

            # Add date filter if provided
            start_year = request.form.get('start_year')
            end_year = request.form.get('end_year')
            if start_year and end_year:
                qb.date_range(int(start_year), int(end_year))

            # Get search parameters
            max_results = int(request.form.get('max_results', 50))
            query_str = qb.build()
            selected_dbs = request.form.getlist('databases')
            
            # Execute searches concurrently
            results = {'pubmed': [], 'gim': [], 'arxiv': []}
            
            if 'pubmed' in selected_dbs:
                pubmed_search = PubMedSearch(max_results=max_results)
                results['pubmed'] = await asyncio.to_thread(pubmed_search.search, query_str)
                pubmed_search.save_to_csv(results['pubmed'], 'data/pubmed_results.csv')
            
            if 'gim' in selected_dbs:
                async with GIMSearch(max_results=max_results) as gim_search:
                    results['gim'] = await gim_search.search(query_str)
                    if results['gim']:
                        # Create data directory if it doesn't exist
                        os.makedirs('data', exist_ok=True)
                        
                        # Ensure all results have the same fields
                        for result in results['gim']:
                            # Add new fields if they don't exist
                            if 'publication_details' not in result:
                                result['publication_details'] = ""
                            if 'database_info' not in result:
                                result['database_info'] = ""
                            if 'subjects' not in result:
                                result['subjects'] = ""
                            if 'doc_id' not in result:
                                result['doc_id'] = ""
                        
                        # Save to CSV with overwrite mode to ensure clean results
                        pd.DataFrame(results['gim']).to_csv(
                            'data/gim_results.csv', 
                            mode='w',  # Use write mode instead of append
                            index=False
                        )
                        app.logger.info(f"Saved {len(results['gim'])} GIM results to CSV")
            
            if 'arxiv' in selected_dbs:
                arxiv_search = ArXivSearch(max_results=max_results, qb=qb)
                results['arxiv'] = await asyncio.to_thread(arxiv_search.search, query_str)
                if results['arxiv']:
                    os.makedirs('data', exist_ok=True)
                    arxiv_search.save_to_csv(results['arxiv'], 'data/arxiv_results.csv')
                    app.logger.info(f"Saved {len(results['arxiv'])} arXiv results to CSV")

            # Log the search
            app.logger.info(
                'Search executed',
                extra={
                    'query': query_str,
                    'terms': terms,
                    'operators': operators,
                    'fields': fields,
                    'start_year': start_year,
                    'end_year': end_year,
                    'max_results': max_results,
                    'result_count': sum(len(v) for v in results.values())  # Count total results
                }
            )
            
            return render_template('results.html', 
                                results=results,
                                query=query_str)
            
        except Exception as e:
            return render_template('error.html', error=str(e))

    return render_template('index.html', current_year=current_year)

@app.route('/export')
def export_results():
    try:
        # Check which file exists and return it
        if os.path.exists('data/gim_results.csv'):
            return send_file(
                os.path.abspath('data/gim_results.csv'),
                mimetype='text/csv',
                download_name='gim_results.csv',
                as_attachment=True
            )
        elif os.path.exists('data/pubmed_results.csv'):
            return send_file(
                os.path.abspath('data/pubmed_results.csv'),
                mimetype='text/csv',
                download_name='pubmed_results.csv',
                as_attachment=True
            )
        elif os.path.exists('data/results.csv'):
            return send_file(
                os.path.abspath('data/results.csv'),
                mimetype='text/csv',
                download_name='results.csv',
                as_attachment=True
            )
        else:
            return "No results to export", 404
    except FileNotFoundError:
        return "No results to export", 404

@app.route('/save_search', methods=['POST'])
def save_search():
    """Save a search query for alerts"""
    try:
        # Get form data
        name = request.form.get('search_name')
        query = request.form.get('query')
        databases = request.form.getlist('databases')
        frequency = request.form.get('frequency', 'monthly')
        email = request.form.get('email')
        
        # Get search parameters
        params = {
            'max_results': request.form.get('max_results', 50),
            'start_year': request.form.get('start_year'),
            'end_year': request.form.get('end_year')
        }
        
        # Create new saved search
        search = SavedSearch(
            name=name,
            query=query,
            parameters=json.dumps(params),
            databases=','.join(databases),
            frequency=frequency,
            active=True,
            user_email=email
        )
        
        db.session.add(search)
        db.session.commit()
        
        app.logger.info(f"Search '{name}' saved successfully")
        
        # Redirect to saved searches page
        return redirect(url_for('saved_searches'))
        
    except Exception as e:
        app.logger.error(f"Error saving search: {str(e)}")
        return render_template('error.html', error=f"Error saving search: {str(e)}")

@app.route('/saved_searches')
def saved_searches():
    """View saved searches"""
    # Using SQLAlchemy 2.0 style query
    searches = db.session.query(SavedSearch).order_by(SavedSearch.created_at.desc()).all()
    return render_template('saved_searches.html', searches=searches)

@app.route('/new_papers')
def new_papers():
    """View new papers"""
    # Get filter parameters
    search_id = request.args.get('search_id')
    database = request.args.get('database')
    
    # Get saved searches for filter dropdown using SQLAlchemy 2.0 style
    saved_searches = db.session.query(SavedSearch).all()
    
    # Get new papers with filters using SQLAlchemy 2.0 style
    query = db.session.query(SearchResult).filter_by(is_new=True)
    
    if search_id:
        query = query.filter_by(saved_search_id=int(search_id))
    
    if database:
        query = query.filter_by(database=database)
    
    # Order by found date (newest first)
    papers = query.order_by(SearchResult.found_date.desc()).all()
    
    return render_template(
        'new_papers.html',
        papers=papers,
        saved_searches=saved_searches,
        selected_search_id=search_id,
        selected_database=database
    )

@app.route('/run_search/<int:search_id>', methods=['POST'])
def run_search(search_id):
    """Manually run a saved search"""
    try:
        # Get the scheduler
        scheduler = app.config.get('scheduler')
        if not scheduler:
            return jsonify({'error': 'Scheduler not initialized'}), 500
        
        # Run the search
        result = scheduler.run_search_now(search_id)
        
        if 'error' in result:
            return jsonify({'error': result['error']}), 400
        
        return jsonify(result)
        
    except Exception as e:
        app.logger.error(f"Error running search: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/mark_as_read/<int:paper_id>', methods=['POST'])
def mark_as_read(paper_id):
    """Mark a paper as read"""
    try:
        result = alert_service.mark_as_read(paper_id)
        if result:
            return redirect(url_for('new_papers'))
        else:
            return render_template('error.html', error="Paper not found")
    except Exception as e:
        app.logger.error(f"Error marking paper as read: {str(e)}")
        return render_template('error.html', error=f"Error: {str(e)}")

@app.route('/delete_search/<int:search_id>', methods=['POST'])
def delete_search(search_id):
    """Delete a saved search"""
    try:
        # Using SQLAlchemy 2.0 style query
        search = db.session.get(SavedSearch, search_id)
        if search:
            db.session.delete(search)
            db.session.commit()
            app.logger.info(f"Search '{search.name}' deleted successfully")
        return redirect(url_for('saved_searches'))
    except Exception as e:
        app.logger.error(f"Error deleting search: {str(e)}")
        return render_template('error.html', error=f"Error: {str(e)}")

@app.route('/toggle_search/<int:search_id>', methods=['POST'])
def toggle_search(search_id):
    """Toggle a saved search active/inactive"""
    try:
        # Using SQLAlchemy 2.0 style query
        search = db.session.get(SavedSearch, search_id)
        if search:
            search.active = not search.active
            db.session.commit()
            status = "activated" if search.active else "deactivated"
            app.logger.info(f"Search '{search.name}' {status}")
        return redirect(url_for('saved_searches'))
    except Exception as e:
        app.logger.error(f"Error toggling search: {str(e)}")
        return render_template('error.html', error=f"Error: {str(e)}")

@app.route('/test_alert/<int:search_id>', methods=['POST'])
def test_alert(search_id):
    """Run a test alert with dummy papers"""
    try:
        # Using SQLAlchemy 2.0 style query
        search = db.session.get(SavedSearch, search_id)
        if not search:
            app.logger.warning(f"Search with ID {search_id} not found")
            return jsonify({'error': 'Search not found'}), 404
        
        app.logger.info(f"Running test alert for search: {search.name}")
        
        # Get search parameters
        params = search.get_parameters_dict()
        databases = search.get_databases_list()
        query = search.query
        
        # Initialize results
        new_papers = []
        all_papers = []
        
        # For each database in the saved search
        for database in databases:
            if database == 'pubmed':
                # Create PubMed search with test mode
                search_obj = PubMedSearch(max_results=params.get('max_results', 50))
                # Get test papers
                results = search_obj.search_with_date_filter(query, None, test_mode=True)
                
                # Process results
                for paper in results:
                    paper['database'] = 'pubmed'
                    all_papers.append(paper)
                    
                    # Save to database
                    try:
                        # Extract paper details
                        paper_id = paper.get('pmid')
                        url = paper.get('url')
                        
                        # Create new search result
                        result = SearchResult(
                            saved_search_id=search.id,
                            paper_id=paper_id,
                            database=database,
                            title=paper.get('title', ''),
                            authors=paper.get('authors', ''),
                            abstract=paper.get('abstract', ''),
                            url=url,
                            publication_date=datetime.now(),
                            is_new=True,
                            is_notified=False
                        )
                        
                        db.session.add(result)
                        new_papers.append(paper)
                        
                    except Exception as e:
                        app.logger.error(f"Error saving test paper to database: {str(e)}")
                
            elif database == 'arxiv':
                # Create ArXiv search with test mode
                qb = QueryBuilder()
                qb.add_term(query)
                search_obj = ArXivSearch(max_results=params.get('max_results', 50), qb=qb)
                # Get test papers
                results = search_obj.search_with_date_filter(query, None, test_mode=True)
                
                # Process results
                for paper in results:
                    paper['database'] = 'arxiv'
                    all_papers.append(paper)
                    
                    # Save to database
                    try:
                        # Extract paper details
                        paper_id = paper.get('arxiv_id')
                        url = paper.get('pdf_url')
                        
                        # Create new search result
                        result = SearchResult(
                            saved_search_id=search.id,
                            paper_id=paper_id,
                            database=database,
                            title=paper.get('title', ''),
                            authors=paper.get('authors', ''),
                            abstract=paper.get('abstract', ''),
                            url=url,
                            publication_date=datetime.now(),
                            is_new=True,
                            is_notified=False
                        )
                        
                        db.session.add(result)
                        new_papers.append(paper)
                        
                    except Exception as e:
                        app.logger.error(f"Error saving test paper to database: {str(e)}")
        
        # Commit all changes
        db.session.commit()
        
        # Send email notification if user email is set
        if new_papers and search.user_email:
            email_service.send_new_papers_notification(
                search.user_email,
                search,
                new_papers
            )
            app.logger.info(f"Sent test email notification to {search.user_email}")
        
        # Return success response
        return jsonify({
            'success': True,
            'search_name': search.name,
            'new_papers_count': len(new_papers),
            'message': 'Test alert completed successfully'
        })
        
    except Exception as e:
        app.logger.error(f"Error running test alert: {str(e)}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Initialize scheduler
    scheduler = AlertScheduler(app)
    scheduler.start()
    app.config['scheduler'] = scheduler
    
    try:
        app.run(debug=True)
    finally:
        # Ensure scheduler is shut down when app exits
        scheduler.stop()
