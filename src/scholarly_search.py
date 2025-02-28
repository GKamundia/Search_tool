import os
import logging
from typing import List, Dict
from tenacity import retry, stop_after_attempt, wait_exponential
from scholarly import scholarly
import pandas as pd
from thefuzz import fuzz
from dotenv import load_dotenv

load_dotenv()

class ScholarSearch:
    def __init__(self, max_results: int = 50, use_fuzzy: bool = False, fuzzy_threshold: int = 85):
        self.max_results = max_results
        self.use_fuzzy = use_fuzzy
        self.fuzzy_threshold = fuzzy_threshold
        self._configure_logging()
        self._configure_proxy()
        
    def _configure_logging(self):
        logging.basicConfig(
            filename='logs/search.log',
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
    def _configure_proxy(self):
        proxy_config = {
            'http': os.getenv('HTTP_PROXY'),
            'https': os.getenv('HTTPS_PROXY')
        }
        if any(proxy_config.values()):
            scholarly.use_proxy(**proxy_config)
            self.logger.info('Proxy configuration loaded')

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def _search_publications(self, query: str) -> List[Dict]:
        try:
            return scholarly.search_pubs(query, self.max_results)
        except Exception as e:
            self.logger.error(f"Search failed: {str(e)}")
            raise

    def _check_duplicate(self, result: Dict, existing: pd.DataFrame) -> bool:
        doi = result.get('bib', {}).get('doi')
        if doi and doi in existing['doi'].values:
            return True
            
        if self.use_fuzzy:
            matches = existing['title'].apply(
                lambda x: fuzzy_match(x, result['bib']['title'], self.fuzzy_threshold)
            )
            if matches.any():
                return True
                
        return False

    def _save_results(self, results: List[Dict]):
        df = pd.DataFrame([{
            'title': pub['bib'].get('title', ''),
            'authors': ', '.join(pub['bib'].get('author', [])),
            'year': pub['bib'].get('year', ''),
            'doi': pub['bib'].get('doi', ''),
            'url': pub.get('pub_url', '')
        } for pub in results])

        output_path = 'data/results.csv'
        if os.path.exists(output_path):
            df.to_csv(output_path, mode='a', header=False, index=False)
        else:
            df.to_csv(output_path, index=False)

    def execute_search(self, query: str):
        existing_df = pd.read_csv('data/results.csv') if os.path.exists('data/results.csv') else pd.DataFrame()
        
        try:
            results = self._search_publications(query)
            filtered = [pub for pub in results if not self._check_duplicate(pub, existing_df)]
            
            if filtered:
                self._save_results(filtered)
                self.logger.info(f"Saved {len(filtered)} new results")
            else:
                self.logger.info("No new unique results found")
                
        except Exception as e:
            self.logger.error(f"Fatal error in search execution: {str(e)}")
            raise
