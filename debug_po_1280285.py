"""
Debug script for PO 1280285 - investigate why download success is so low
"""

import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager

def debug_po_1280285():
    """Debug what happens when clicking items in PO 1280285"""
    
    print("🔍 Debugging PO 1280285 - First 5 items")
    
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
        print("\n📝 Logging in...")
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
        print("✅ Login successful!")
        
        print("\n🔍 Navigating to PO 1280285...")
        po_url = "https://app.e-brandid.com/Bidnet/bidnet3/factoryPODetail.aspx?po_id=1280285"
        driver.get(po_url)
        time.sleep(5)
        print("✅ Navigation successful!")
        
        # Find item links
        tables = driver.find_elements(By.TAG_NAME, "table")
        item_links = []
        for table in tables:
            links = table.find_elements(By.XPATH, ".//a[contains(@onclick, 'openItemDetail')]")
            if links:
                item_links = links
                break
        
        print(f"Found {len(item_links)} item links")
        
        # Debug first 5 items in detail
        for i in range(min(5, len(item_links))):
            try:
                hyperlink = item_links[i]
                link_text = hyperlink.text.strip()
                onclick_attr = hyperlink.get_attribute('onclick')
                
                print(f"\n🔍 DEBUGGING ITEM {i+1}/5: '{link_text}'")
                print(f"   OnClick: {onclick_attr}")
                
                # Scroll to element
                driver.execute_script("arguments[0].scrollIntoView(true);", hyperlink)
                time.sleep(1)
                
                # Click the hyperlink
                print(f"   🖱️ Clicking item link...")
                original_windows = len(driver.window_handles)
                hyperlink.click()
                time.sleep(5)  # Wait longer to see what happens
                
                # Check for new window
                windows = driver.window_handles
                print(f"   📊 Windows before: {original_windows}, after: {len(windows)}")
                
                if len(windows) > original_windows:
                    print(f"   ✅ New window opened!")
                    
                    # Switch to new window
                    driver.switch_to.window(windows[-1])
                    time.sleep(3)
                    
                    # Get window details
                    current_url = driver.current_url
                    page_title = driver.title
                    print(f"   📄 New window URL: {current_url}")
                    print(f"   📄 New window title: {page_title}")
                    
                    # Look for download link
                    print(f"   🔍 Looking for download link...")
                    try:
                        download_element = driver.find_element(By.XPATH, "//a[contains(text(), 'Download')]")
                        download_text = download_element.text
                        download_href = download_element.get_attribute('href')
                        download_onclick = download_element.get_attribute('onclick')
                        
                        print(f"   ✅ Found download link!")
                        print(f"      Text: '{download_text}'")
                        print(f"      Href: '{download_href}'")
                        print(f"      OnClick: '{download_onclick}'")
                        
                        # Try clicking download
                        print(f"   📥 Clicking download...")
                        download_element.click()
                        time.sleep(3)
                        
                        # Check what happened after clicking download
                        new_url = driver.current_url
                        new_title = driver.title
                        print(f"   📄 After download click - URL: {new_url}")
                        print(f"   📄 After download click - Title: {new_title}")
                        
                    except NoSuchElementException:
                        print(f"   ❌ No download link found!")
                        
                        # Let's see what's actually on the page
                        print(f"   🔍 Page content analysis:")
                        
                        # Look for any links
                        all_links = driver.find_elements(By.TAG_NAME, "a")
                        print(f"      Found {len(all_links)} total links")
                        
                        for j, link in enumerate(all_links[:5]):  # Show first 5 links
                            link_text = link.text.strip()
                            link_href = link.get_attribute('href')
                            if link_text or link_href:
                                print(f"         Link {j+1}: '{link_text}' -> {link_href}")
                        
                        # Look for any text containing "download"
                        page_source = driver.page_source.lower()
                        if "download" in page_source:
                            print(f"      ✅ Page contains 'download' text")
                        else:
                            print(f"      ❌ Page does NOT contain 'download' text")
                        
                        # Look for any buttons or inputs
                        buttons = driver.find_elements(By.TAG_NAME, "button")
                        inputs = driver.find_elements(By.TAG_NAME, "input")
                        print(f"      Found {len(buttons)} buttons, {len(inputs)} inputs")
                    
                    # Close new window and return to main
                    driver.close()
                    driver.switch_to.window(windows[0])
                    print(f"   ✅ Closed new window, returned to main")
                    
                else:
                    print(f"   ❌ No new window opened!")
                
                print(f"   ✅ Finished debugging item {i+1}")
                time.sleep(2)
                
            except Exception as e:
                print(f"   ❌ Error debugging item {i+1}: {e}")
                continue
        
        print(f"\n🎯 DEBUG COMPLETE!")
        print(f"📊 Analyzed first 5 items of PO 1280285")
        print(f"💡 This should help identify why download success is low")
        
    finally:
        print(f"\n🔄 Closing browser...")
        driver.quit()

if __name__ == "__main__":
    debug_po_1280285()
