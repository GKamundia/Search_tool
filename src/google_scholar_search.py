import os
import re
import logging
import pandas as pd
import requests
from typing import List, Dict, Any, Optional
from datetime import datetime
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

class GoogleScholarAPIError(Exception):
    """Exception raised for Google Scholar API errors"""
    pass

class GoogleScholarSearch:
    """
    Class to search Google Scholar using SerpAPI
    """
    
    def __init__(self, max_results: int = 100):
        self.max_results = max_results
        self.logger = logging.getLogger(__name__)
        self.api_key = os.getenv('SERPAPI_KEY')
        
        if not self.api_key:
            self.logger.warning("No SERPAPI_KEY found in environment variables")
        
        self.base_url = "https://serpapi.com/search"
    
    def search_with_date_filter(self, query: str, since_date: Optional[datetime] = None, test_mode: bool = False) -> List[Dict]:
        """
        Search Google Scholar with date filter
        
        Args:
            query: Search query
            since_date: Only return papers published after this date
            test_mode: If True, return dummy test papers instead of making API calls
            
        Returns:
            List of paper dictionaries
        """
        if test_mode:
            # Return dummy test papers for testing
            self.logger.info(f"Running Google Scholar search in TEST MODE for query: {query}")
            return [
                {
                    'paper_id': f'test_gs_{i}',
                    'title': f'Test Google Scholar Paper {i}: {query}',
                    'abstract': f'This is a test paper for query: {query}. It contains scholarly information related to the search terms.',
                    'authors': 'Test Scholar A, Test Scholar B',
                    'year': datetime.now().year,
                    'citation_count': 42 + i,
                    'url': f'https://example.com/scholar/test{i}',
                    'pdf_url': f'https://example.com/scholar/test{i}.pdf',
                    'database': 'google_scholar'
                }
                for i in range(1, 6)  # Generate 5 test papers
            ]
        
        if not since_date:
            return self.search(query)
            
        # Format the date for Google Scholar API (YYYY)
        year_str = since_date.strftime("%Y")
        
        # Add date filter to query if not already present
        if "after:" not in query.lower():
            date_query = f"{query} after:{year_str}"
        else:
            # Query already has date filter, leave it as is
            date_query = query
        
        self.logger.info(f"Searching Google Scholar with date filter: {date_query}")
        
        # Execute search with date filter
        return self.search(date_query)

    @retry(
        stop=stop_after_attempt(3), 
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((GoogleScholarAPIError, requests.exceptions.RequestException))
    )
    def search(self, query: str) -> List[Dict]:
        """
        Search Google Scholar using SerpAPI
        
        Args:
            query: Search query string
            
        Returns:
            List of search result dictionaries
        """
        if not self.api_key:
            self.logger.error("Cannot search Google Scholar: No API key provided")
            return []
            
        try:
            # Initial search parameters
            params = {
                "api_key": self.api_key,
                "engine": "google_scholar",
                "q": query,
                "num": min(self.max_results, 100),  # SerpAPI limits to 100 results per page
                "hl": "en"  # Language: English
            }
            
            self.logger.info(f"Sending Google Scholar API request for query: {query}")
            
            response = requests.get(self.base_url, params=params)
            
            if response.status_code == 429:
                self.logger.error("SerpAPI rate limit exceeded")
                raise GoogleScholarAPIError("Rate limit exceeded")
                
            if response.status_code != 200:
                self.logger.error(f"SerpAPI error: {response.status_code}, {response.text}")
                raise GoogleScholarAPIError(f"API returned status code {response.status_code}")
                
            data = response.json()
            
            # Check for API errors in response
            if "error" in data:
                self.logger.error(f"SerpAPI returned error: {data['error']}")
                raise GoogleScholarAPIError(data["error"])
            
            # Extract organic results (publications)
            results = []
            if "organic_results" in data:
                for item in data["organic_results"]:
                    result = self._format_result(item)
                    results.append(result)
                
                self.logger.info(f"Found {len(results)} Google Scholar results")
                
                # Save results to CSV
                self.save_to_csv(results, 'data/google_scholar_results.csv')
                return results
            else:
                self.logger.warning("No organic results found in Google Scholar API response")
                # Create empty results file
                self.save_to_csv([], 'data/google_scholar_results.csv')
                return []
            
        except Exception as e:
            self.logger.error(f"Error while searching Google Scholar: {str(e)}")
            # Create empty results file to indicate search was attempted
            self.save_to_csv([], 'data/google_scholar_results.csv')
            return []
    
    def _format_result(self, item: Dict) -> Dict:
        """Format SerpAPI result to match application schema"""
        # Extract basic metadata
        title = item.get("title", "")
        
        # Extract and format authors
        authors = ""
        if "publication_info" in item and "authors" in item["publication_info"]:
            authors = ", ".join(item["publication_info"]["authors"])
        
        # Extract source/journal info
        source = ""
        if "publication_info" in item and "summary" in item["publication_info"]:
            source = item["publication_info"]["summary"]
        
        # Extract year
        year = ""
        if "publication_info" in item and "year" in item["publication_info"]:
            year = item["publication_info"]["year"]
        elif source:
            # Try to extract year from source string
            year_match = re.search(r'\b(19|20)\d{2}\b', source)
            if year_match:
                year = year_match.group(0)
        
        # Extract abstract (snippet)
        abstract = item.get("snippet", "")
        
        # Extract citation count
        citations = 0
        if "inline_links" in item and "cited_by" in item["inline_links"]:
            citations = item["inline_links"]["cited_by"].get("total", 0)
        
        # Extract main URL and PDF URL
        url = item.get("link", "")
        pdf_url = ""
        
        # Look for PDF link
        if "resources" in item:
            for resource in item["resources"]:
                if resource.get("file_format") == "PDF":
                    pdf_url = resource.get("link", "")
                    break
        
        # Extract DOI
        doi = self._extract_doi(item)
        
        # Create a unique paper ID
        # Since Google Scholar doesn't provide a stable ID, create one from title or DOI
        if doi:
            paper_id = doi
        else:
            # Create a hash from title
            paper_id = f"gs_{hash(title) % 10000000}"
        
        # Assemble result
        result = {
            "paper_id": paper_id,
            "title": title,
            "authors": authors,
            "year": year,
            "journal": source,
            "abstract": abstract,
            "citation_count": citations,
            "url": url,
            "pdf_url": pdf_url,
            "doi": doi,
            "database": "google_scholar"
        }
        
        return result
    
    def _extract_doi(self, item: Dict) -> str:
        """Extract DOI from Google Scholar result using various methods"""
        # Method 1: Check if DOI is in the link
        url = item.get("link", "")
        doi_match = re.search(r'10\.\d{4,9}/[-._;()/:A-Z0-9]+', url, re.IGNORECASE)
        if doi_match:
            return doi_match.group(0)
        
        # Method 2: Check in snippet (abstract)
        snippet = item.get("snippet", "")
        doi_match = re.search(r'10\.\d{4,9}/[-._;()/:A-Z0-9]+', snippet, re.IGNORECASE)
        if doi_match:
            return doi_match.group(0)
        
        # Method 3: Check in title
        title = item.get("title", "")
        doi_match = re.search(r'10\.\d{4,9}/[-._;()/:A-Z0-9]+', title, re.IGNORECASE)
        if doi_match:
            return doi_match.group(0)
        
        # Method 4: Check in publication info
        if "publication_info" in item and "summary" in item["publication_info"]:
            summary = item["publication_info"]["summary"]
            doi_match = re.search(r'10\.\d{4,9}/[-._;()/:A-Z0-9]+', summary, re.IGNORECASE)
            if doi_match:
                return doi_match.group(0)
        
        # No DOI found
        return ""
    
    def _enrich_abstract(self, result: Dict) -> Dict:
        """
        Attempt to enrich abstract by fetching from additional sources 
        when abstract is too short or missing
        """
        # Only attempt enrichment if abstract is missing or too short
        if len(result.get("abstract", "")) > 200:
            return result
            
        # Try using Crossref if DOI is available
        doi = result.get("doi", "")
        if doi:
            try:
                url = f"https://api.crossref.org/works/{doi}"
                response = requests.get(url, headers={"Accept": "application/json"})
                
                if response.status_code == 200:
                    data = response.json()
                    abstract = data.get("message", {}).get("abstract")
                    if abstract and len(abstract) > len(result.get("abstract", "")):
                        # Clean HTML tags that might be in the abstract
                        abstract = re.sub(r'<[^>]+>', '', abstract)
                        result["abstract"] = abstract
                        result["abstract_source"] = "crossref"
                        
                        self.logger.info(f"Enriched abstract from Crossref for DOI: {doi}")
                        return result
            except Exception as e:
                self.logger.warning(f"Error fetching abstract from Crossref: {e}")
        
        return result
    
    def save_to_csv(self, results: List[Dict], filename: str = 'data/google_scholar_results.csv') -> None:
        """Save results to CSV file"""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            
            # Define expected columns
            columns = [
                'paper_id', 'title', 'authors', 'year', 'journal', 
                'abstract', 'citation_count', 'url', 'pdf_url', 'doi', 'database'
            ]
            
            # If results is empty, create an empty DataFrame with the expected columns
            if not results:
                df = pd.DataFrame(columns=columns)
            else:
                df = pd.DataFrame(results)
                
                # Ensure all columns exist
                for col in columns:
                    if col not in df.columns:
                        df[col] = ""
            
            # Write to CSV with header only if file doesn't exist
            df.to_csv(
                filename,
                mode='a' if os.path.exists(filename) else 'w',
                index=False,
                header=not os.path.exists(filename),
                columns=columns
            )
            
            self.logger.info(f"Saved {len(results)} Google Scholar results to {filename}")
            
        except Exception as e:
            self.logger.error(f"Failed to save Google Scholar results to CSV: {str(e)}")