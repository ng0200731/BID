"""
Test script for the advanced crawler with JavaScript support
"""

import sqlite3
from advanced_crawler import AdvancedWebCrawler

def test_advanced_crawler():
    """Test the advanced crawler with JavaScript support"""
    
    # Create a test database connection
    conn = sqlite3.connect(':memory:')
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
    
    # Initialize advanced crawler
    crawler = AdvancedWebCrawler(conn, headless=False)  # Set to False to see browser
    
    # Test URL
    test_url = "https://app.e-brandid.com"
    
    print(f"Testing advanced crawler with URL: {test_url}")
    print("This will open a browser window and may take a minute...")
    print("The browser will interact with elements on the page.")
    
    try:
        # Crawl with JavaScript support and element interaction
        results = crawler.crawl_page_advanced(
            test_url, 
            max_depth=1,  # Start with depth 1
            delay=3,      # 3 second delay
            click_elements=True,  # Enable clicking
            wait_for_load=5       # Wait 5 seconds for page load
        )
        
        print(f"\nAdvanced crawl completed! Found {len(results)} page(s)")
        
        for i, result in enumerate(results, 1):
            print(f"\n--- Page {i} ---")
            print(f"URL: {result['url']}")
            print(f"Title: {result['title']}")
            print(f"Status: {result['status']}")
            print(f"Content length: {len(result['content'])} characters")
            print(f"Number of interactions: {len(result.get('interactions', []))}")
            
            # Show interactions
            if result.get('interactions'):
                print("Interactions performed:")
                for j, interaction in enumerate(result['interactions'][:3], 1):
                    print(f"  {j}. {interaction['action']} on {interaction['element']}: {interaction['text'][:50]}...")
                    print(f"     Success: {interaction['success']}")
            
            print(f"Content preview: {result['content'][:300]}...")
            
    except Exception as e:
        print(f"Error during advanced crawling: {e}")
    
    finally:
        conn.close()

if __name__ == "__main__":
    test_advanced_crawler()
