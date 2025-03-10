import os
import logging
import random
from typing import List, Dict
from tenacity import retry, stop_after_attempt, wait_exponential
import requests
from bs4 import BeautifulSoup
import pandas as pd
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

load_dotenv()

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
]

class GlobalIndexMedicusSearch:
    def __init__(self):
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=True, slow_mo=50)
        self.context = self.browser.new_context(
            user_agent=random.choice(USER_AGENTS)
        )
        self.page = self.context.new_page()

    def search(self, query: str) -> List[Dict]:
        try:
            self.page.goto("https://globalindexmedicus.net/")
            self.page.fill("input[name='q']", query)
            self.page.click("button[type='submit']")
            self.page.wait_for_selector(".search-results", timeout=10000)
            
            results = []
            items = self.page.query_selector_all(".result-item")
            for item in items:
                results.append({
                    "title": item.query_selector("h3").inner_text(),
                    "authors": item.query_selector(".authors").inner_text(),
                    "journal": item.query_selector(".journal").inner_text(),
                    "year": item.query_selector(".year").inner_text(),
                    "abstract": item.query_selector(".abstract").inner_text()
                })
            return results
        except Exception as e:
            self.page.screenshot(path='logs/gim_error.png')
            raise
        finally:
            self.browser.close()

    def save_to_csv(self, results: List[Dict], filename: str) -> None:
        pd.DataFrame(results).to_csv(filename, index=False)

class PubMedSearch:
    def __init__(self, max_results: int = 100):
        self.max_results = max_results
        self._configure_logging()
        self.existing_pmids = self._load_existing_pmids()

    def _configure_logging(self):
        logging.basicConfig(
            filename='logs/search.log',
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def search(self, query: str) -> List[Dict]:
        """Search PubMed's Entrez API"""
        base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
        params = {
            "db": "pubmed",
            "term": query,
            "retmode": "json",
            "retmax": self.max_results,
            "api_key": os.getenv("PUBMED_API_KEY")
        }
        
        try:
            response = requests.get(base_url, params=params)
            response.raise_for_status()
            data = response.json()
            id_list = data.get("esearchresult", {}).get("idlist", [])
            return self._fetch_details(id_list)
        except Exception as e:
            self.logger.error(f"Search failed: {str(e)}")
            return []

    def _load_existing_pmids(self) -> set:
        """Load existing PMIDs from saved results"""
        try:
            df = pd.read_csv('data/results.csv')
            return set(df['pmid'].astype(str))
        except FileNotFoundError:
            return set()

    def _fetch_details(self, pmids: List[str]) -> List[Dict]:
        """Get detailed records from PubMed IDs with deduplication"""
        new_pmids = [pmid for pmid in pmids if pmid not in self.existing_pmids]
        
        if not new_pmids:
            return []
            
        base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
        params = {
            "db": "pubmed",
            "id": ",".join(new_pmids),
            "retmode": "xml"
        }

        try:
            response = requests.get(base_url, params=params)
            response.raise_for_status()
            return self._parse_xml(response.content)
        except Exception as e:
            self.logger.error(f"Details fetch failed: {str(e)}")
            return []

    def _parse_xml(self, content: bytes) -> List[Dict]:
        """Parse PubMed XML response"""
        soup = BeautifulSoup(content, "xml")
        articles = []
        
        for article in soup.find_all("PubmedArticle"):
            articles.append({
                "pmid": article.find("PMID").get_text(),
                "title": article.find("ArticleTitle").get_text(),
                "abstract": article.find("AbstractText").get_text() if article.find("AbstractText") else "",
                "authors": ", ".join([a.get_text() for a in article.find_all("Author")]),
                "journal": article.find("Title").get_text() if article.find("Title") else "",
                "pub_date": article.find("PubMedPubDate", {"PubStatus": "pubmed"}).get_text(),
                "doi": self._extract_doi(article),
                "url": f"https://pubmed.ncbi.nlm.nih.gov/{article.find('PMID').get_text()}"
            })
        return articles

    def _extract_doi(self, article) -> str:
        """Extract DOI from article metadata"""
        if doi := article.find("ArticleId", {"IdType": "doi"}):
            return doi.get_text()
        return ""

    def save_to_csv(self, results: List[Dict], filename: str) -> None:
        """Save results to CSV with proper path handling and error logging"""
        try:
            abs_path = os.path.abspath(filename)
            os.makedirs(os.path.dirname(abs_path), exist_ok=True)
            df = pd.DataFrame(results)
            
            df.to_csv(
                abs_path,
                mode='a',
                index=False,
                header=not os.path.exists(abs_path)
            )
            self.logger.info(f"Saved {len(results)} records to {abs_path}")
        except Exception as e:
            self.logger.error(f"Failed to save CSV: {str(e)}")
            raise
