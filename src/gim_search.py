import os
import logging
import random
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
            # First try using the JavaScript function directly
            try:
                self.logger.info(f"Attempting to set results per page to {count} using JavaScript function")
                await page.evaluate(f"change_count('{count}')")
                await page.wait_for_load_state('networkidle')
                self.logger.info(f"Set results per page to {count} using JavaScript function")
                return True
            except Exception as js_error:
                self.logger.warning(f"JavaScript approach failed: {str(js_error)}, trying fallback methods")
            
            # Look for the results per page selector as fallback
            count_selectors = [
                f'a:has-text("{count}")',
                '.count a',
                '.per-page a',
                'a[href*="count={count}"]',
                f'a[href*="javascript: change_count(\'{count}\')"]'
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
        
        # First, check if the "See more details" toggle is already ON
        try:
            self.logger.info("Checking if 'See more details' toggle is already ON")
            
            # Take a screenshot before checking toggle state
            await page.screenshot(path=f'logs/screenshots/gim_results_page_before_checking_toggle.png')
            
            # Check the toggle state using JavaScript
            toggle_already_on = False
            try:
                toggle_state = await page.evaluate("""
                    () => {
                        // Try to find the toggle checkbox
                        const toggle = document.getElementById('showDetailSwitch');
                        if (toggle) {
                            console.log('Toggle state:', toggle.checked);
                            return toggle.checked;
                        }
                        
                        // If we can't find it by ID, look for the class
                        const toggleByClass = document.querySelector('.custom-control-input');
                        if (toggleByClass) {
                            console.log('Toggle state by class:', toggleByClass.checked);
                            return toggleByClass.checked;
                        }
                        
                        // If we can't determine the state, assume it's not checked
                        return false;
                    }
                """)
                
                if toggle_state:
                    self.logger.info("'See more details' toggle is already ON, no need to click it")
                    toggle_already_on = True
                else:
                    self.logger.info("'See more details' toggle is OFF, need to activate it")
            except Exception as js_error:
                self.logger.warning(f"Failed to check toggle state: {str(js_error)}")
            
            # Only try to activate the toggle if it's not already ON
            if not toggle_already_on:
                self.logger.info("Attempting to activate global 'See more details' toggle")
                
                # Try using JavaScript to click the toggle
                toggle_activated = False
                try:
                    # Try direct getElementById approach
                    await page.evaluate("""
                        if (document.getElementById('showDetailSwitch')) {
                            document.getElementById('showDetailSwitch').click();
                            console.log('Clicked showDetailSwitch via getElementById');
                        } else if (document.querySelector('.custom-control-input')) {
                            document.querySelector('.custom-control-input').click();
                            console.log('Clicked custom-control-input via querySelector');
                        } else if (document.querySelector('label[for="showDetailSwitch"]')) {
                            document.querySelector('label[for="showDetailSwitch"]').click();
                            console.log('Clicked label for showDetailSwitch');
                        }
                    """)
                    
                    # Wait for any potential page updates after clicking the toggle
                    await asyncio.sleep(2)
                    await page.wait_for_load_state('networkidle')
                    
                    # Take a screenshot after toggling
                    await page.screenshot(path=f'logs/screenshots/gim_results_page_after_toggle.png')
                    
                    # Save the HTML content after toggling for debugging
                    os.makedirs('logs/html', exist_ok=True)
                    html_after_toggle = await page.content()
                    with open('logs/html/gim_page_after_toggle.html', 'w', encoding='utf-8') as f:
                        f.write(html_after_toggle)
                    
                    toggle_activated = True
                    self.logger.info("Successfully activated global 'See more details' toggle via JavaScript")
                except Exception as js_error:
                    self.logger.warning(f"JavaScript toggle activation failed: {str(js_error)}")
                
                # If JavaScript approach failed, try using Playwright's click method
                if not toggle_activated:
                    toggle_selectors = [
                        '#showDetailSwitch',
                        'label[for="showDetailSwitch"]',
                        '.custom-control-input',
                        '.custom-switch input'
                    ]
                    
                    for selector in toggle_selectors:
                        try:
                            if await page.locator(selector).count() > 0:
                                await page.locator(selector).click()
                                await asyncio.sleep(2)
                                await page.wait_for_load_state('networkidle')
                                toggle_activated = True
                                self.logger.info(f"Successfully activated global 'See more details' toggle via selector: {selector}")
                                break
                        except Exception as click_error:
                            self.logger.warning(f"Failed to click toggle with selector {selector}: {str(click_error)}")
                
                if toggle_activated:
                    self.logger.info("Global 'See more details' toggle activated successfully")
                else:
                    self.logger.warning("Could not activate global 'See more details' toggle")
            
            # Verify the toggle state after our actions
            try:
                final_toggle_state = await page.evaluate("""
                    () => {
                        const toggle = document.getElementById('showDetailSwitch');
                        if (toggle) return toggle.checked;
                        
                        const toggleByClass = document.querySelector('.custom-control-input');
                        if (toggleByClass) return toggleByClass.checked;
                        
                        return false;
                    }
                """)
                
                self.logger.info(f"Final 'See more details' toggle state: {final_toggle_state}")
                
                # Take a screenshot to verify the final state
                await page.screenshot(path=f'logs/screenshots/gim_results_page_final_toggle_state.png')
            except Exception as verify_error:
                self.logger.warning(f"Failed to verify final toggle state: {str(verify_error)}")
                
        except Exception as toggle_error:
            self.logger.error(f"Error handling global toggle: {str(toggle_error)}")
        
        # Try to find result items
        result_selectors = [
            '.box1[data-test="result_resource_item"]'  # Target specific result containers
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
                title_text = await item.locator('.titleArt a').first.text_content()
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
                url = await item.locator('.titleArt a').first.get_attribute('href')
                if not url or url.startswith('javascript:'):
                    self.logger.info(f"Skipping item with invalid URL: {title}")
                    continue
                
                self.logger.info(f"Processing result {i+1}: {title}")
                
                # We've already tried to activate the global toggle, but we'll check if we need to toggle for this specific item
                item_details_visible = False
                
                try:
                    # Check if this item already has abstract content visible (from the global toggle)
                    abstract_check_selectors = [
                        '.reference-detail',
                        'div:has-text("ABSTRACT")',
                        '.details .text',
                        '.record-abstract'
                    ]
                    
                    for selector in abstract_check_selectors:
                        if await item.locator(selector).count() > 0:
                            item_details_visible = True
                            self.logger.info(f"Item {i+1} already has details visible")
                            break
                    
                    # If details aren't visible, try to toggle for this specific item
                    if not item_details_visible:
                        more_details_selectors = [
                            '#showDetailSwitch',
                            'label[for="showDetailSwitch"]',
                            '.custom-control-input',
                            '.custom-switch input',
                            'a.showDetails', 
                            'button.showDetails',
                            'a:has-text("See more details")',
                            'button:has-text("See more details")',
                            '.toggle-details',
                            '.show-more'
                        ]
                        
                        for selector in more_details_selectors:
                            try:
                                if await item.locator(selector).count() > 0:
                                    await item.locator(selector).click()
                                    self.logger.info(f"Clicked item-specific 'See more details' with selector: {selector}")
                                    item_details_visible = True
                                    # Wait longer for the details to load
                                    await asyncio.sleep(2)
                                    break
                            except Exception as e:
                                self.logger.debug(f"Could not click item-specific toggle with selector {selector}: {str(e)}")
                except Exception as item_toggle_error:
                    self.logger.warning(f"Error checking/toggling item details: {str(item_toggle_error)}")
                
                # Take a screenshot after clicking "See more details"
                if item_details_visible:
                    await page.screenshot(path=f'logs/screenshots/gim_result_item_{i+1}_expanded.png')
                
                # Extract authors
                authors = []
                try:
                    author_links = await item.locator('.author a').all()
                    for author in author_links:
                        authors.append(await author.text_content())
                    authors = '; '.join(authors)
                except Exception as author_error:
                    self.logger.warning(f"Error extracting authors: {str(author_error)}")
                    authors = ""
                
                # Extract journal and publication details
                journal = ""
                publication_details = ""
                year = ""
                try:
                    ref_selector = '.reference em'
                    if await item.locator(ref_selector).count() > 0:
                        journal_text = await item.locator(ref_selector).text_content()
                        # Parse "Arch. latinoam. nutr;74(3): 199-205, oct. 2024. tab"
                        journal_parts = journal_text.split(';')
                        if journal_parts:
                            journal = journal_parts[0].strip()
                            publication_details = journal_text
                            
                            # Extract year from publication details
                            year_match = re.search(r'(19|20)\d{2}', journal_text)
                            if year_match:
                                year = year_match.group(0)
                except Exception as journal_error:
                    self.logger.warning(f"Error extracting journal info: {str(journal_error)}")
                
                # Extract database info
                database_info = ""
                try:
                    db_selector = '.dataArticle'
                    if await item.locator(db_selector).count() > 0:
                        database_info = await item.locator(db_selector).text_content()
                except Exception as db_error:
                    self.logger.warning(f"Error extracting database info: {str(db_error)}")
                
                # Extract abstract
                abstract = ""
                try:
                    abstract_selector = '.reference-detail'
                    if await item.locator(abstract_selector).count() > 0:
                        abstract_text = await item.locator(abstract_selector).text_content()
                        
                        # Extract text after ABSTRACT heading
                        abstract_match = re.search(r'ABSTRACT(.*?)(?:INTRODUCTION|OBJECTIVE|MATERIALS AND METHODS|RESULTS|CONCLUSION|REFERENCES|Subject|$)', 
                                                 abstract_text, re.DOTALL | re.IGNORECASE)
                        if abstract_match:
                            abstract = abstract_match.group(1).strip()
                        else:
                            # Fallback to all text if sections not found
                            abstract = abstract_text.strip()
                except Exception as abstract_error:
                    self.logger.warning(f"Error extracting abstract: {str(abstract_error)}")
                
                # Extract subjects/keywords
                subjects = []
                try:
                    # First check if there's a Subject(s) heading
                    subject_heading_selector = '.reference-detail h5.title2:has-text("Subject")'
                    if await item.locator(subject_heading_selector).count() > 0:
                        # Get all subject links that follow the heading
                        subject_links = await item.locator('.reference-detail h5.title2:has-text("Subject") ~ a').all()
                        for subject_link in subject_links:
                            subject_text = await subject_link.text_content()
                            if subject_text and subject_text.strip():
                                subjects.append(subject_text.strip())
                except Exception as subject_error:
                    self.logger.warning(f"Error extracting subjects: {str(subject_error)}")
                
                # Extract document ID
                doc_id = ""
                try:
                    doc_id_selector = '.doc_id'
                    if await item.locator(doc_id_selector).count() > 0:
                        doc_id = await item.locator(doc_id_selector).text_content()
                except Exception as doc_id_error:
                    self.logger.warning(f"Error extracting document ID: {str(doc_id_error)}")
                
                # Take a screenshot of the item
                await page.screenshot(path=f'logs/screenshots/gim_result_item_{i+1}.png')
                
                # Add the result with enhanced metadata
                results.append({
                    'title': title,
                    'authors': authors,
                    'journal': journal,
                    'year': year,
                    'publication_details': publication_details,
                    'database_info': database_info,
                    'abstract': abstract if abstract else "Abstract not available.",
                    'subjects': '; '.join(subjects) if subjects else "",
                    'doc_id': doc_id,
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
        os.makedirs('logs', exist_ok=True)
        with open('logs/gim_results_content.html', 'w', encoding='utf-8') as f:
            f.write(html)
        self.logger.info(f"Saved results HTML content to logs/gim_results_content.html")
        
        # Try to find result items with the specific selector
        result_items = soup.select('.box1[data-test="result_resource_item"]')
        
        if not result_items:
            # If no results found with specific selector, try other selectors
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
            
            for selector in selectors:
                items = soup.select(selector)
                if items:
                    self.logger.info(f"Found {len(items)} items with selector: {selector}")
                    result_items = items
                    break
        
        if not result_items:
            # If still no results, check if there's a "no results" message
            no_results_texts = ["no results", "no documents found", "your search did not match", "try different keywords"]
            page_text = soup.get_text().lower()
            
            for text in no_results_texts:
                if text in page_text:
                    self.logger.info(f"Found '{text}' message - confirming no results")
                    return []
        
        self.logger.info(f"Found {len(result_items)} potential result items")
        
        for item in result_items:
            try:
                # Extract title and URL
                title_elem = item.select_one('.titleArt a')
                
                if not title_elem:
                    self.logger.warning("Could not find title element in result item")
                    continue
                    
                title = title_elem.text.strip()
                url = title_elem.get('href', '')
                
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
                
                # Extract authors
                authors = ""
                author_elems = item.select('.author a')
                if author_elems:
                    authors = '; '.join([a.text.strip() for a in author_elems])
                
                # Extract journal and publication details
                journal = ""
                publication_details = ""
                year = ""
                ref_elem = item.select_one('.reference em')
                if ref_elem:
                    journal_text = ref_elem.text.strip()
                    journal_parts = journal_text.split(';')
                    if journal_parts:
                        journal = journal_parts[0].strip()
                        publication_details = journal_text
                        
                        # Extract year from publication details
                        year_match = re.search(r'(19|20)\d{2}', journal_text)
                        if year_match:
                            year = year_match.group(0)
                
                # Extract database info
                database_info = ""
                db_elem = item.select_one('.dataArticle')
                if db_elem:
                    database_info = db_elem.text.strip()
                
                # Extract abstract
                abstract = ""
                abstract_elem = item.select_one('.reference-detail')
                if abstract_elem:
                    abstract_text = abstract_elem.text.strip()
                    
                    # Extract text after ABSTRACT heading
                    abstract_match = re.search(r'ABSTRACT(.*?)(?:INTRODUCTION|OBJECTIVE|MATERIALS AND METHODS|RESULTS|CONCLUSION|REFERENCES|Subject|$)', 
                                             abstract_text, re.DOTALL | re.IGNORECASE)
                    if abstract_match:
                        abstract = abstract_match.group(1).strip()
                    else:
                        # Fallback to all text if sections not found
                        abstract = abstract_text
                
                # Extract subjects/keywords
                subjects = []
                subject_heading = item.select_one('.reference-detail h5.title2:-soup-contains("Subject")')
                if subject_heading:
                    # Get all subject links that follow the heading
                    current = subject_heading.next_sibling
                    while current and not (hasattr(current, 'name') and current.name == 'h5'):
                        if hasattr(current, 'name') and current.name == 'a':
                            subject_text = current.text.strip()
                            if subject_text:
                                subjects.append(subject_text)
                        current = current.next_sibling
                
                # Extract document ID
                doc_id = ""
                doc_id_elem = item.select_one('.doc_id')
                if doc_id_elem:
                    doc_id = doc_id_elem.text.strip()
                
                # Add the result with enhanced metadata
                results.append({
                    'title': title,
                    'authors': authors,
                    'journal': journal,
                    'year': year,
                    'publication_details': publication_details,
                    'database_info': database_info,
                    'abstract': abstract if abstract else "Abstract not available.",
                    'subjects': '; '.join(subjects) if subjects else "",
                    'doc_id': doc_id,
                    'url': url
                })
                
                if len(results) >= self.max_results:
                    break
                    
            except Exception as e:
                self.logger.error(f"Error processing result item: {str(e)}")
                continue
        
        self.logger.info(f"Found {len(results)} valid results from GIM HTML parsing")
        return results
