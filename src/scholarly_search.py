import os
import logging
from typing import List, Dict
from tenacity import retry, stop_after_attempt, wait_exponential
import requests
from bs4 import BeautifulSoup
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

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

    def __init__(self, max_results: int = 100):
        self.max_results = max_results
        self._configure_logging()
        self.existing_pmids = self._load_existing_pmids()
        
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
