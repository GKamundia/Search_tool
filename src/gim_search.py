import os
import logging
import random
import time
import asyncio
import re
from typing import List, Dict
from playwright.async_api import async_playwright
from tenacity import retry, stop_after_attempt, wait_exponential

class GIMSearch:
    def __init__(self, max_results: int = 100):
        self.max_results = max_results
        self.logger = logging.getLogger(__name__)
        self.captcha_counter = 0
        self.playwright = None
        self.browser = None
        self.context = None

    async def __aenter__(self):
        await self._init_browser()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.context.close()
        await self.browser.close()
        await self.playwright.stop()

    async def _init_browser(self, headless: bool = True):
        """Initialize browser with anti-detection settings"""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=headless,
            args=["--disable-blink-features=AutomationControlled"]
        )
        
        # Check if storage state file exists, if not use default settings
        import os
        storage_state_param = {}
        if os.path.exists("gim_session.json"):
            storage_state_param["storage_state"] = "gim_session.json"
            
        self.context = await self.browser.new_context(
            user_agent=self._random_user_agent(),
            **storage_state_param
        )

    def _random_user_agent(self):
        agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36...",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15...",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36..."
        ]
        return random.choice(agents)

    def _format_query_for_gim(self, query: str) -> str:
        """Format a PubMed query for GIM search using the specific syntax that works"""
        # Use the exact format that works manually: (visceral OR leishmaniasis) AND (model*)
        
        # Extract terms with wildcards from field tags
        wildcard_terms = re.findall(r'(\w+\*)\s*(?:\[\w+(?:/\w+)?\])?', query)
        
        # Extract regular terms from field tags
        regular_terms = re.findall(r'(\b\w+\b)(?!\*)\s*(?:\[\w+(?:/\w+)?\])?', query)
        regular_terms = [term for term in regular_terms if term.lower() not in ('and', 'or', 'not')]
        
        self.logger.info(f"Extracted terms: regular={regular_terms}, wildcard={wildcard_terms}")
        
        # Build the query in the format that works
        formatted_query = ""
        
        # Group regular terms with OR if there are multiple
        if len(regular_terms) >= 2:
            formatted_query = f"({regular_terms[0]} OR {regular_terms[1]})"
        elif len(regular_terms) == 1:
            formatted_query = f"({regular_terms[0]})"
        
        # Add wildcard terms with AND
        if wildcard_terms and formatted_query:
            formatted_query += f" AND ({wildcard_terms[0]})"
        elif wildcard_terms:
            formatted_query = f"({wildcard_terms[0]})"
        
        # If no terms were extracted, use a simplified version of the original query
        if not formatted_query:
            # Remove field tags and use the raw query
            simplified = re.sub(r'\[\w+(/\w+)?\]', '', query).strip()
            formatted_query = simplified
        
        self.logger.info(f"Formatted query for GIM: '{formatted_query}' (original: '{query}')")
        return formatted_query

    async def _try_direct_search_url(self, query: str) -> List[Dict]:
        """Try a direct search URL approach as a fallback"""
        page = await self.context.new_page()
        try:
            # Encode the query for URL
            encoded_query = query.replace(' ', '+')
            
            # Try direct search URL
            direct_url = f"https://pesquisa.bvsalud.org/gim/?output=site&lang=en&from=0&sort=&format=summary&count=20&fb=&page=1&q={encoded_query}"
            self.logger.info(f"Trying direct search URL: {direct_url}")
            
            await page.goto(direct_url, timeout=60000)
            self.logger.info("Navigated to direct search URL")
            
            # Save screenshot for debugging
            await page.screenshot(path=f'logs/screenshots/gim_direct_search_page.png')
            
            # Wait a moment for results to load
            await asyncio.sleep(3)
            
            # Save the page content
            html_content = await page.content()
            with open('logs/gim_direct_search_content.html', 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            # Try to parse results using the browser-based approach first
            results = await self._parse_results_with_browser(page)
            
            # If no results found, fall back to HTML parsing
            if not results:
                self.logger.info("No results found with browser parsing in direct URL, trying HTML parsing")
                results = await self._parse_results(html_content)
                
            return results
            
        except Exception as e:
            self.logger.error(f"Direct search URL approach failed: {str(e)}")
            return []
        finally:
            await page.close()

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def search(self, query: str) -> List[Dict]:
        """Search Global Index Medicus website using the BVS search"""
        page = await self.context.new_page()
        try:
            # Format the query for GIM
            gim_query = self._format_query_for_gim(query)
            self.logger.info(f"Starting GIM search with query: {gim_query}")
            
            # Use the basic search instead of advanced for simplicity
            await page.goto("https://pesquisa.bvsalud.org/gim/?lang=en", timeout=60000)
            self.logger.info("Navigated to GIM search page")
            
            # Save screenshot for debugging
            os.makedirs('logs/screenshots', exist_ok=True)
            await page.screenshot(path=f'logs/screenshots/gim_search_page.png')
            
            # Handle potential CAPTCHA
            if "CAPTCHA" in await page.content():
                self.logger.warning("CAPTCHA detected, retrying...")
                raise Exception("CAPTCHA challenge detected")

            # Log the page content to understand its structure
            html_content = await page.content()
            with open('logs/gim_page_content.html', 'w', encoding='utf-8') as f:
                f.write(html_content)
            self.logger.info("Saved page content to logs/gim_page_content.html")
            
            # Try to find the search input - try different selectors
            search_input_selectors = [
                'input.form-control[name="q"]',
                'input[type="search"]',
                'input.searchBox',
                '#searchForm input[type="text"]'
            ]
            
            for selector in search_input_selectors:
                if await page.query_selector(selector):
                    await page.fill(selector, gim_query)
                    self.logger.info(f"Found and filled search input using selector: {selector}")
                    break
            else:
                self.logger.warning("Could not find search input, taking screenshot for debugging")
                await page.screenshot(path=f'logs/screenshots/gim_search_input_not_found.png')
                raise Exception("Could not find search input")
            
            # Try to find the search button - try different selectors
            search_button_selectors = [
                'button.searchButton',
                'button[type="submit"]',
                'input[type="submit"]',
                '#searchForm button'
            ]
            
            for selector in search_button_selectors:
                if await page.query_selector(selector):
                    await page.click(selector, timeout=30000)
                    self.logger.info(f"Found and clicked search button using selector: {selector}")
                    break
            else:
                self.logger.warning("Could not find search button, taking screenshot for debugging")
                await page.screenshot(path=f'logs/screenshots/gim_search_button_not_found.png')
                raise Exception("Could not find search button")
            
            # Wait for results with extended timeout - try different selectors
            result_selectors = [
                '.results',
                '.resultRow',
                '.media-list',
                '.searchResults',
                'article.post',
                '.item'
            ]
            
            # Try each selector with a short timeout
            for selector in result_selectors:
                try:
                    await page.wait_for_selector(selector, timeout=10000)
                    self.logger.info(f"Results page loaded, found selector: {selector}")
                    break
                except Exception:
                    continue
            else:
                # If none of the selectors worked, take a screenshot and log the issue
                self.logger.warning("Could not find results container, taking screenshot for debugging")
                await page.screenshot(path=f'logs/screenshots/gim_results_not_found.png')
                
                # Check if we're on an error page or no results page
                page_text = await page.text_content('body')
                if "no results" in page_text.lower() or "no documents" in page_text.lower():
                    self.logger.info("Search returned no results")
                    return []
                
                # Wait a bit longer for any results to appear
                await asyncio.sleep(5)
            
            # Set results per page to 100
            await self._set_results_per_page(page, 100)
            
            # Save screenshot of results page
            await page.screenshot(path=f'logs/screenshots/gim_results_page.png')
            
            # Parse the results using the browser-based approach to handle "See more details" buttons
            results = await self._parse_results_with_browser(page)
            
            # If we need more results and there are more pages, navigate to them
            if len(results) < self.max_results:
                page_num = 2
                while len(results) < self.max_results:
                    # Check if there's a next page link
                    next_page_selectors = [
                        f'a:has-text("{page_num}")',
                        'a.next',
                        'a:has-text("Next")',
                        'a[rel="next"]'
                    ]
                    
                    next_page_found = False
                    for selector in next_page_selectors:
                        if await page.query_selector(selector):
                            self.logger.info(f"Found next page link: {selector}")
                            await page.click(selector, timeout=30000)
                            await page.wait_for_load_state('networkidle')
                            self.logger.info(f"Navigated to page {page_num}")
                            
                            # Save screenshot of next page
                            await page.screenshot(path=f'logs/screenshots/gim_results_page_{page_num}.png')
                            
                            # Parse results from this page
                            page_results = await self._parse_results_with_browser(page)
                            if not page_results:
                                self.logger.info(f"No results found on page {page_num}")
                                break
                                
                            self.logger.info(f"Found {len(page_results)} results on page {page_num}")
                            results.extend(page_results)
                            
                            page_num += 1
                            next_page_found = True
                            break
                    
                    if not next_page_found or page_num > 10:  # Limit to 10 pages to avoid infinite loops
                        self.logger.info("No more pages found or reached page limit")
                        break
            
            # If no results found or if we couldn't parse with the browser, try the fallback approach
            if not results:
                self.logger.info("No results found with browser parsing, trying fallback approach")
                # Parse the results from the HTML content
                results = await self._parse_results(await page.content())
                
                # If still no results, try the direct URL approach
                if not results:
                    self.logger.info("No results found with form search, trying direct URL approach")
                    results = await self._try_direct_search_url(gim_query)
                
            return results
            
        except Exception as e:
            self.logger.error(f"GIM search failed: {str(e)}")
            
            # Try the direct URL approach as a fallback
            self.logger.info("Search failed, trying direct URL approach as fallback")
            return await self._try_direct_search_url(self._format_query_for_gim(query))
        finally:
            await page.close()
            
    async def _set_results_per_page(self, page, count: int = 100):
        """Set the number of results per page"""
        try:
            # Look for the results per page selector
            count_selectors = [
                f'a:has-text("{count}")',
                '.count a',
                '.per-page a',
                'a[href*="count={count}"]'
            ]
            
            for selector in count_selectors:
                count_link = page.locator(selector)
                if await count_link.count() > 0:
                    self.logger.info(f"Found results per page selector: {selector}")
                    await count_link.click()
                    await page.wait_for_load_state('networkidle')
                    self.logger.info(f"Set results per page to {count}")
                    return True
            
            self.logger.warning(f"Could not find results per page selector for count={count}")
            return False
        except Exception as e:
            self.logger.error(f"Error setting results per page: {str(e)}")
            return False

    async def _parse_results_with_browser(self, page) -> List[Dict]:
        """Parse results directly from the browser page, clicking 'See more details' buttons"""
        results = []
        
        # Save screenshot of results page
        await page.screenshot(path=f'logs/screenshots/gim_results_page_before_parsing.png')
        
        # Try to find result items
        result_selectors = [
            '.results .item',
            '.media-list > div',
            '.resultRow',
            '.searchResults li',
            '.record',
            '.result',
            'article.post',
            '.searchResultItem',
            'div[id^="doc"]',
            '.document'
        ]
        
        # Find which selector works for this page
        working_selector = None
        for selector in result_selectors:
            count = await page.locator(selector).count()
            if count > 0:
                self.logger.info(f"Found {count} result items with selector: {selector}")
                working_selector = selector
                break
        
        if not working_selector:
            self.logger.warning("Could not find result items on the page")
            return []
        
        # Get the count of result items
        item_count = await page.locator(working_selector).count()
        self.logger.info(f"Processing {item_count} result items")
        
        # Process each result item
        for i in range(min(item_count, self.max_results)):
            try:
                # Get the current item
                item = page.locator(working_selector).nth(i)
                
                # Extract basic information before clicking "See more details"
                title_text = await item.locator('a').first.text_content()
                title = title_text.strip()
                
                # Skip navigation elements and pagination links
                if any(skip_text in title.lower() for skip_text in [
                    'list items', 'clear list', 'page', 'next', 'previous', 'javascript:',
                    'go to', 'login', 'register', 'sign in', 'sign up'
                ]):
                    self.logger.info(f"Skipping navigation element: {title}")
                    continue
                
                # Skip items with very short titles
                if len(title) < 5:
                    self.logger.info(f"Skipping invalid result: {title}")
                    continue
                
                # Get the URL
                url = await item.locator('a').first.get_attribute('href')
                if not url or url.startswith('javascript:'):
                    self.logger.info(f"Skipping item with invalid URL: {title}")
                    continue
                
                self.logger.info(f"Processing result {i+1}: {title}")
                
                # Look for "See more details" button within this item
                more_details_selectors = [
                    'a.showDetails', 
                    'button.showDetails',
                    'a:has-text("See more details")',
                    'button:has-text("See more details")',
                    '.toggle-details',
                    '.show-more'
                ]
                
                # Try to find and click the "See more details" button
                details_clicked = False
                for selector in more_details_selectors:
                    details_button = item.locator(selector)
                    if await details_button.count() > 0:
                        try:
                            await details_button.click()
                            self.logger.info(f"Clicked 'See more details' button for item {i+1}")
                            details_clicked = True
                            # Wait a moment for the details to load
                            await asyncio.sleep(0.5)
                            break
                        except Exception as e:
                            self.logger.error(f"Error clicking 'See more details' button: {str(e)}")
                
                # Take a screenshot after clicking "See more details"
                if details_clicked:
                    await page.screenshot(path=f'logs/screenshots/gim_result_item_{i+1}_expanded.png')
                
                # Extract authors
                authors = ""
                authors_selectors = ['.authors', '.author', '.line:nth-child(2)']
                for selector in authors_selectors:
                    if await item.locator(selector).count() > 0:
                        authors = await item.locator(selector).text_content()
                        authors = authors.strip()
                        break
                
                # Extract journal
                journal = ""
                journal_selectors = ['.journalTitle', '.journal', '.source']
                for selector in journal_selectors:
                    if await item.locator(selector).count() > 0:
                        journal = await item.locator(selector).text_content()
                        journal = journal.strip()
                        break
                
                # Extract year
                year = ""
                year_selectors = ['.year', '.date', '.line:nth-child(3)']
                for selector in year_selectors:
                    if await item.locator(selector).count() > 0:
                        year_text = await item.locator(selector).text_content()
                        year_text = year_text.strip()
                        # Try to extract just the year if it's part of a longer string
                        year_match = re.search(r'(19|20)\d{2}', year_text)
                        if year_match:
                            year = year_match.group(0)
                        else:
                            year = year_text
                        break
                
                # Extract abstract - this should be visible after clicking "See more details"
                abstract = ""
                abstract_selectors = ['.abstract', '#abstract', 'div:has-text("ABSTRACT")', '.details .text', '.record-abstract']
                for selector in abstract_selectors:
                    if await item.locator(selector).count() > 0:
                        abstract_text = await item.locator(selector).text_content()
                        abstract_text = abstract_text.strip()
                        # Clean up the text
                        abstract_text = re.sub(r'ABSTRACT\s*', '', abstract_text, flags=re.IGNORECASE).strip()
                        if abstract_text:
                            abstract = abstract_text
                            break
                
                # If we still don't have an abstract, try to find it in the expanded content
                if not abstract and details_clicked:
                    # Get the entire text content of the expanded item
                    full_text = await item.text_content()
                    
                    # Look for the abstract section
                    abstract_match = re.search(r'ABSTRACT\s*(.*?)(?:INTRODUCTION|OBJECTIVE|MATERIALS AND METHODS|RESULTS|CONCLUSION|$)', 
                                              full_text, re.DOTALL | re.IGNORECASE)
                    if abstract_match:
                        abstract = abstract_match.group(1).strip()
                    else:
                        # Try another approach - look for text after "ABSTRACT" keyword
                        abstract_pos = full_text.lower().find('abstract')
                        if abstract_pos != -1:
                            abstract = full_text[abstract_pos + 8:].strip()
                            # Limit to a reasonable length
                            if len(abstract) > 500:
                                abstract = abstract[:500] + "..."
                
                # Add the result
                results.append({
                    'title': title,
                    'authors': authors,
                    'journal': journal,
                    'year': year,
                    'abstract': abstract if abstract else "Abstract not available.",
                    'url': url
                })
                
                if len(results) >= self.max_results:
                    break
                    
            except Exception as e:
                self.logger.error(f"Error processing result item {i+1}: {str(e)}")
                continue
        
        self.logger.info(f"Found {len(results)} valid results from GIM")
        return results

    async def _parse_results(self, html: str) -> List[Dict]:
        """Parse HTML content from BVS GIM search results"""
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')
        results = []
        
        # Save the HTML content for debugging
        with open('logs/gim_results_content.html', 'w', encoding='utf-8') as f:
            f.write(html)
        self.logger.info(f"Saved results HTML content to logs/gim_results_content.html")
        
        # Try multiple selectors to find result items
        selectors = [
            '.results .item',
            '.media-list > div',
            '.resultRow',
            '.searchResults li',
            '.record',
            '.result',
            'article.post',
            '.searchResultItem',
            'div[id^="doc"]',
            '.document'
        ]
        
        result_items = []
        for selector in selectors:
            items = soup.select(selector)
            if items:
                self.logger.info(f"Found {len(items)} items with selector: {selector}")
                result_items = items
                break
        
        if not result_items:
            # If no results found with standard selectors, try to find any links that might be results
            self.logger.warning("No results found with standard selectors, trying fallback approach")
            
            # Look for any div that might contain a list of results
            potential_containers = soup.select('div.results, div.searchResults, div.content, main, div.container')
            
            for container in potential_containers:
                # Look for links with titles that might be result items
                links = container.select('a[href]:not([href^="#"])')
                if len(links) > 5:  # If we find a group of links, they might be results
                    self.logger.info(f"Found {len(links)} potential result links in container")
                    
                    # Create simple result items from these links
                    result_items = []
                    for link in links:
                        # Create a simple wrapper div for each link to use with our existing parsing logic
                        wrapper = soup.new_tag('div')
                        wrapper.append(link)
                        result_items.append(wrapper)
                    break
        
        self.logger.info(f"Found {len(result_items)} potential result items")
        
        # If still no results, check if there's a "no results" message
        if not result_items:
            no_results_texts = ["no results", "no documents found", "your search did not match", "try different keywords"]
            page_text = soup.get_text().lower()
            
            for text in no_results_texts:
                if text in page_text:
                    self.logger.info(f"Found '{text}' message - confirming no results")
                    return []
        
        for item in result_items:
            try:
                # Extract title and URL - try different possible selectors
                title_elem = (item.select_one('a.result-title') or 
                             item.select_one('.line a') or 
                             item.select_one('h3 a') or
                             item.select_one('a[title]'))
                
                if not title_elem:
                    self.logger.warning("Could not find title element in result item")
                    continue
                    
                title = title_elem.text.strip()
                url = title_elem['href']
                
                # Skip navigation elements, pagination links, and other non-result items
                if any(skip_text in title.lower() for skip_text in [
                    'list items', 'clear list', 'page', 'next', 'previous', 'javascript:',
                    'go to', 'login', 'register', 'sign in', 'sign up'
                ]):
                    self.logger.info(f"Skipping navigation element: {title}")
                    continue
                
                # Skip items with very short titles or URLs that are JavaScript functions
                if len(title) < 5 or url.startswith('javascript:'):
                    self.logger.info(f"Skipping invalid result: {title} ({url})")
                    continue
                
                self.logger.debug(f"Found valid result: {title}")
                
                # Extract authors - try different possible selectors
                authors = ""
                authors_elem = (item.select_one('.authors') or 
                               item.select_one('.author') or
                               item.select_one('.line:nth-child(2)'))
                if authors_elem:
                    authors = authors_elem.text.strip()
                
                # Extract journal - try different possible selectors
                journal = ""
                journal_elem = (item.select_one('.journalTitle') or 
                               item.select_one('.journal') or
                               item.select_one('.source'))
                if journal_elem:
                    journal = journal_elem.text.strip()
                
                # Extract year - try different possible selectors
                year = ""
                year_elem = (item.select_one('.year') or 
                            item.select_one('.date') or
                            item.select_one('.line:nth-child(3)'))
                if year_elem:
                    year = year_elem.text.strip()
                    # Try to extract just the year if it's part of a longer string
                    year_match = re.search(r'(19|20)\d{2}', year)
                    if year_match:
                        year = year_match.group(0)
                
                # Extract abstract - try different possible selectors
                abstract = ""
                abstract_elem = (item.select_one('.abstract') or 
                                item.select_one('.description') or
                                item.select_one('.text'))
                if abstract_elem:
                    abstract = abstract_elem.text.strip()
                
                # Note: We'll use the browser-based parsing for abstracts instead of this method
                
                results.append({
                    'title': title,
                    'authors': authors,
                    'journal': journal,
                    'year': year,
                    'abstract': abstract if abstract else "Abstract not available.",
                    'url': url
                })
                
                if len(results) >= self.max_results:
                    break
            except Exception as e:
                self.logger.error(f"Error parsing result item: {str(e)}")
                continue
        
        # Final validation to ensure we only return valid results
        valid_results = [r for r in results if len(r['title']) > 5 and not r['url'].startswith('javascript:')]
        self.logger.info(f"Found {len(valid_results)} valid results from GIM (filtered from {len(results)} total)")
        return valid_results
