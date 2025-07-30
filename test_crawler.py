"""
Simple test script to demonstrate the crawler functionality
"""

import sqlite3
from crawler import WebCrawler

def test_crawler():
    """Test the crawler with a simple example"""
    
    # Create a test database connection
    conn = sqlite3.connect(':memory:')  # In-memory database for testing
    cursor = conn.cursor()
    
    # Create tables
    cursor.execute('''
        CREATE TABLE crawl_jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            url TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE crawled_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id INTEGER,
            url TEXT NOT NULL,
            title TEXT,
            content TEXT,
            crawled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    
    # Initialize crawler
    crawler = WebCrawler(conn)
    
    # Test URL (your specific website)
    test_url = "https://app.e-brandid.com"
    
    print(f"Testing crawler with URL: {test_url}")
    print("This may take a few seconds...")
    
    try:
        # Crawl the page (depth 0 = just the current page)
        results = crawler.crawl_page(test_url, max_depth=0, delay=1)
        
        print(f"\nCrawl completed! Found {len(results)} page(s)")
        
        for i, result in enumerate(results, 1):
            print(f"\n--- Page {i} ---")
            print(f"URL: {result['url']}")
            print(f"Title: {result['title']}")
            print(f"Status: {result['status']}")
            print(f"Content length: {len(result['content'])} characters")
            print(f"Content preview: {result['content'][:200]}...")
            
    except Exception as e:
        print(f"Error during crawling: {e}")
    
    finally:
        conn.close()

if __name__ == "__main__":
    test_crawler()
