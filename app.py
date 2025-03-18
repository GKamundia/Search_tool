import os
import logging
import pandas as pd
import json
from flask import Flask, render_template, request, send_file, redirect, url_for, jsonify, flash
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

# Initialize database
db = init_db(app)

# Initialize services
alert_service = AlertService(app)
email_service = EmailService(app)

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

if __name__ == '__main__':
    app.run(debug=True)
