"""
Web Crawler Module
Handles the actual web crawling functionality.
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time
import threading
from datetime import datetime
import sqlite3

class WebCrawler:
    def __init__(self, db_connection):
        self.conn = db_connection
        self.cursor = self.conn.cursor()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
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
    
    def crawl_page(self, url, max_depth=2, delay=1, same_domain_only=True):
        """
        Crawl a single page and optionally follow links
        
        Args:
            url: Starting URL to crawl
            max_depth: Maximum depth to crawl (0 = current page only)
            delay: Delay between requests in seconds
            same_domain_only: Only crawl pages from the same domain
        """
        if not self.is_valid_url(url):
            return {"error": "Invalid URL"}
        
        crawled_urls = set()
        to_crawl = [(url, 0)]  # (url, depth)
        base_domain = self.get_domain(url) if same_domain_only else None
        results = []
        
        while to_crawl:
            current_url, depth = to_crawl.pop(0)
            
            if current_url in crawled_urls or depth > max_depth:
                continue
                
            try:
                print(f"Crawling: {current_url} (depth: {depth})")
                
                # Add delay to be polite
                if delay > 0:
                    time.sleep(delay)
                
                response = self.session.get(current_url, timeout=10)
                response.raise_for_status()
                
                # Parse the page
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Extract page information
                title = soup.find('title')
                title_text = title.get_text().strip() if title else "No title"
                
                # Extract text content (remove scripts and styles)
                for script in soup(["script", "style"]):
                    script.decompose()
                content = soup.get_text()
                
                # Clean up content
                lines = (line.strip() for line in content.splitlines())
                chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                content = ' '.join(chunk for chunk in chunks if chunk)
                
                # Limit content length
                if len(content) > 5000:
                    content = content[:5000] + "..."
                
                page_data = {
                    'url': current_url,
                    'title': title_text,
                    'content': content,
                    'status': 'success',
                    'crawled_at': datetime.now().isoformat()
                }
                
                results.append(page_data)
                crawled_urls.add(current_url)
                
                # Find links for next depth level
                if depth < max_depth:
                    links = soup.find_all('a', href=True)
                    for link in links:
                        href = link['href']
                        full_url = urljoin(current_url, href)
                        
                        if self.is_valid_url(full_url):
                            # Check domain restriction
                            if same_domain_only and base_domain:
                                if self.get_domain(full_url) != base_domain:
                                    continue
                            
                            if full_url not in crawled_urls:
                                to_crawl.append((full_url, depth + 1))
                
            except requests.RequestException as e:
                error_data = {
                    'url': current_url,
                    'title': 'Error',
                    'content': f'Failed to crawl: {str(e)}',
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
                    'status': 'error',
                    'crawled_at': datetime.now().isoformat()
                }
                results.append(error_data)
                crawled_urls.add(current_url)
        
        return results
    
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
    
    def get_user_jobs(self, user_id):
        """Get all crawl jobs for a user"""
        self.cursor.execute(
            """SELECT id, url, status, created_at, completed_at 
               FROM crawl_jobs WHERE user_id = ? 
               ORDER BY created_at DESC""",
            (user_id,)
        )
        return self.cursor.fetchall()
    
    def get_job_data(self, job_id):
        """Get all crawled data for a specific job"""
        self.cursor.execute(
            """SELECT url, title, content, crawled_at 
               FROM crawled_data WHERE job_id = ? 
               ORDER BY crawled_at""",
            (job_id,)
        )
        return self.cursor.fetchall()


class CrawlerThread(threading.Thread):
    """Thread class for running crawler in background"""
    
    def __init__(self, crawler, job_id, url, max_depth=2, delay=1, same_domain_only=True, callback=None):
        threading.Thread.__init__(self)
        self.crawler = crawler
        self.job_id = job_id
        self.url = url
        self.max_depth = max_depth
        self.delay = delay
        self.same_domain_only = same_domain_only
        self.callback = callback
        self.daemon = True
    
    def run(self):
        """Run the crawler in background"""
        try:
            # Update job status to running
            self.crawler.update_job_status(self.job_id, 'running')
            
            # Perform the crawl
            results = self.crawler.crawl_page(
                self.url, 
                max_depth=self.max_depth,
                delay=self.delay,
                same_domain_only=self.same_domain_only
            )
            
            # Save results to database
            for page_data in results:
                self.crawler.save_crawled_data(self.job_id, page_data)
            
            # Update job status to completed
            self.crawler.update_job_status(self.job_id, 'completed')
            
            # Call callback if provided
            if self.callback:
                self.callback(self.job_id, 'completed', len(results))
                
        except Exception as e:
            # Update job status to failed
            self.crawler.update_job_status(self.job_id, 'failed')
            
            # Call callback if provided
            if self.callback:
                self.callback(self.job_id, 'failed', str(e))
