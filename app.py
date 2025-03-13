import os
import logging
import pandas as pd
from flask import Flask, render_template, request, send_file
import asyncio
from concurrent.futures import ThreadPoolExecutor
from src.gim_search import GIMSearch
from src.scholarly_search import PubMedSearch
from src.query_builder import QueryBuilder
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
            results = {'pubmed': [], 'gim': []}
            
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
                    'result_count': len(results)
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
