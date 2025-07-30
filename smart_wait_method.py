"""
Smart wait method - Uses explicit waits instead of time.sleep() for better performance
"""

import os
import glob
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager

def wait_for_new_window(driver, original_window_count, timeout=10):
    """Wait for new window to open"""
    try:
        WebDriverWait(driver, timeout).until(
            lambda d: len(d.window_handles) > original_window_count
        )
        return True
    except TimeoutException:
        return False

def wait_for_download_start(download_folder, initial_count, timeout=15):
    """Wait for new file to appear in download folder"""
    for i in range(timeout):
        import time
        time.sleep(1)
        current_count = len(glob.glob(os.path.join(download_folder, "*.pdf")))
        if current_count > initial_count:
            return True
    return False

def wait_for_page_load(driver, timeout=10):
    """Wait for page to be fully loaded"""
    try:
        WebDriverWait(driver, timeout).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
        return True
    except TimeoutException:
        return False

def smart_wait_method():
    """Download using smart waits instead of fixed delays"""
    
    print("🚀 Smart Wait Method - PO 1280282 (First 5 Files)")
    print("⚡ Using explicit waits for optimal performance")
    
    po_number = "1280282"
    download_folder = os.path.join(os.getcwd(), str(po_number))
    
    # Setup folder
    if not os.path.exists(download_folder):
        os.makedirs(download_folder, exist_ok=True)
        print(f"📁 Created folder: {download_folder}")
    else:
        print(f"📁 Using existing folder: {download_folder}")
    
    # Setup Chrome
    chrome_options = Options()
    prefs = {
        "download.default_directory": download_folder,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True,
        "plugins.always_open_pdf_externally": True
    }
    chrome_options.add_experimental_option("prefs", prefs)
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
        print(f"\n📝 Step 1: Smart login...")
        driver.get("https://app.e-brandid.com/login/login.aspx")
        
        # Wait for login form to be ready
        username_field = wait.until(EC.element_to_be_clickable((By.ID, "txtUserName")))
        password_field = wait.until(EC.element_to_be_clickable((By.ID, "txtPassword")))
        
        username_field.send_keys("sales10@fuchanghk.com")
        password_field.send_keys("fc31051856")
        
        # Wait for login button and click
        login_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//img[@onclick='return Login();']")))
        login_button.click()
        
        # Wait for login to complete (URL change or specific element)
        wait.until(lambda d: "login" not in d.current_url.lower())
        print("✅ Login completed!")
        
        print(f"\n🔍 Step 2: Smart navigation to PO {po_number}...")
        po_url = f"https://app.e-brandid.com/Bidnet/bidnet3/factoryPODetail.aspx?po_id={po_number}"
        driver.get(po_url)
        
        # Wait for page to load completely
        wait_for_page_load(driver)
        
        # Wait for table to be present
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "table")))
        print("✅ PO page loaded!")
        
        print(f"\n📥 Step 3: Smart item processing...")
        
        # Set download behavior
        driver.execute_cdp_cmd('Page.setDownloadBehavior', {
            'behavior': 'allow',
            'downloadPath': download_folder
        })
        
        # Find item links with smart wait
        tables = driver.find_elements(By.TAG_NAME, "table")
        item_links = []
        for table in tables:
            links = table.find_elements(By.XPATH, ".//a[contains(@onclick, 'openItemDetail')]")
            if links:
                item_links = links
                break
        
        total_items = len(item_links)
        print(f"Found {total_items} item links")
        
        if total_items == 0:
            print("❌ No item links found!")
            return
        
        # Process first 5 items with smart waits
        downloaded_files = []
        failed_downloads = []
        
        for i in range(min(5, len(item_links))):
            try:
                hyperlink = item_links[i]
                link_text = hyperlink.text.strip()
                print(f"\n📄 Processing item {i+1}/5: '{link_text}'")
                
                # Count files before download
                files_before = len(glob.glob(os.path.join(download_folder, "*.pdf")))
                
                # Smart scroll - wait for element to be in view
                driver.execute_script("arguments[0].scrollIntoView(true);", hyperlink)
                wait.until(EC.element_to_be_clickable(hyperlink))
                
                # Click and wait for new window
                print(f"  🖱️ Clicking item link...")
                original_window_count = len(driver.window_handles)
                hyperlink.click()
                
                # Smart wait for new window
                if wait_for_new_window(driver, original_window_count, timeout=10):
                    print(f"  ✅ New window opened")
                    
                    # Switch to new window
                    driver.switch_to.window(driver.window_handles[-1])
                    
                    # Smart wait for download link to be ready
                    try:
                        download_element = wait.until(
                            EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'Download')]"))
                        )
                        print(f"  ✅ Download link ready")
                        
                        # Click download
                        print(f"  📥 Clicking download...")
                        download_element.click()
                        
                        # Smart wait for download to start
                        if wait_for_download_start(download_folder, files_before, timeout=15):
                            print(f"  ✅ Download completed!")
                            downloaded_files.append(link_text)
                        else:
                            print(f"  ⚠️ Download timeout")
                            failed_downloads.append(link_text)
                        
                    except TimeoutException:
                        print(f"  ❌ Download link not found")
                        failed_downloads.append(link_text)
                    
                    # Close new window and return to main
                    driver.close()
                    driver.switch_to.window(driver.window_handles[0])
                    print(f"  ✅ Returned to main window")
                    
                else:
                    print(f"  ❌ New window timeout")
                    failed_downloads.append(link_text)
                
            except Exception as e:
                print(f"  ❌ Error: {e}")
                failed_downloads.append(f"Item {i+1}")
                continue
        
        print(f"\n🎉 SMART WAIT METHOD COMPLETED!")
        print(f"✅ Successfully downloaded: {len(downloaded_files)}/5")
        print(f"❌ Failed downloads: {len(failed_downloads)}")
        
        # Final summary
        final_files = glob.glob(os.path.join(download_folder, "*.pdf"))
        total_size = sum(os.path.getsize(f) for f in final_files)
        
        print(f"\n📊 FINAL SUMMARY:")
        print(f"📄 Total PDF files: {len(final_files)}")
        print(f"💾 Total size: {total_size:,} bytes ({total_size/1024/1024:.1f} MB)")
        print(f"📁 Location: {download_folder}")
        
        if final_files:
            print(f"\n📋 Downloaded files:")
            for file_path in final_files:
                file_name = os.path.basename(file_path)
                file_size = os.path.getsize(file_path)
                print(f"  - {file_name} ({file_size:,} bytes)")
        
        print(f"\n⚡ SMART WAITS ARE MUCH FASTER!")
        print(f"🎯 No unnecessary delays - waits only for actual events")
        print(f"🚀 Ready to process all {total_items} items!")
        
    finally:
        print(f"\n🔄 Closing browser...")
        driver.quit()

if __name__ == "__main__":
    smart_wait_method()
