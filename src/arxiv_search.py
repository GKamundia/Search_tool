import logging
from typing import List, Dict
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import requests
from bs4 import BeautifulSoup
import pandas as pd
import os
from urllib.parse import urlencode

class ArxivAPIError(Exception):
    pass

class ArXivSearch:
    def __init__(self, max_results: int = 100):
        self.max_results = max_results
        self.logger = logging.getLogger(__name__)
        self.base_url = "http://export.arxiv.org/api/query"
        
    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        retry=retry_if_exception_type((ArxivAPIError, requests.exceptions.RequestException))
    )
    def search(self, query: str) -> List[Dict]:
        """Search arXiv API with query string"""
        try:
            params = {
                "search_query": query,
                "start": 0,
                "max_results": self.max_results,
                "sortBy": "relevance",
                "sortOrder": "descending"
            }
            
            response = requests.get(f"{self.base_url}?{urlencode(params)}")
            response.raise_for_status()
            
            if response.status_code == 403:
                raise ArxivAPIError("Rate limit exceeded")
                
            return self._parse_response(response.content)
            
        except Exception as e:
            self.logger.error(f"arXiv search failed: {str(e)}")
            raise

    def _parse_response(self, content: bytes) -> List[Dict]:
        soup = BeautifulSoup(content, 'xml')
        entries = soup.find_all('entry')
        
        results = []
        for entry in entries:
            arxiv_id = entry.id.text.split('/')[-1]
            result = {
                'title': entry.title.text.strip(),
                'authors': ', '.join([a.find('name').text for a in entry.find_all('author')]),
                'abstract': entry.summary.text.strip(),
                'published': entry.published.text,
                'pdf_url': f"https://arxiv.org/pdf/{arxiv_id}",
                'arxiv_id': arxiv_id,
                'categories': [cat['term'] for cat in entry.find_all('category')],
                'primary_category': entry.find('category')['term'] if entry.find('category') else '',
                'journal_ref': entry.journal_ref.text if entry.journal_ref else ''
            }
            results.append(result)
            
        return results

    def save_to_csv(self, results: List[Dict], filename: str = 'data/arxiv_results.csv') -> None:
        try:
            abs_path = os.path.abspath(filename)
            os.makedirs(os.path.dirname(abs_path), exist_ok=True)
            df = pd.DataFrame(results)
            
            columns = [
                'arxiv_id', 'title', 'authors', 'published',
                'primary_category', 'pdf_url', 'abstract'
            ]
            
            df.to_csv(
                abs_path,
                mode='a' if os.path.exists(abs_path) else 'w',
                index=False,
                header=not os.path.exists(abs_path),
                columns=columns
            )
            self.logger.info(f"Saved {len(results)} arXiv results to {abs_path}")
        except Exception as e:
            self.logger.error(f"Failed to save arXiv CSV: {str(e)}")
            raise
