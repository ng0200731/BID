"""
Enhanced Web Crawler with Login Capability
Handles automatic login to websites before crawling protected content.
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

class LoginWebCrawler:
    def __init__(self, db_connection, headless=True):
        self.conn = db_connection
        self.cursor = self.conn.cursor()
        self.headless = headless
        self.driver = None
        self.wait_timeout = 15
        
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
    
    def login_to_website(self, login_url, username, password, username_field="username", password_field="password", login_button="login"):
        """
        Automatically login to a website
        
        Args:
            login_url: URL of the login page
            username: Username to login with
            password: Password to login with
            username_field: CSS selector or name for username field
            password_field: CSS selector or name for password field
            login_button: CSS selector or text for login button
        """
        try:
            print(f"Navigating to login page: {login_url}")
            self.driver.get(login_url)
            
            # Wait for page to load
            time.sleep(3)
            
            # Try different selectors for username field
            username_selectors = [
                f"input[name='{username_field}']",
                f"input[id='{username_field}']",
                "input[type='text']",
                "input[type='email']",
                "#username", "#user", "#email",
                ".username", ".user", ".email"
            ]
            
            username_element = None
            for selector in username_selectors:
                try:
                    username_element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    print(f"Found username field with selector: {selector}")
                    break
                except NoSuchElementException:
                    continue
            
            if not username_element:
                return False, "Could not find username field"
            
            # Try different selectors for password field
            password_selectors = [
                f"input[name='{password_field}']",
                f"input[id='{password_field}']",
                "input[type='password']",
                "#password", "#pass", "#pwd",
                ".password", ".pass", ".pwd"
            ]
            
            password_element = None
            for selector in password_selectors:
                try:
                    password_element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    print(f"Found password field with selector: {selector}")
                    break
                except NoSuchElementException:
                    continue
            
            if not password_element:
                return False, "Could not find password field"
            
            # Fill in credentials
            username_element.clear()
            username_element.send_keys(username)
            print(f"Entered username: {username}")
            
            password_element.clear()
            password_element.send_keys(password)
            print("Entered password")
            
            time.sleep(1)
            
            # Try different selectors for login button
            login_selectors = [
                f"input[value*='{login_button}']",
                f"button[type='submit']",
                f"input[type='submit']",
                f"button:contains('{login_button}')",
                ".login", ".signin", ".submit",
                "#login", "#signin", "#submit"
            ]
            
            login_element = None
            for selector in login_selectors:
                try:
                    login_element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    print(f"Found login button with selector: {selector}")
                    break
                except NoSuchElementException:
                    continue
            
            # If no button found, try finding by text
            if not login_element:
                try:
                    login_element = self.driver.find_element(By.XPATH, "//button[contains(text(), 'LOGIN')]")
                    print("Found login button by text: LOGIN")
                except NoSuchElementException:
                    try:
                        login_element = self.driver.find_element(By.XPATH, "//input[@type='submit']")
                        print("Found submit button")
                    except NoSuchElementException:
                        return False, "Could not find login button"
            
            # Click login button
            self.driver.execute_script("arguments[0].scrollIntoView(true);", login_element)
            time.sleep(1)
            login_element.click()
            print("Clicked login button")
            
            # Wait for login to complete
            time.sleep(5)
            
            # Check if login was successful (URL change or specific element)
            current_url = self.driver.current_url
            if current_url != login_url and "login" not in current_url.lower():
                print(f"Login successful! Redirected to: {current_url}")
                return True, f"Login successful, redirected to: {current_url}"
            else:
                # Check for error messages
                try:
                    error_element = self.driver.find_element(By.CSS_SELECTOR, ".error, .alert, .warning, [class*='error'], [class*='alert']")
                    error_text = error_element.text
                    return False, f"Login failed: {error_text}"
                except NoSuchElementException:
                    return False, "Login may have failed - still on login page"
            
        except Exception as e:
            return False, f"Login error: {str(e)}"
    
    def crawl_with_login(self, login_url, username, password, crawl_urls=None, max_depth=2, delay=2):
        """
        Crawl website after logging in
        
        Args:
            login_url: URL of login page
            username: Login username
            password: Login password
            crawl_urls: List of URLs to crawl after login (if None, crawl from login redirect)
            max_depth: Maximum crawling depth
            delay: Delay between requests
        """
        if not self.setup_driver():
            return {"error": "Failed to setup WebDriver"}
        
        try:
            # Step 1: Login
            login_success, login_message = self.login_to_website(login_url, username, password)
            
            if not login_success:
                return {"error": f"Login failed: {login_message}"}
            
            print(f"Login successful: {login_message}")
            
            # Step 2: Determine what to crawl
            if not crawl_urls:
                # Use current URL after login redirect
                crawl_urls = [self.driver.current_url]
            
            # Step 3: Crawl the protected content
            results = []
            crawled_urls = set()
            
            for start_url in crawl_urls:
                to_crawl = [(start_url, 0)]
                base_domain = self.get_domain(start_url)
                
                while to_crawl:
                    current_url, depth = to_crawl.pop(0)
                    
                    if current_url in crawled_urls or depth > max_depth:
                        continue
                    
                    try:
                        print(f"Crawling protected page: {current_url} (depth: {depth})")
                        
                        # Navigate to page (already logged in)
                        self.driver.get(current_url)
                        time.sleep(3)
                        
                        # Wait for content to load
                        try:
                            self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
                        except TimeoutException:
                            print(f"Timeout waiting for page: {current_url}")
                        
                        # Extract page data
                        title = self.driver.title
                        try:
                            body_element = self.driver.find_element(By.TAG_NAME, "body")
                            content = body_element.text
                        except NoSuchElementException:
                            content = "No body content found"
                        
                        # Limit content length
                        if len(content) > 15000:
                            content = content[:15000] + "..."
                        
                        page_data = {
                            'url': current_url,
                            'title': title,
                            'content': content,
                            'status': 'success',
                            'crawled_at': datetime.now().isoformat(),
                            'login_required': True
                        }
                        
                        results.append(page_data)
                        crawled_urls.add(current_url)
                        
                        # Find more links if not at max depth
                        if depth < max_depth:
                            links = self.extract_links(current_url, base_domain)
                            for link in links[:10]:  # Limit to 10 links per page
                                if link not in crawled_urls:
                                    to_crawl.append((link, depth + 1))
                        
                        # Add delay
                        if delay > 0:
                            time.sleep(delay)
                            
                    except Exception as e:
                        error_data = {
                            'url': current_url,
                            'title': 'Error',
                            'content': f'Error crawling protected page: {str(e)}',
                            'status': 'error',
                            'crawled_at': datetime.now().isoformat(),
                            'login_required': True
                        }
                        results.append(error_data)
                        crawled_urls.add(current_url)
            
            return results
            
        finally:
            self.close_driver()
    
    def extract_links(self, current_url, base_domain):
        """Extract links from current page"""
        links = []
        try:
            link_elements = self.driver.find_elements(By.TAG_NAME, "a")
            for link_element in link_elements:
                href = link_element.get_attribute("href")
                if href:
                    full_url = urljoin(current_url, href)
                    if self.is_valid_url(full_url) and self.get_domain(full_url) == base_domain:
                        links.append(full_url)
        except Exception as e:
            print(f"Error extracting links: {e}")
        return list(set(links))
    
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
        self.cursor.execute(
            """INSERT INTO crawled_data (job_id, url, title, content) 
               VALUES (?, ?, ?, ?)""",
            (job_id, page_data['url'], page_data['title'], page_data['content'])
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
