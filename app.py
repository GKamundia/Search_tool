from flask import Flask, render_template, request, jsonify, send_file
from src.scholarly_search import ScholarSearch
from src.query_builder import QueryBuilder
import pandas as pd
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
qb = QueryBuilder()
searcher = ScholarSearch()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search():
    # Build platform-specific queries
    google_query = qb.build_google_query(
        title=request.form.get('google_title'),
        author=request.form.get('google_author'),
        site=request.form.get('google_site')
    )
    
    pubmed_query = qb.build_pubmed_query(
        title=request.form.get('pubmed_title'),
        abstract=request.form.get('pubmed_abstract'),
        author=request.form.get('pubmed_author')
    )

    # Execute search
    results = searcher.execute_advanced_search(google_query, pubmed_query)
    
    # Convert to DataFrame for CSV export
    df = pd.DataFrame(results)
    df.to_csv('data/latest_results.csv', index=False)
    
    return render_template('results.html', 
                         results=results,
                         google_count=len([r for r in results if r['source'] == 'Google Scholar']),
                         pubmed_count=len([r for r in results if r['source'] == 'PubMed']))

@app.route('/export')
def export():
    return send_file('data/latest_results.csv',
                     mimetype='text/csv',
                     download_name='search_results.csv',
                     as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
