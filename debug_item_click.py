"""
Debug script to see what happens when we click an item link
"""

import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def debug_item_click():
    """Debug what happens when clicking an item link"""
    
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
        
        print("\n=== FINDING ITEM LINKS ===")
        
        # Find all tables and look for the one with item links
        tables = driver.find_elements(By.TAG_NAME, "table")
        print(f"Found {len(tables)} tables on page")
        
        item_links = []
        for i, table in enumerate(tables):
            links = table.find_elements(By.XPATH, ".//a[contains(@onclick, 'openItemDetail')]")
            if links:
                item_links = links
                print(f"Found table {i+1} with {len(item_links)} item links")
                break
        
        if not item_links:
            print("❌ No item links found!")
            return
        
        # Test clicking the first few item links
        for i in range(min(3, len(item_links))):
            print(f"\n=== TESTING ITEM {i+1} ===")
            
            link = item_links[i]
            link_text = link.text.strip()
            onclick_attr = link.get_attribute('onclick')
            
            print(f"Item {i+1}: '{link_text}' with onclick: {onclick_attr}")
            
            # Scroll to element
            driver.execute_script("arguments[0].scrollIntoView(true);", link)
            time.sleep(1)
            
            print("Clicking item link...")
            driver.execute_script("arguments[0].click();", link)
            time.sleep(5)
            
            # Check for popups, modals, new windows
            print("Checking for popups/modals...")
            
            # Check for new windows
            windows = driver.window_handles
            print(f"Number of windows: {len(windows)}")
            
            if len(windows) > 1:
                print("New window detected! Switching to new window...")
                driver.switch_to.window(windows[-1])
                time.sleep(3)
                
                print(f"New window URL: {driver.current_url}")
                print(f"New window title: {driver.title}")
                
                # Look for download links in new window
                download_links = driver.find_elements(By.XPATH, "//a[contains(@href, 'download') or contains(text(), 'Download') or contains(text(), 'download')]")
                print(f"Found {len(download_links)} potential download links in new window")
                
                for j, dl_link in enumerate(download_links):
                    href = dl_link.get_attribute('href')
                    text = dl_link.text.strip()
                    print(f"  Download link {j+1}: Text='{text}', Href='{href}'")
                
                # Close new window and return to main window
                driver.close()
                driver.switch_to.window(windows[0])
                print("Closed new window, returned to main window")
            
            else:
                # Check for modal/popup in same window
                print("No new window. Checking for modal/popup in current window...")
                
                # Look for modal elements
                modal_selectors = [
                    ".modal",
                    ".popup",
                    ".dialog",
                    "[role='dialog']",
                    ".overlay"
                ]
                
                modal_found = False
                for selector in modal_selectors:
                    modals = driver.find_elements(By.CSS_SELECTOR, selector)
                    if modals:
                        print(f"Found modal with selector: {selector}")
                        modal_found = True
                        
                        # Look for download links in modal
                        for modal in modals:
                            download_links = modal.find_elements(By.XPATH, ".//a[contains(@href, 'download') or contains(text(), 'Download') or contains(text(), 'download')]")
                            print(f"Found {len(download_links)} download links in modal")
                            
                            for j, dl_link in enumerate(download_links):
                                href = dl_link.get_attribute('href')
                                text = dl_link.text.strip()
                                print(f"  Download link {j+1}: Text='{text}', Href='{href}'")
                        break
                
                if not modal_found:
                    print("No modal found. Checking entire page for new download links...")
                    
                    # Look for any download links on the page
                    download_links = driver.find_elements(By.XPATH, "//a[contains(@href, 'download') or contains(text(), 'Download') or contains(text(), 'download')]")
                    print(f"Found {len(download_links)} download links on page")
                    
                    for j, dl_link in enumerate(download_links):
                        href = dl_link.get_attribute('href')
                        text = dl_link.text.strip()
                        print(f"  Download link {j+1}: Text='{text}', Href='{href}'")
            
            print(f"Finished testing item {i+1}")
            time.sleep(2)
        
        print("\n=== MANUAL INSPECTION ===")
        print("Browser window is open. Please manually inspect the page.")
        print("Try clicking an item link manually to see what happens.")
        print("Press Enter when you're done inspecting...")
        input()
        
    finally:
        driver.quit()

if __name__ == "__main__":
    debug_item_click()
