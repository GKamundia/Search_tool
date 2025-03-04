import os
import logging
from flask import Flask, render_template, request, send_file
from src.scholarly_search import PubMedSearch
from src.query_builder import QueryBuilder
from dotenv import load_dotenv
import datetime
from logging.handlers import RotatingFileHandler

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'dev-secret')

@app.route('/', methods=['GET', 'POST'])
def index():
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

            # Execute search
            max_results = int(request.form.get('max_results', 50))
            search = PubMedSearch(max_results=max_results)
            query_str = qb.build()
            results = search.search(query_str)
            search.save_to_csv(results, 'data/results.csv')
            
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
        return send_file(
            os.path.abspath('data/results.csv'),
            mimetype='text/csv',
            download_name='pubmed_results.csv',
            as_attachment=True
        )
    except FileNotFoundError:
        return "No results to export", 404

if __name__ == '__main__':
    app.run(debug=True)
