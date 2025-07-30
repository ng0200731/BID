"""
Check specific items for duplicate URLs
"""

import re
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

def extract_item_code(full_text):
    """Extract item code from text like '13685CARE22437BLK' -> '13685CARE22437'"""
    match = re.match(r'(\d+[A-Z]+\d+)', full_text)
    if match:
        return match.group(1)
    return full_text

def check_specific_duplicates():
    """Check specific items that might have duplicate URLs"""
    
    print("🔍 Checking specific items for duplicate URLs...")
    
    # Setup Chrome
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    try:
        driver_path = ChromeDriverManager().install()
        service = Service(driver_path)
        driver = webdriver.Chrome(service=service, options=chrome_options)
    except:
        driver = webdriver.Chrome(options=chrome_options)
    
    wait = WebDriverWait(driver, 15)
    
    try:
        print("📝 Logging in...")
        driver.get("https://app.e-brandid.com/login/login.aspx")
        time.sleep(3)
        
        # Login
        username_field = wait.until(EC.presence_of_element_located((By.ID, "txtUserName")))
        password_field = driver.find_element(By.ID, "txtPassword")
        
        username_field.send_keys("sales10@fuchanghk.com")
        password_field.send_keys("fc31051856")
        
        login_button = driver.find_element(By.XPATH, "//img[@onclick='return Login();']")
        login_button.click()
        time.sleep(5)
        
        print("🔍 Navigating to PO page...")
        po_url = "https://app.e-brandid.com/Bidnet/bidnet3/factoryPODetail.aspx?po_id=1288060"
        driver.get(po_url)
        time.sleep(5)
        
        print("📊 Looking for 13685PRTL40035 items specifically...")
        
        # Find all item links
        item_links = driver.find_elements(By.XPATH, "//a[contains(@onclick, 'openItemDetail')]")
        
        # Look for the specific items you mentioned
        target_items = []
        all_urls = {}
        
        for i, link in enumerate(item_links):
            try:
                onclick_attr = link.get_attribute('onclick')
                item_text = link.text.strip()
                
                # Check if this is one of the items we're looking for
                if "13685PRTL40035" in item_text:
                    # Extract IDs
                    match = re.search(r'openItemDetail\((\d+),(\d+)\)', onclick_attr)
                    if match:
                        request_id = match.group(1)
                        suffix_id = match.group(2)
                        item_code = extract_item_code(item_text)
                        direct_url = f"https://app4.brandid.com/Artwork/{item_code}_{suffix_id}.pdf"
                        
                        target_items.append({
                            'item_text': item_text,
                            'item_code': item_code,
                            'request_id': request_id,
                            'suffix_id': suffix_id,
                            'direct_url': direct_url
                        })
                        
                        print(f"Found: {item_text}")
                        print(f"  Item code: {item_code}")
                        print(f"  Request ID: {request_id}")
                        print(f"  Suffix ID: {suffix_id}")
                        print(f"  Direct URL: {direct_url}")
                        print()
                
                # Also collect all URLs to check for duplicates
                match = re.search(r'openItemDetail\((\d+),(\d+)\)', onclick_attr)
                if match:
                    request_id = match.group(1)
                    suffix_id = match.group(2)
                    item_code = extract_item_code(item_text)
                    direct_url = f"https://app4.brandid.com/Artwork/{item_code}_{suffix_id}.pdf"
                    
                    if direct_url in all_urls:
                        all_urls[direct_url].append(item_text)
                    else:
                        all_urls[direct_url] = [item_text]
                        
            except Exception as e:
                continue
        
        print(f"📊 Found {len(target_items)} items with 13685PRTL40035")
        
        # Check if any of these items have the same URL
        target_urls = [item['direct_url'] for item in target_items]
        unique_target_urls = set(target_urls)
        
        print(f"🔗 Unique URLs for 13685PRTL40035 items: {len(unique_target_urls)}")
        print(f"📄 Total 13685PRTL40035 items: {len(target_items)}")
        
        if len(unique_target_urls) < len(target_items):
            print("⚠️ DUPLICATE URLs FOUND in 13685PRTL40035 items!")
            
            # Show which items have duplicate URLs
            url_counts = {}
            for item in target_items:
                url = item['direct_url']
                if url in url_counts:
                    url_counts[url].append(item)
                else:
                    url_counts[url] = [item]
            
            for url, items in url_counts.items():
                if len(items) > 1:
                    print(f"\n🔗 Duplicate URL: {url}")
                    for item in items:
                        print(f"  - {item['item_text']} (suffix: {item['suffix_id']})")
        else:
            print("✅ All 13685PRTL40035 items have unique URLs!")
        
        # Check for ANY duplicate URLs in the entire dataset
        print(f"\n🌐 CHECKING ALL ITEMS FOR DUPLICATES...")
        duplicate_urls = {url: items for url, items in all_urls.items() if len(items) > 1}
        
        print(f"🔗 Total duplicate URLs found: {len(duplicate_urls)}")
        
        if duplicate_urls:
            print(f"📋 First 10 duplicate URLs:")
            for i, (url, items) in enumerate(list(duplicate_urls.items())[:10]):
                print(f"\n{i+1}. URL: {url}")
                print(f"   Items ({len(items)}):")
                for item in items:
                    print(f"     - {item}")
        else:
            print("✅ No duplicate URLs found in entire dataset!")
        
    finally:
        driver.quit()

if __name__ == "__main__":
    check_specific_duplicates()
