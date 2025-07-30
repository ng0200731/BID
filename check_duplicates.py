"""
Check for duplicate URLs in the extraction process
"""

import re
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

def check_duplicates():
    """Check for duplicate URLs in the extraction process"""
    
    print("🔍 Checking for duplicate URLs in extraction process...")
    
    # Setup Chrome (minimal)
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
        
        print("📊 Analyzing all item links for duplicates...")
        
        # Find all item links
        item_links = driver.find_elements(By.XPATH, "//a[contains(@onclick, 'openItemDetail')]")
        print(f"Found {len(item_links)} total item links")
        
        # Extract all data
        all_data = []
        url_counts = {}
        item_code_counts = {}
        suffix_counts = {}
        
        for i, link in enumerate(item_links):
            try:
                onclick_attr = link.get_attribute('onclick')
                item_text = link.text.strip()
                
                # Extract IDs
                match = re.search(r'openItemDetail\((\d+),(\d+)\)', onclick_attr)
                if match:
                    request_id = match.group(1)
                    suffix_id = match.group(2)
                    item_code = extract_item_code(item_text)
                    direct_url = f"https://app4.brandid.com/Artwork/{item_code}_{suffix_id}.pdf"
                    
                    all_data.append({
                        'index': i,
                        'item_text': item_text,
                        'item_code': item_code,
                        'request_id': request_id,
                        'suffix_id': suffix_id,
                        'direct_url': direct_url
                    })
                    
                    # Count occurrences
                    url_counts[direct_url] = url_counts.get(direct_url, 0) + 1
                    item_code_counts[item_code] = item_code_counts.get(item_code, 0) + 1
                    suffix_counts[suffix_id] = suffix_counts.get(suffix_id, 0) + 1
                    
            except Exception as e:
                print(f"Error processing item {i}: {e}")
        
        print(f"\n📊 DUPLICATE ANALYSIS:")
        
        # Check for duplicate URLs
        duplicate_urls = {url: count for url, count in url_counts.items() if count > 1}
        print(f"🔗 Duplicate URLs: {len(duplicate_urls)}")
        
        if duplicate_urls:
            print("📋 Duplicate URLs found:")
            for url, count in list(duplicate_urls.items())[:10]:  # Show first 10
                print(f"  {count}x: {url}")
                # Show which items have this URL
                items_with_url = [d for d in all_data if d['direct_url'] == url]
                for item in items_with_url:
                    print(f"    - {item['item_text']} (index {item['index']})")
        
        # Check for duplicate item codes
        duplicate_codes = {code: count for code, count in item_code_counts.items() if count > 1}
        print(f"\n🏷️ Duplicate item codes: {len(duplicate_codes)}")
        
        if duplicate_codes:
            print("📋 Duplicate item codes found:")
            for code, count in list(duplicate_codes.items())[:10]:  # Show first 10
                print(f"  {count}x: {code}")
                items_with_code = [d for d in all_data if d['item_code'] == code]
                for item in items_with_code:
                    print(f"    - {item['item_text']} (suffix: {item['suffix_id']})")
        
        # Check for duplicate suffix IDs
        duplicate_suffixes = {suffix: count for suffix, count in suffix_counts.items() if count > 1}
        print(f"\n🔢 Duplicate suffix IDs: {len(duplicate_suffixes)}")
        
        if duplicate_suffixes:
            print("📋 Duplicate suffix IDs found:")
            for suffix, count in list(duplicate_suffixes.items())[:10]:  # Show first 10
                print(f"  {count}x: {suffix}")
                items_with_suffix = [d for d in all_data if d['suffix_id'] == suffix]
                for item in items_with_suffix:
                    print(f"    - {item['item_text']} (code: {item['item_code']})")
        
        print(f"\n📈 SUMMARY:")
        print(f"Total items: {len(all_data)}")
        print(f"Unique URLs: {len(url_counts)}")
        print(f"Unique item codes: {len(item_code_counts)}")
        print(f"Unique suffix IDs: {len(suffix_counts)}")
        
        if len(url_counts) < len(all_data):
            print(f"⚠️ WARNING: {len(all_data) - len(url_counts)} duplicate URLs detected!")
            print("This means some files will be downloaded multiple times.")
        else:
            print("✅ No duplicate URLs - each item has a unique PDF!")
        
    finally:
        driver.quit()

if __name__ == "__main__":
    import time
    check_duplicates()
