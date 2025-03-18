import os
import logging
from typing import List, Dict, Optional
from datetime import datetime
from tenacity import retry, stop_after_attempt, wait_exponential
import requests
from bs4 import BeautifulSoup
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

class PubMedSearch:
    def __init__(self, max_results: int = 100):
        self.max_results = max_results
        self.logger = logging.getLogger(__name__)
        self.existing_pmids = self._load_existing_pmids()
        
    def search_with_date_filter(self, query: str, since_date: Optional[datetime] = None) -> List[Dict]:
        """Search PubMed with date filter"""
        if not since_date:
            return self.search(query)
            
        # Format the date for PubMed API (YYYY/MM/DD)
        date_str = since_date.strftime("%Y/%m/%d")
        
        # Add date filter to query if not already present
        if "[dp]" not in query:
            date_query = f"{query} AND {date_str}:3000[dp]"
        else:
            # Query already has date filter, we need to modify it
            # This is a simplistic approach; a more robust parser would be needed for complex queries
            date_query = query.replace("]", f" AND {date_str}:3000]")
        
        self.logger.info(f"Searching PubMed with date filter: {date_query}")
        
        # Execute search with date filter
        return self.search(date_query)

    def _load_existing_pmids(self) -> set:
        """Load existing PMIDs from saved results"""
        try:
            df = pd.read_csv('data/pubmed_results.csv')
            if 'pmid' in df.columns:
                return set(df['pmid'].astype(str))
            return set()
        except FileNotFoundError:
            return set()
        except Exception as e:
            self.logger.warning(f"Could not load existing PMIDs: {str(e)}")
            return set()

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
            
            if not id_list:
                self.logger.info(f"No PubMed IDs found for query: {query}")
                # Create empty CSV file
                self.save_to_csv([], 'data/pubmed_results.csv')
                return []
                
            results = self._fetch_details(id_list)
            
            # Save results to CSV regardless of count
            self.save_to_csv(results, 'data/pubmed_results.csv')
            
            return results
        except Exception as e:
            self.logger.error(f"PubMed search failed: {str(e)}")
            # Create empty CSV file to indicate search was attempted
            self.save_to_csv([], 'data/pubmed_results.csv')
            return []

    def _fetch_details(self, pmids: List[str]) -> List[Dict]:
        """Get detailed records from PubMed IDs with deduplication"""
        new_pmids = [pmid for pmid in pmids if pmid not in self.existing_pmids]
        
        if not new_pmids:
            self.logger.info("No new PubMed IDs to fetch")
            return []
            
        base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
        params = {
            "db": "pubmed",
            "id": ",".join(new_pmids),
            "retmode": "xml",
            "api_key": os.getenv("PUBMED_API_KEY")
        }

        try:
            response = requests.get(base_url, params=params)
            response.raise_for_status()
            
            # Log response details for debugging
            self.logger.info(f"PubMed API response: status={response.status_code}, content_length={len(response.content)}")
            
            return self._parse_xml(response.content)
        except Exception as e:
            self.logger.error(f"Details fetch failed: {str(e)}")
            return []

    def _parse_xml(self, content: bytes) -> List[Dict]:
        """Parse PubMed XML response"""
        soup = BeautifulSoup(content, "xml")
        articles = []
        
        # Check if we have any PubmedArticle elements
        article_elements = soup.find_all("PubmedArticle")
        if not article_elements:
            self.logger.warning(f"No PubmedArticle elements found in XML response")
            # Log a sample of the response for debugging
            self.logger.debug(f"XML response sample: {content[:500]}...")
            return []
        
        for article in article_elements:
            try:
                # Get elements with null checks
                pmid_elem = article.find("PMID")
                title_elem = article.find("ArticleTitle")
                abstract_elem = article.find("AbstractText")
                
                # Find journal title with fallbacks
                journal_elem = None
                journal_info = article.find("Journal")
                if journal_info:
                    journal_elem = journal_info.find("Title")
                
                # Find publication date with fallbacks
                pub_date_elem = article.find("PubMedPubDate", {"PubStatus": "pubmed"})
                if not pub_date_elem:
                    pub_date_elem = article.find("PubMedPubDate")
                
                # Only add article if we have at least PMID and title
                if pmid_elem and title_elem:
                    pmid = pmid_elem.get_text()
                    
                    # Extract authors with error handling
                    authors = []
                    try:
                        author_list = article.find("AuthorList")
                        if author_list:
                            for author in author_list.find_all("Author"):
                                author_parts = []
                                if last_name := author.find("LastName"):
                                    author_parts.append(last_name.get_text())
                                if fore_name := author.find("ForeName"):
                                    author_parts.append(fore_name.get_text())
                                if author_parts:
                                    authors.append(" ".join(author_parts))
                    except Exception as e:
                        self.logger.warning(f"Error extracting authors: {str(e)}")
                    
                    articles.append({
                        "pmid": pmid,
                        "title": title_elem.get_text(),
                        "abstract": abstract_elem.get_text() if abstract_elem else "",
                        "authors": ", ".join(authors),
                        "journal": journal_elem.get_text() if journal_elem else "",
                        "pub_date": pub_date_elem.get_text() if pub_date_elem else "",
                        "doi": self._extract_doi(article),
                        "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}"
                    })
                else:
                    self.logger.warning(f"Skipping article due to missing required fields")
            except Exception as e:
                self.logger.error(f"Error parsing article: {str(e)}")
                continue
                
        self.logger.info(f"Successfully parsed {len(articles)} articles from XML response")
        return articles

    def _extract_doi(self, article) -> str:
        """Extract DOI from article metadata"""
        try:
            if doi_elem := article.find("ArticleId", {"IdType": "doi"}):
                return doi_elem.get_text()
        except Exception as e:
            self.logger.warning(f"Error extracting DOI: {str(e)}")
        return ""

    def save_to_csv(self, results: List[Dict], filename: str) -> None:
        """Save results to CSV with proper path handling and error logging"""
        try:
            abs_path = os.path.abspath(filename)
            os.makedirs(os.path.dirname(abs_path), exist_ok=True)
            
            # Create DataFrame from results
            df = pd.DataFrame(results)
            
            # Define expected columns
            columns = [
                'pmid', 'title', 'authors', 'abstract',
                'journal', 'pub_date', 'doi', 'url'
            ]
            
            # If DataFrame is empty, create with expected columns
            if df.empty:
                df = pd.DataFrame(columns=columns)
                # Write empty DataFrame with headers
                df.to_csv(abs_path, index=False)
                self.logger.info(f"Created empty CSV file with headers at {abs_path}")
            else:
                # Ensure all columns exist
                for col in columns:
                    if col not in df.columns:
                        df[col] = ""
                
                # Write to CSV with header only if file doesn't exist
                df.to_csv(
                    abs_path,
                    mode='a' if os.path.exists(abs_path) else 'w',
                    index=False,
                    header=not os.path.exists(abs_path),
                    columns=columns
                )
                self.logger.info(f"Saved {len(results)} records to {abs_path}")
        except Exception as e:
            self.logger.error(f"Failed to save CSV: {str(e)}")
            # Don't raise the exception to prevent search failure
