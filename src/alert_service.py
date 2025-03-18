import logging
from datetime import datetime
from typing import Dict, List, Optional
import json

from src.models import db, SavedSearch, SearchResult
from src.pubmed_search import PubMedSearch
from src.arxiv_search import ArXivSearch
from src.query_builder import QueryBuilder

class AlertService:
    """Service to check for new papers and generate alerts"""
    
    def __init__(self, app=None):
        self.logger = logging.getLogger(__name__)
        self.app = app
    
    def check_for_new_papers(self, saved_search: SavedSearch) -> Dict:
        """
        Check for new papers for a saved search
        
        Args:
            saved_search: The SavedSearch object to check
            
        Returns:
            Dict with results information
        """
        self.logger.info(f"Checking for new papers for saved search: {saved_search.name}")
        
        # Get the last check timestamp
        last_check = saved_search.last_check_timestamp
        
        # Get search parameters
        params = saved_search.get_parameters_dict()
        databases = saved_search.get_databases_list()
        query = saved_search.query
        
        # Initialize results
        new_papers = []
        all_papers = []
        
        # For each database in the saved search
        for database in databases:
            if database == 'pubmed':
                # Create PubMed search with date filter
                search = PubMedSearch(max_results=params.get('max_results', 50))
                # Add date filter to only get papers newer than last check
                results = search.search_with_date_filter(query, last_check)
                
                # Process results
                for paper in results:
                    paper['database'] = 'pubmed'
                    all_papers.append(paper)
                    
                    # Check if this is a new paper
                    if self._is_new_paper(saved_search.id, 'pubmed', paper.get('pmid')):
                        new_papers.append(paper)
                        # Save to database
                        self._save_paper_to_db(saved_search.id, 'pubmed', paper)
                
            elif database == 'arxiv':
                # Create ArXiv search with date filter
                qb = QueryBuilder()
                qb.add_term(query)
                search = ArXivSearch(max_results=params.get('max_results', 50), qb=qb)
                # Add date filter to only get papers newer than last check
                results = search.search_with_date_filter(query, last_check)
                
                # Process results
                for paper in results:
                    paper['database'] = 'arxiv'
                    all_papers.append(paper)
                    
                    # Check if this is a new paper
                    if self._is_new_paper(saved_search.id, 'arxiv', paper.get('arxiv_id')):
                        new_papers.append(paper)
                        # Save to database
                        self._save_paper_to_db(saved_search.id, 'arxiv', paper)
        
        # Update the last check timestamp
        saved_search.last_check_timestamp = datetime.utcnow()
        db.session.commit()
        
        self.logger.info(f"Found {len(new_papers)} new papers for saved search: {saved_search.name}")
        
        return {
            'saved_search': saved_search,
            'new_papers': new_papers,
            'all_papers': all_papers
        }
    
    def _is_new_paper(self, saved_search_id: int, database: str, paper_id: str) -> bool:
        """Check if a paper is new (not in the database)"""
        if not paper_id:
            return False
            
        existing = SearchResult.query.filter_by(
            saved_search_id=saved_search_id,
            database=database,
            paper_id=paper_id
        ).first()
        
        return existing is None
    
    def _save_paper_to_db(self, saved_search_id: int, database: str, paper: Dict) -> None:
        """Save a paper to the database"""
        try:
            # Extract paper ID based on database
            if database == 'pubmed':
                paper_id = paper.get('pmid')
                url = paper.get('url')
                pub_date_str = paper.get('pub_date')
                # Try to parse the publication date
                try:
                    pub_date = datetime.strptime(pub_date_str, '%Y-%m-%d')
                except:
                    pub_date = datetime.utcnow()
            elif database == 'arxiv':
                paper_id = paper.get('arxiv_id')
                url = paper.get('pdf_url')
                pub_date_str = paper.get('published')
                # Try to parse the publication date
                try:
                    pub_date = datetime.strptime(pub_date_str, '%Y-%m-%dT%H:%M:%SZ')
                except:
                    pub_date = datetime.utcnow()
            else:
                self.logger.warning(f"Unknown database: {database}")
                return
            
            # Create new search result
            result = SearchResult(
                saved_search_id=saved_search_id,
                paper_id=paper_id,
                database=database,
                title=paper.get('title', ''),
                authors=paper.get('authors', ''),
                abstract=paper.get('abstract', ''),
                url=url,
                publication_date=pub_date,
                is_new=True,
                is_notified=False
            )
            
            db.session.add(result)
            db.session.commit()
            
        except Exception as e:
            self.logger.error(f"Error saving paper to database: {str(e)}")
            db.session.rollback()
    
    def get_new_papers(self, saved_search_id: Optional[int] = None, 
                      database: Optional[str] = None, 
                      limit: int = 50) -> List[SearchResult]:
        """Get new papers from the database"""
        query = SearchResult.query.filter_by(is_new=True)
        
        if saved_search_id:
            query = query.filter_by(saved_search_id=saved_search_id)
        
        if database:
            query = query.filter_by(database=database)
        
        return query.order_by(SearchResult.found_date.desc()).limit(limit).all()
    
    def mark_as_read(self, result_id: int) -> bool:
        """Mark a search result as read (not new)"""
        try:
            result = SearchResult.query.get(result_id)
            if result:
                result.is_new = False
                db.session.commit()
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error marking paper as read: {str(e)}")
            db.session.rollback()
            return False
    
    def run_all_alerts(self, frequency: str = None) -> Dict:
        """Run alerts for all saved searches with the specified frequency"""
        results = {
            'total_searches': 0,
            'searches_with_new_papers': 0,
            'total_new_papers': 0,
            'details': []
        }
        
        # Get all active saved searches
        query = SavedSearch.query.filter_by(active=True)
        
        if frequency:
            query = query.filter_by(frequency=frequency)
        
        saved_searches = query.all()
        results['total_searches'] = len(saved_searches)
        
        for search in saved_searches:
            # Check for new papers
            check_result = self.check_for_new_papers(search)
            new_papers = check_result.get('new_papers', [])
            
            if new_papers:
                results['searches_with_new_papers'] += 1
                results['total_new_papers'] += len(new_papers)
                
                results['details'].append({
                    'search_id': search.id,
                    'search_name': search.name,
                    'new_papers_count': len(new_papers)
                })
        
        return results
