import os
import logging
import random
import time
from typing import List, Dict
from tenacity import retry, stop_after_attempt, wait_exponential
from scholarly import scholarly, ProxyGenerator
from fp.fp import FreeProxy
import requests
from bs4 import BeautifulSoup
import json
from fake_useragent import UserAgent
import pandas as pd
from thefuzz import fuzz
from dotenv import load_dotenv

load_dotenv()

class ScholarSearch:
    def __init__(self, scholar_max: int = 50, pubmed_max: int = 100, 
                 use_fuzzy: bool = False, fuzzy_threshold: int = 85):
        self.scholar_max = scholar_max
        self.pubmed_max = pubmed_max
        self.use_fuzzy = use_fuzzy
        self.fuzzy_threshold = fuzzy_threshold
        self.user_agent_rotator = UserAgent()
        self.proxy_pool = FreeProxy(https=True).get_proxy_list(repeat=3)
        self.current_proxy = None
        self.request_count = 0
        self.reset_threshold = random.randint(3, 7)
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

    def _rotate_identity(self):
        """Rotate IP and user agent to avoid detection"""
        try:
            self.current_proxy = random.choice(self.proxy_pool)
            scholarly.use_proxy(http=self.current_proxy, https=self.current_proxy)
        except Exception as e:
            self.logger.warning(f"Proxy rotation failed: {str(e)}")
            
        scholarly.set_user_agent(self.user_agent_rotator.random)
        self.request_count = 0
        self.reset_threshold = random.randint(3, 7)
        self.logger.info("Rotated identity - New User Agent & Proxy")

    def _human_like_delay(self):
        """Randomized delay patterns to mimic human behavior"""
        delay_patterns = [
            (1.5, 3.5),   # Short pause
            (4.2, 7.8),   # Medium pause
            (10.5, 15.3) # Long pause after multiple requests
        ]
        min_d, max_d = random.choice(delay_patterns)
        delay = random.uniform(min_d, max_d) + random.gauss(0, 0.3)
        time.sleep(abs(delay))

    @retry(stop=stop_after_attempt(5), 
           wait=wait_exponential(multiplier=1, min=4, max=60),
           before_sleep=lambda _: logging.info("Retrying after CAPTCHA detection..."))
    def _search_pubmed(self, query: str) -> List[Dict]:
        """Search PubMed's Entrez API"""
        base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
        params = {
            "db": "pubmed",
            "term": query,
            "retmode": "json",
            "retmax": self.pubmed_max,
            "api_key": os.getenv("PUBMED_API_KEY")
        }
        
        try:
            response = requests.get(base_url, params=params)
            response.raise_for_status()
            data = response.json()
            
            id_list = data.get("esearchresult", {}).get("idlist", [])
            return self._fetch_pubmed_details(id_list)
            
        except Exception as e:
            self.logger.error(f"PubMed search failed: {str(e)}")
            return []

    def _fetch_pubmed_details(self, pmids: List[str]) -> List[Dict]:
        """Get detailed records from PubMed IDs"""
        base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
        params = {
            "db": "pubmed",
            "id": ",".join(pmids),
            "retmode": "xml",
            "api_key": os.getenv("PUBMED_API_KEY")
        }

        try:
            response = requests.get(base_url, params=params)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, "xml")
            
            articles = []
            for article in soup.find_all("PubmedArticle"):
                doi = article.find("ArticleId", IdType="doi")
                articles.append({
                    "title": article.find("ArticleTitle").get_text() if article.find("ArticleTitle") else "Untitled",
                    "authors": ", ".join([a.get_text() for a in article.find_all("Author") if a and a.get_text()]),
                    "year": article.find("PubDate").Year.get_text() if article.find("PubDate") and article.find("PubDate").Year else "",
                    "doi": doi.get_text() if doi else "",
                    "url": f"https://pubmed.ncbi.nlm.nih.gov/{article.find('PMID').get_text()}"
                })
            return articles
            
        except Exception as e:
            self.logger.error(f"PubMed details fetch failed: {str(e)}")
            return []

    def _search_publications(self, query: str) -> List[Dict]:
        try:
            search_results = []
            self._human_like_delay()
            
            if self.request_count >= self.reset_threshold:
                self._rotate_identity()

            generator = scholarly.search_pubs(query)
            self.request_count += 1
            
            while len(search_results) < self.scholar_max:
                try:
                    result = next(generator)
                    if 'CAPTCHA' in str(result).upper():
                        raise RuntimeError("Google CAPTCHA detected")
                    search_results.append(result)
                except StopIteration:
                    break
            return search_results[:self.scholar_max]
        except Exception as e:
            self.logger.error(f"Search failed: {str(e)}")
            if 'CAPTCHA' in str(e).upper():
                captcha_url = "https://scholar.google.com/scholar?q=please+enable+cookies"
                if "https://scholar.google.com" in str(e):
                    captcha_url = str(e).split("visit ")[1]
                
                print(f"\nCAPTCHA required! Please visit this URL in a browser:")
                print(f"\n{captcha_url}")
                input("After solving the CAPTCHA, press Enter to continue...")
                self._rotate_identity()
                return self._search_publications(query)
            raise

    def _check_duplicate(self, result: Dict, existing: pd.DataFrame) -> bool:
        doi = self._extract_doi(result)
        if doi and doi in existing['doi'].values:
            return True
            
        if self.use_fuzzy:
            title = result.get('bib', {}).get('title', result.get('title', 'Untitled'))
            matches = existing['title'].apply(
                lambda x: fuzz.ratio(x, title) > self.fuzzy_threshold
            )
            if matches.any():
                return True
                
        return False

    def _save_results(self, results: List[Dict]):
        df = pd.DataFrame([{
            'title': pub.get('bib', {}).get('title', pub.get('title', 'Untitled')),
            'authors': ', '.join(pub.get('bib', {}).get('author', [])) if 'bib' in pub else ', '.join(pub.get('authors', [])),
            'year': pub['bib'].get('year', '') if 'bib' in pub else pub.get('year', ''),
            'doi': self._extract_doi(pub),
            'url': pub.get('pub_url', '')
        } for pub in results])

        output_path = 'data/results.csv'
        if os.path.exists(output_path):
            df.to_csv(output_path, mode='a', header=False, index=False)
        else:
            df.to_csv(output_path, index=False)

    def _extract_doi(self, result):
        """Robust DOI extraction with fallback"""
        try:
            if 'doi' in result.get('pub_url', ''):
                return result['pub_url'].split('doi=')[-1]
            return scholarly.bibtex(result).get('doi', '')
        except Exception as e:
            self.logger.warning(f"DOI extraction failed: {str(e)}")
            return None

    def execute_search(self, query: str):
        existing_df = pd.read_csv('data/results.csv') if os.path.exists('data/results.csv') else pd.DataFrame()
        
        try:
            try:
                # First try Google Scholar
                results = self._search_publications(query)
            except Exception as e:
                self.logger.warning(f"Google Scholar failed, trying PubMed: {str(e)}")
                results = self._search_pubmed(query)
            filtered = [pub for pub in results if not self._check_duplicate(pub, existing_df)]
            
            if filtered:
                self._save_results(filtered)
                self.logger.info(f"Saved {len(filtered)} new results")
            else:
                self.logger.info("No new unique results found")
                
        except Exception as e:
            self.logger.error(f"Fatal error: {str(e)}")
            raise
