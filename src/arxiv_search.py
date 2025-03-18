import logging
from typing import List, Dict, Optional
from datetime import datetime
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import requests
from bs4 import BeautifulSoup
import pandas as pd
import os
import re
from urllib.parse import urlencode
from src.query_builder import QueryBuilder

class ArxivAPIError(Exception):
    pass

class ArXivSearch:
    def __init__(self, max_results: int = 100, qb: QueryBuilder = None):
        self.max_results = max_results
        self.logger = logging.getLogger(__name__)
        self.base_url = "http://export.arxiv.org/api/query"
        self.qb = qb or QueryBuilder()
        
    def search_with_date_filter(self, query: str, since_date: Optional[datetime] = None) -> List[Dict]:
        """Search arXiv with date filter"""
        if not since_date:
            return self.search(query)
            
        # Format the date for arXiv API (YYYYMMDD)
        date_str = since_date.strftime("%Y%m%d")
        
        # Store the original query
        original_query = query
        
        # Build and convert query
        self.qb.build()
        converted_query = self._convert_query()
        
        # Add submittedDate filter if not already present
        if "submittedDate:" not in converted_query:
            converted_query += f" AND submittedDate:[{date_str}0000 TO 30000101000000]"
        
        self.logger.info(f"Searching arXiv with date filter: {converted_query}")
        
        # Execute search with date filter
        params = {
            "search_query": converted_query,
            "start": 0,
            "max_results": self.max_results,
            "sortBy": "submittedDate",
            "sortOrder": "descending"
        }
        
        try:
            response = requests.get(f"{self.base_url}?{urlencode(params)}")
            response.raise_for_status()
            
            if response.status_code == 403:
                raise ArxivAPIError("Rate limit exceeded")
            
            # Log the response status and size
            self.logger.info(f"arXiv API response: status={response.status_code}, content_length={len(response.content)}")
            
            results = self._parse_response(response.content)
            
            # Save results to CSV
            self.save_to_csv(results, 'data/arxiv_results.csv')
            self.logger.info(f"Saved {len(results)} arXiv results to CSV")
            
            return results
            
        except Exception as e:
            self.logger.error(f"arXiv search failed: {str(e)}")
            # Create an empty CSV file to indicate the search was attempted
            self.save_to_csv([], 'data/arxiv_results.csv')
            return []

    def _convert_query(self) -> str:
        """Convert PubMed-style query to arXiv syntax"""
        arxiv_terms = []
        current_op = "AND"
        
        # First, extract and clean all terms
        cleaned_terms = []
        for term in self.qb.terms:
            if term in ("AND", "OR", "NOT"):
                cleaned_terms.append(term)
            else:
                # Remove all field tags and special characters
                clean_term = re.sub(r'\[\w+(/\w+)?\]', '', term)  # Remove field tags like [Title/Abstract]
                clean_term = re.sub(r'[\[\]{}()*]', '', clean_term).strip()  # Remove any remaining special chars
                if clean_term:
                    cleaned_terms.append(clean_term)
        
        # Now process the cleaned terms
        i = 0
        while i < len(cleaned_terms):
            term = cleaned_terms[i]
            
            # Handle boolean operators
            if term in ("AND", "OR", "NOT"):
                current_op = term
                i += 1
                continue
            
            # Check if this term contains boolean operators
            if " OR " in term or " AND " in term or " NOT " in term:
                # For terms with internal boolean operators, wrap in parentheses
                # but don't quote the individual parts
                arxiv_terms += [current_op, f'all:({term})']
            else:
                # For simple terms, quote if they contain spaces
                if ' ' in term:
                    arxiv_terms += [current_op, f'all:"{term}"']
                else:
                    arxiv_terms += [current_op, f'all:{term}']
            
            i += 1
        
        # Add date filters
        date_terms = []
        for date_filter in self.qb.filters:
            start, end = date_filter.replace("[dp]", "").split(":")
            # Exact arXiv date format from documentation
            date_terms.append(f'submittedDate:[{start}01010000 TO {end}12312400]')
        
        # Combine terms
        query = " ".join(arxiv_terms).lstrip("AND ")
        if date_terms:
            query += " AND " + " AND ".join(date_terms)
            
        self.logger.debug(f"Converted arXiv query: {query}")
        return query

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        retry=retry_if_exception_type((ArxivAPIError, requests.exceptions.RequestException))
    )
    def search(self, query: str) -> List[Dict]:
        """Search arXiv API with converted query"""
        try:
            # Build and convert query
            self.qb.build()
            converted_query = self._convert_query()
            
            self.logger.info(f"Sending arXiv query: {converted_query}")
            
            params = {
                "search_query": converted_query,
                "start": 0,
                "max_results": self.max_results,
                "sortBy": "relevance",
                "sortOrder": "descending"
            }
            
            response = requests.get(f"{self.base_url}?{urlencode(params)}")
            response.raise_for_status()
            
            if response.status_code == 403:
                raise ArxivAPIError("Rate limit exceeded")
            
            # Log the response status and size
            self.logger.info(f"arXiv API response: status={response.status_code}, content_length={len(response.content)}")
            
            results = self._parse_response(response.content)
            
            # Save results to CSV regardless of count (even if empty)
            self.save_to_csv(results, 'data/arxiv_results.csv')
            self.logger.info(f"Saved {len(results)} arXiv results to CSV")
            
            return results
            
        except Exception as e:
            self.logger.error(f"arXiv search failed: {str(e)}")
            # Create an empty CSV file to indicate the search was attempted
            self.save_to_csv([], 'data/arxiv_results.csv')
            return []

    def _parse_response(self, content: bytes) -> List[Dict]:
        try:
            soup = BeautifulSoup(content, 'xml')
            entries = soup.find_all('entry')
            
            # If no entries found, log the response content for debugging
            if not entries:
                self.logger.warning(f"No entries found in arXiv response. Response content: {content[:500]}...")
                return []
            
            results = []
            for entry in entries:
                try:
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
                except Exception as e:
                    self.logger.error(f"Error parsing entry: {str(e)}")
            
            return results
        except Exception as e:
            self.logger.error(f"Error parsing arXiv response: {str(e)}")
            return []

    def save_to_csv(self, results: List[Dict], filename: str = 'data/arxiv_results.csv') -> None:
        try:
            abs_path = os.path.abspath(filename)
            os.makedirs(os.path.dirname(abs_path), exist_ok=True)
            
            # Create DataFrame from results
            df = pd.DataFrame(results)
            
            # Define expected columns
            columns = [
                'arxiv_id', 'title', 'authors', 'published',
                'primary_category', 'pdf_url', 'abstract'
            ]
            
            # If DataFrame is empty, create with expected columns
            if df.empty:
                df = pd.DataFrame(columns=columns)
                # Write empty DataFrame with headers
                df.to_csv(abs_path, index=False)
            else:
                # Normal case with results
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
            # Don't raise the exception to prevent search failure
