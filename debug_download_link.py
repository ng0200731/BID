"""
Debug script to inspect the download link behavior
"""

import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

def debug_download_link():
    """Debug what exactly happens with the download link"""
    
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
        print("=== LOGGING IN ===")
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
        
        print("✅ Login successful")
        
        print("\n=== NAVIGATING TO PO PAGE ===")
        po_url = "https://app.e-brandid.com/Bidnet/bidnet3/factoryPODetail.aspx?po_id=1288060"
        driver.get(po_url)
        time.sleep(5)
        
        print("✅ PO page loaded")
        
        print("\n=== FINDING FIRST ITEM LINK ===")
        
        # Find item links
        tables = driver.find_elements(By.TAG_NAME, "table")
        item_links = []
        for table in tables:
            links = table.find_elements(By.XPATH, ".//a[contains(@onclick, 'openItemDetail')]")
            if links:
                item_links = links
                break
        
        if not item_links:
            print("❌ No item links found!")
            return
        
        # Click first item
        first_link = item_links[0]
        link_text = first_link.text.strip()
        onclick_attr = first_link.get_attribute('onclick')
        
        print(f"First item: '{link_text}' with onclick: {onclick_attr}")
        
        # Click the item link
        driver.execute_script("arguments[0].scrollIntoView(true);", first_link)
        time.sleep(1)
        driver.execute_script("arguments[0].click();", first_link)
        time.sleep(3)
        
        # Switch to new window
        windows = driver.window_handles
        if len(windows) > 1:
            print(f"✅ New window opened")
            driver.switch_to.window(windows[-1])
            time.sleep(3)
            
            print(f"New window URL: {driver.current_url}")
            print(f"New window title: {driver.title}")
            
            print("\n=== ANALYZING DOWNLOAD LINK ===")
            
            # Find all links on the page
            all_links = driver.find_elements(By.TAG_NAME, "a")
            print(f"Found {len(all_links)} links on page")
            
            download_links = []
            for i, link in enumerate(all_links):
                link_text = link.text.strip()
                link_href = link.get_attribute('href')
                link_onclick = link.get_attribute('onclick')
                
                if 'download' in link_text.lower() or 'download' in str(link_href).lower():
                    download_links.append(link)
                    print(f"Download link {len(download_links)}:")
                    print(f"  Text: '{link_text}'")
                    print(f"  Href: '{link_href}'")
                    print(f"  OnClick: '{link_onclick}'")
                    print(f"  Visible: {link.is_displayed()}")
                    print(f"  Enabled: {link.is_enabled()}")
            
            if download_links:
                print(f"\n=== TESTING DOWNLOAD LINK ===")
                download_link = download_links[0]
                
                print("Before clicking download link:")
                print(f"  Current URL: {driver.current_url}")
                print(f"  Page title: {driver.title}")
                
                # Try different click methods
                print("\nTrying regular click...")
                try:
                    download_link.click()
                    time.sleep(3)
                    print("✅ Regular click successful")
                except Exception as e:
                    print(f"❌ Regular click failed: {e}")
                
                print(f"After regular click:")
                print(f"  Current URL: {driver.current_url}")
                print(f"  Page title: {driver.title}")
                
                print("\nTrying JavaScript click...")
                try:
                    driver.execute_script("arguments[0].click();", download_link)
                    time.sleep(3)
                    print("✅ JavaScript click successful")
                except Exception as e:
                    print(f"❌ JavaScript click failed: {e}")
                
                print(f"After JavaScript click:")
                print(f"  Current URL: {driver.current_url}")
                print(f"  Page title: {driver.title}")
                
                # Check for any new windows or downloads
                new_windows = driver.window_handles
                print(f"Number of windows after clicks: {len(new_windows)}")
                
                # Check if URL changed or if there are any download indicators
                href = download_link.get_attribute('href')
                if href and href != '#':
                    print(f"\nTrying direct navigation to href: {href}")
                    driver.get(href)
                    time.sleep(3)
                    print(f"After direct navigation:")
                    print(f"  Current URL: {driver.current_url}")
                    print(f"  Page title: {driver.title}")
            
            else:
                print("❌ No download links found!")
            
            print("\n=== MANUAL INSPECTION ===")
            print("Browser window is open. Please manually inspect the download link.")
            print("Try clicking it manually to see what happens.")
            print("Press Enter when you're done inspecting...")
            input()
        
        else:
            print("❌ No new window opened!")
        
    finally:
        driver.quit()

if __name__ == "__main__":
    debug_download_link()
