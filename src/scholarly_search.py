import os
import logging
from typing import List, Dict
from tenacity import retry, stop_after_attempt, wait_exponential
from scholarly import scholarly
import pandas as pd
from thefuzz import fuzz
from dotenv import load_dotenv
import argparse
import os

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
            search_results = []
            generator = scholarly.search_pubs(query)
            
            while len(search_results) < self.max_results:
                try:
                    result = next(generator)
                    if 'CAPTCHA' in str(result).upper():
                        raise Exception("Google CAPTCHA detected - manual intervention required")
                    search_results.append(result)
                except StopIteration:
                    break
            return search_results[:self.max_results]
        except Exception as e:
            self.logger.error(f"Search failed: {str(e)}")
            if 'CAPTCHA' in str(e).upper():
                raise RuntimeError("CAPTCHA required - visit https://scholar.google.com to solve") from e
            raise

    def _check_duplicate(self, result: Dict, existing: pd.DataFrame) -> bool:
        doi = result.get('bib', {}).get('doi')
        if doi and doi in existing['doi'].values:
            return True
            
        if self.use_fuzzy:
            matches = existing['title'].apply(
                lambda x: fuzz.ratio(x, result['bib']['title']) > self.fuzzy_threshold
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
        print(f"Searching for:\n{query}")
        existing_df = pd.read_csv('data/results.csv') if os.path.exists('data/results.csv') else pd.DataFrame()
        
        try:
            results = self._search_publications(query)
            filtered = [pub for pub in results if not self._check_duplicate(pub, existing_df)]
            
            if filtered:
                self._save_results(filtered)
                print(f"Found {len(filtered)} new results")
                self.logger.info(f"Saved {len(filtered)} new results")
            else:
                print("No new unique results found")
                self.logger.info("No new unique results found")
                
        except Exception as e:
            self.logger.error(f"Fatal error in search execution: {str(e)}")
            print(f"Error: {str(e)}")
            raise

def main():
    parser = argparse.ArgumentParser(description='Search Google Scholar publications')
    parser.add_argument('query', type=str, help='Search query string')
    args = parser.parse_args()
    
    try:
        if not os.path.exists('logs'):
            os.makedirs('logs')
        if not os.path.exists('data'):
            os.makedirs('data')
            
        searcher = ScholarSearch()
        searcher.execute_search(args.query)
    except Exception as e:
        print(f"Critical error: {str(e)}")
        exit(1)

if __name__ == "__main__":
    main()
