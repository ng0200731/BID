"""
Diagnostic downloader - Let's see what's actually happening
"""
import os
import glob
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

def setup_driver():
    """Setup Chrome driver with visible browser"""
    print("Setting up Chrome driver (visible mode)...")
    
    # Create download directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    download_dir = os.path.join(os.getcwd(), f"diagnostic_downloads_{timestamp}")
    os.makedirs(download_dir, exist_ok=True)
    
    chrome_options = Options()
    # Remove headless mode so we can see what's happening
    chrome_options.add_argument("--disable-web-security")
    chrome_options.add_argument("--allow-running-insecure-content")
    
    # Download preferences
    prefs = {
        "download.default_directory": download_dir,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": False
    }
    chrome_options.add_experimental_option("prefs", prefs)
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    print(f"📁 Download directory: {download_dir}")
    return driver, download_dir

def diagnostic_download():
    """Diagnostic download to see what's happening"""
    driver = None
    try:
        print("=== DIAGNOSTIC DOWNLOAD ===")
        print("We'll open the browser visibly so you can see what happens")
        print("=" * 50)
        
        driver, download_dir = setup_driver()
        wait = WebDriverWait(driver, 30)
        
        # Login
        print("\n🔐 Logging in...")
        driver.get("https://app.e-brandid.com/login/login.aspx")
        
        username_field = wait.until(EC.presence_of_element_located((By.ID, "txtUserName")))
        password_field = driver.find_element(By.ID, "txtPassword")
        
        username_field.send_keys("sales10@fuchanghk.com")
        password_field.send_keys("fc31051856")
        
        login_button = driver.find_element(By.XPATH, "//img[@onclick='return Login();']")
        login_button.click()
        
        wait.until(lambda d: "login" not in d.current_url.lower())
        print("✅ Login successful!")
        
        # Navigate to PO
        print("\n🔍 Navigating to PO...")
        po_url = f"https://app.e-brandid.com/Bidnet/bidnet3/factoryPODetail.aspx?po_id=1284678"
        driver.get(po_url)
        
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "table")))
        time.sleep(3)
        
        # Find items
        print("\n📋 Finding items...")
        tables = driver.find_elements(By.TAG_NAME, "table")
        item_links = []
        for table in tables:
            links = table.find_elements(By.XPATH, ".//a[contains(@onclick, 'openItemDetail')]")
            if links:
                item_links = links
                break
        
        print(f"✅ Found {len(item_links)} items")
        
        if item_links:
            print(f"\n🎯 Let's examine the first item...")
            link = item_links[0]
            
            # Get link details
            onclick_attr = link.get_attribute('onclick')
            link_text = link.text
            print(f"📝 Link text: '{link_text}'")
            print(f"📝 Onclick: {onclick_attr}")
            
            print(f"\n🖱️  Clicking first item link...")
            print(f"👀 Watch the browser - a popup should open")
            
            original_windows = len(driver.window_handles)
            driver.execute_script("arguments[0].click();", link)
            
            # Wait for popup
            popup_opened = False
            for i in range(50):  # 5 seconds
                time.sleep(0.1)
                if len(driver.window_handles) > original_windows:
                    popup_opened = True
                    break
            
            if popup_opened:
                print(f"✅ Popup opened! Switching to it...")
                driver.switch_to.window(driver.window_handles[-1])
                
                # Get current URL
                current_url = driver.current_url
                print(f"📍 Popup URL: {current_url}")
                
                # Look for download elements
                print(f"\n🔍 Looking for download elements...")
                
                # Try different selectors
                download_selectors = [
                    "//a[contains(text(), 'Download')]",
                    "//a[contains(@href, '.pdf')]",
                    "//a[contains(@onclick, 'download')]",
                    "//input[@type='button' and contains(@value, 'Download')]",
                    "//button[contains(text(), 'Download')]"
                ]
                
                download_element = None
                for selector in download_selectors:
                    try:
                        elements = driver.find_elements(By.XPATH, selector)
                        if elements:
                            download_element = elements[0]
                            print(f"✅ Found download element with selector: {selector}")
                            print(f"📝 Element text: '{download_element.text}'")
                            print(f"📝 Element tag: {download_element.tag_name}")
                            
                            # Get attributes
                            href = download_element.get_attribute('href')
                            onclick = download_element.get_attribute('onclick')
                            if href:
                                print(f"📝 Href: {href}")
                            if onclick:
                                print(f"📝 Onclick: {onclick}")
                            break
                    except:
                        continue
                
                if download_element:
                    print(f"\n🖱️  Clicking download element...")
                    print(f"👀 Watch for download to start...")
                    
                    # Check downloads before
                    files_before = glob.glob(os.path.join(download_dir, "*"))
                    print(f"📊 Files before: {len(files_before)}")
                    
                    download_element.click()
                    
                    # Wait and check for downloads
                    print(f"⏳ Waiting 10 seconds for download...")
                    time.sleep(10)
                    
                    files_after = glob.glob(os.path.join(download_dir, "*"))
                    print(f"📊 Files after: {len(files_after)}")
                    
                    if len(files_after) > len(files_before):
                        new_files = set(files_after) - set(files_before)
                        for new_file in new_files:
                            filename = os.path.basename(new_file)
                            file_size = os.path.getsize(new_file) / 1024
                            print(f"🎉 Downloaded: {filename} ({file_size:.1f} KB)")
                    else:
                        print(f"❌ No new files detected")
                        
                        # Check Chrome downloads page
                        print(f"🔍 Let's check Chrome's downloads page...")
                        driver.get("chrome://downloads/")
                        time.sleep(2)
                        
                        # Try to get download info from Chrome
                        try:
                            downloads_manager = driver.execute_script("return document.querySelector('downloads-manager')")
                            if downloads_manager:
                                print(f"📋 Chrome downloads manager found")
                            else:
                                print(f"❌ No downloads manager found")
                        except:
                            print(f"❌ Could not access downloads manager")
                
                else:
                    print(f"❌ No download element found!")
                    print(f"📋 Let's see what's in this popup...")
                    
                    # Get page source
                    page_source = driver.page_source
                    if "download" in page_source.lower():
                        print(f"✅ Page contains 'download' text")
                    else:
                        print(f"❌ Page does not contain 'download' text")
                    
                    # Look for any links
                    all_links = driver.find_elements(By.TAG_NAME, "a")
                    print(f"📋 Found {len(all_links)} links in popup:")
                    for i, link in enumerate(all_links[:5]):  # Show first 5
                        try:
                            text = link.text.strip()
                            href = link.get_attribute('href')
                            print(f"   {i+1}. '{text}' -> {href}")
                        except:
                            print(f"   {i+1}. [Error reading link]")
            
            else:
                print(f"❌ No popup window opened")
        
        print(f"\n⏸️  Pausing for 30 seconds so you can examine the browser...")
        print(f"👀 Look at the browser window to see what's happening")
        time.sleep(30)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if driver:
            print(f"\n🔚 Closing browser...")
            driver.quit()

if __name__ == "__main__":
    diagnostic_download()
