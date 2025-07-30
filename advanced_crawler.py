"""
Advanced Web Crawler with JavaScript Support and Interactive Features
Handles dynamic content, clicking elements, and form interactions.
"""

import time
import json
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
from urllib.parse import urljoin, urlparse
import sqlite3

class AdvancedWebCrawler:
    def __init__(self, db_connection, headless=True):
        self.conn = db_connection
        self.cursor = self.conn.cursor()
        self.headless = headless
        self.driver = None
        self.wait_timeout = 10
        
    def setup_driver(self):
        """Setup Chrome WebDriver with options"""
        try:
            chrome_options = Options()
            if self.headless:
                chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
            
            # Install and setup ChromeDriver automatically
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.wait = WebDriverWait(self.driver, self.wait_timeout)
            return True
        except Exception as e:
            print(f"Failed to setup WebDriver: {e}")
            return False
    
    def close_driver(self):
        """Close the WebDriver"""
        if self.driver:
            self.driver.quit()
            self.driver = None
    
    def crawl_page_advanced(self, url, max_depth=2, delay=2, same_domain_only=True, 
                           click_elements=True, wait_for_load=3):
        """
        Advanced crawl with JavaScript support and element interaction
        
        Args:
            url: Starting URL
            max_depth: Maximum depth to crawl
            delay: Delay between requests
            same_domain_only: Only crawl same domain
            click_elements: Whether to click on interactive elements
            wait_for_load: Seconds to wait for page load
        """
        if not self.setup_driver():
            return {"error": "Failed to setup WebDriver"}
        
        try:
            crawled_urls = set()
            to_crawl = [(url, 0)]
            base_domain = self.get_domain(url) if same_domain_only else None
            results = []
            
            while to_crawl:
                current_url, depth = to_crawl.pop(0)
                
                if current_url in crawled_urls or depth > max_depth:
                    continue
                
                try:
                    print(f"Crawling: {current_url} (depth: {depth})")
                    
                    # Navigate to page
                    self.driver.get(current_url)
                    
                    # Wait for page to load
                    time.sleep(wait_for_load)
                    
                    # Wait for body element to be present
                    try:
                        self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
                    except TimeoutException:
                        print(f"Timeout waiting for page to load: {current_url}")
                    
                    # Get page information
                    title = self.driver.title
                    page_source = self.driver.page_source
                    
                    # Extract text content
                    try:
                        body_element = self.driver.find_element(By.TAG_NAME, "body")
                        content = body_element.text
                    except NoSuchElementException:
                        content = "No body content found"
                    
                    # Interact with page elements if requested
                    interactions = []
                    if click_elements and depth < max_depth:
                        interactions = self.interact_with_elements()
                    
                    # Limit content length
                    if len(content) > 10000:
                        content = content[:10000] + "..."
                    
                    page_data = {
                        'url': current_url,
                        'title': title,
                        'content': content,
                        'interactions': interactions,
                        'status': 'success',
                        'crawled_at': datetime.now().isoformat(),
                        'page_source_length': len(page_source)
                    }
                    
                    results.append(page_data)
                    crawled_urls.add(current_url)
                    
                    # Find links for next depth
                    if depth < max_depth:
                        links = self.extract_links(current_url, base_domain, same_domain_only)
                        for link in links:
                            if link not in crawled_urls:
                                to_crawl.append((link, depth + 1))
                    
                    # Add delay
                    if delay > 0:
                        time.sleep(delay)
                        
                except WebDriverException as e:
                    error_data = {
                        'url': current_url,
                        'title': 'WebDriver Error',
                        'content': f'WebDriver error: {str(e)}',
                        'interactions': [],
                        'status': 'error',
                        'crawled_at': datetime.now().isoformat()
                    }
                    results.append(error_data)
                    crawled_urls.add(current_url)
                
                except Exception as e:
                    error_data = {
                        'url': current_url,
                        'title': 'Error',
                        'content': f'Unexpected error: {str(e)}',
                        'interactions': [],
                        'status': 'error',
                        'crawled_at': datetime.now().isoformat()
                    }
                    results.append(error_data)
                    crawled_urls.add(current_url)
            
            return results
            
        finally:
            self.close_driver()
    
    def interact_with_elements(self):
        """Interact with clickable elements on the page"""
        interactions = []
        
        try:
            # Find clickable elements (buttons, links with specific classes, etc.)
            clickable_selectors = [
                "button",
                "a[href]",
                "[onclick]",
                ".btn",
                ".button",
                "[role='button']",
                "input[type='submit']"
            ]
            
            for selector in clickable_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    
                    for i, element in enumerate(elements[:3]):  # Limit to first 3 elements
                        try:
                            if element.is_displayed() and element.is_enabled():
                                element_text = element.text or element.get_attribute("value") or "No text"
                                element_tag = element.tag_name
                                
                                # Scroll element into view
                                self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
                                time.sleep(1)
                                
                                # Try to click
                                element.click()
                                time.sleep(2)  # Wait for any changes
                                
                                # Record the interaction
                                interaction = {
                                    'action': 'click',
                                    'element': element_tag,
                                    'text': element_text[:100],
                                    'selector': selector,
                                    'success': True
                                }
                                interactions.append(interaction)
                                
                                # Get any new content after click
                                new_content = self.driver.find_element(By.TAG_NAME, "body").text
                                if len(new_content) > 1000:
                                    interaction['new_content_preview'] = new_content[:500] + "..."
                                
                        except Exception as e:
                            interaction = {
                                'action': 'click',
                                'element': element.tag_name if element else 'unknown',
                                'text': 'Failed to get text',
                                'selector': selector,
                                'success': False,
                                'error': str(e)
                            }
                            interactions.append(interaction)
                            
                except Exception as e:
                    print(f"Error finding elements with selector {selector}: {e}")
                    
        except Exception as e:
            print(f"Error during element interaction: {e}")
        
        return interactions
    
    def extract_links(self, current_url, base_domain, same_domain_only):
        """Extract links from current page"""
        links = []
        
        try:
            link_elements = self.driver.find_elements(By.TAG_NAME, "a")
            
            for link_element in link_elements:
                href = link_element.get_attribute("href")
                if href:
                    full_url = urljoin(current_url, href)
                    
                    if self.is_valid_url(full_url):
                        if same_domain_only and base_domain:
                            if self.get_domain(full_url) == base_domain:
                                links.append(full_url)
                        else:
                            links.append(full_url)
                            
        except Exception as e:
            print(f"Error extracting links: {e}")
        
        return list(set(links))  # Remove duplicates
    
    def is_valid_url(self, url):
        """Check if URL is valid"""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except:
            return False
    
    def get_domain(self, url):
        """Extract domain from URL"""
        return urlparse(url).netloc
    
    def save_crawl_job(self, user_id, url, status='pending'):
        """Save a new crawl job to database"""
        self.cursor.execute(
            "INSERT INTO crawl_jobs (user_id, url, status) VALUES (?, ?, ?)",
            (user_id, url, status)
        )
        self.conn.commit()
        return self.cursor.lastrowid
    
    def save_crawled_data(self, job_id, page_data):
        """Save crawled page data to database"""
        # Convert interactions to JSON string
        interactions_json = json.dumps(page_data.get('interactions', []))
        
        self.cursor.execute(
            """INSERT INTO crawled_data (job_id, url, title, content) 
               VALUES (?, ?, ?, ?)""",
            (job_id, page_data['url'], page_data['title'], 
             f"{page_data['content']}\n\n--- INTERACTIONS ---\n{interactions_json}")
        )
        self.conn.commit()
    
    def update_job_status(self, job_id, status):
        """Update crawl job status"""
        completed_at = datetime.now() if status == 'completed' else None
        self.cursor.execute(
            "UPDATE crawl_jobs SET status = ?, completed_at = ? WHERE id = ?",
            (status, completed_at, job_id)
        )
        self.conn.commit()
