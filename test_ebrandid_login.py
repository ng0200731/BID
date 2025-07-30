"""
Test script for e-brandid website with automatic login
"""

import sqlite3
from login_crawler import LoginWebCrawler

def test_ebrandid_login():
    """Test automatic login and crawling of e-brandid website"""
    
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
    
    # Initialize login crawler
    crawler = LoginWebCrawler(conn, headless=False)  # Set to False to see browser
    
    # Your e-brandid credentials
    login_url = "https://app.e-brandid.com/login/login.aspx"
    username = "sales10@fuchanghk.com"
    password = "fc31051856"
    
    print(f"Testing e-brandid login crawler...")
    print(f"Login URL: {login_url}")
    print(f"Username: {username}")
    print("This will open a browser window and attempt to login automatically...")
    
    try:
        # Crawl with automatic login
        results = crawler.crawl_with_login(
            login_url=login_url,
            username=username,
            password=password,
            crawl_urls=None,  # Will crawl from wherever login redirects
            max_depth=2,      # Crawl 2 levels deep
            delay=3           # 3 second delay between pages
        )
        
        # Check if results is an error
        if isinstance(results, dict) and 'error' in results:
            print(f"\nCrawl failed: {results['error']}")
            return
        
        print(f"\nLogin and crawl completed! Found {len(results)} page(s)")
        
        for i, result in enumerate(results, 1):
            print(f"\n--- Page {i} ---")
            print(f"URL: {result['url']}")
            print(f"Title: {result['title']}")
            print(f"Status: {result['status']}")
            print(f"Login Required: {result.get('login_required', False)}")
            print(f"Content length: {len(result['content'])} characters")
            print(f"Content preview: {result['content'][:500]}...")
            
            # Save interesting content to file for review
            if i == 1:  # Save first page content
                with open('ebrandid_content.txt', 'w', encoding='utf-8') as f:
                    f.write(f"E-BrandID Crawl Results\n")
                    f.write(f"URL: {result['url']}\n")
                    f.write(f"Title: {result['title']}\n")
                    f.write(f"Crawled: {result['crawled_at']}\n")
                    f.write("=" * 80 + "\n")
                    f.write(result['content'])
                print(f"Saved detailed content to: ebrandid_content.txt")
            
    except Exception as e:
        print(f"Error during login crawling: {e}")
    
    finally:
        conn.close()

if __name__ == "__main__":
    test_ebrandid_login()
