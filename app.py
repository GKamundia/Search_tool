import os
from flask import Flask, render_template, request
from src.scholarly_search import PubMedSearch
from src.query_builder import QueryBuilder
from dotenv import load_dotenv
import datetime

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
            
            # Construct query from multiple terms
            for i, term in enumerate(terms):
                if term.strip():
                    field = fields[i] if i < len(fields) else ''
                    qb.add_term(term, field)
                    if i < len(operators):
                        op = operators[i]
                        if op == 'AND': qb.AND()
                        elif op == 'OR': qb.OR()
                        elif op == 'NOT': qb.NOT()

            # Add date filter if provided
            start_year = request.form.get('start_year')
            end_year = request.form.get('end_year')
            if start_year and end_year:
                qb.date_range(int(start_year), int(end_year))

            # Execute search
            max_results = int(request.form.get('max_results', 50))
            search = PubMedSearch(max_results=max_results)
            results = search.search(qb.build())
            
            return render_template('results.html', results=results)
            
        except Exception as e:
            return render_template('error.html', error=str(e))

    return render_template('index.html', current_year=current_year)

if __name__ == '__main__':
    app.run(debug=True)
