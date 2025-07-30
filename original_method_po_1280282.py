"""
Original reliable method for PO 1280282 - First 10 files using popup clicking
"""

import os
import time
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

def original_method_po_1280282():
    """Download first 10 files from PO 1280282 using original popup method"""
    
    print("🚀 Original Method for PO 1280282 (First 10 Files)")
    print("🔄 Using reliable popup-clicking method")
    
    po_number = "1280282"
    
    # Setup download folder
    download_folder = os.path.join(os.getcwd(), str(po_number))
    
    if os.path.exists(download_folder):
        existing_files = glob.glob(os.path.join(download_folder, "*.pdf"))
        if existing_files:
            print(f"\n📁 Folder already contains {len(existing_files)} PDF files")
            print("❓ What would you like to do?")
            print("1. Remove existing files and start fresh")
            print("2. Create new folder with timestamp")
            
            while True:
                choice = input("Enter your choice (1 or 2): ").strip()
                if choice == "1":
                    import shutil
                    shutil.rmtree(download_folder)
                    os.makedirs(download_folder, exist_ok=True)
                    print("🗑️ Removed existing files")
                    break
                elif choice == "2":
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    download_folder = f"{download_folder}_{timestamp}"
                    os.makedirs(download_folder, exist_ok=True)
                    print(f"📁 Created new folder: {download_folder}")
                    break
                else:
                    print("❌ Invalid choice. Please enter 1 or 2.")
    else:
        os.makedirs(download_folder, exist_ok=True)
        print(f"📁 Created new folder: {download_folder}")
    
    # Setup Chrome with download preferences
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
    
    # Setup driver
    try:
        driver_path = ChromeDriverManager().install()
        service = Service(driver_path)
        driver = webdriver.Chrome(service=service, options=chrome_options)
    except:
        driver = webdriver.Chrome(options=chrome_options)
    
    wait = WebDriverWait(driver, 15)
    
    try:
        print(f"\n📝 Step 1: Logging in...")
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
        
        print(f"\n🔍 Step 2: Navigating to PO {po_number}...")
        po_url = f"https://app.e-brandid.com/Bidnet/bidnet3/factoryPODetail.aspx?po_id={po_number}"
        driver.get(po_url)
        time.sleep(5)
        print("✅ Navigation successful!")
        
        print(f"\n📥 Step 3: Finding and downloading files using original method...")
        
        # Set download behavior
        driver.execute_cdp_cmd('Page.setDownloadBehavior', {
            'behavior': 'allow',
            'downloadPath': download_folder
        })
        
        # Find all tables and look for the one with item links
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
        
        # Process first 10 items using original popup method
        downloaded_files = []
        failed_downloads = []
        
        for i in range(min(10, len(item_links))):
            try:
                hyperlink = item_links[i]
                link_text = hyperlink.text.strip()
                print(f"\n📄 Processing item {i+1}/10: '{link_text}'")
                
                # Count files before download
                files_before = len(glob.glob(os.path.join(download_folder, "*.pdf")))
                
                # Scroll to element
                driver.execute_script("arguments[0].scrollIntoView(true);", hyperlink)
                time.sleep(1)
                
                # Click the hyperlink (opens new window)
                print(f"  🖱️ Clicking item link...")
                driver.execute_script("arguments[0].click();", hyperlink)
                time.sleep(3)
                
                # Check for new window
                windows = driver.window_handles
                if len(windows) > 1:
                    print(f"  ✅ New window opened, switching to it...")
                    
                    # Switch to new window
                    driver.switch_to.window(windows[-1])
                    time.sleep(2)
                    
                    # Look for download link in new window
                    try:
                        download_element = driver.find_element(By.XPATH, "//a[contains(text(), 'Download')]")
                        print(f"  ✅ Found download link")
                        
                        # Click download
                        print(f"  📥 Clicking download...")
                        driver.execute_script("arguments[0].click();", download_element)
                        time.sleep(3)
                        
                        # Wait for download to complete
                        print(f"  ⏳ Waiting for download to complete...")
                        download_started = False
                        for wait_time in range(15):  # Wait up to 15 seconds
                            time.sleep(1)
                            files_after = len(glob.glob(os.path.join(download_folder, "*.pdf")))
                            if files_after > files_before:
                                download_started = True
                                print(f"  ✅ Download completed!")
                                downloaded_files.append(link_text)
                                break
                        
                        if not download_started:
                            print(f"  ⚠️ Download may not have started")
                            failed_downloads.append(link_text)
                        
                    except NoSuchElementException:
                        print(f"  ❌ Could not find download link in new window")
                        failed_downloads.append(link_text)
                    
                    # Close new window and return to main window
                    driver.close()
                    driver.switch_to.window(windows[0])
                    print(f"  ✅ Closed new window, returned to main window")
                    
                else:
                    print(f"  ❌ No new window opened")
                    failed_downloads.append(link_text)
                
                time.sleep(2)  # Small delay between items
                
            except Exception as e:
                print(f"  ❌ Error processing item {i+1}: {e}")
                failed_downloads.append(f"Item {i+1}")
                continue
        
        print(f"\n🎉 DOWNLOAD PROCESS COMPLETED!")
        print(f"✅ Successfully downloaded: {len(downloaded_files)}/10")
        print(f"❌ Failed downloads: {len(failed_downloads)}")
        print(f"📁 Download folder: {download_folder}")
        
        # Final file count and summary
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
        
        if failed_downloads:
            print(f"\n⚠️ Failed downloads:")
            for failure in failed_downloads:
                print(f"  - {failure}")
        
        print(f"\n🎉 PO {po_number} TEST COMPLETED!")
        print(f"🔄 Original method is more reliable for session management")
        print(f"🚀 Ready to process all {total_items} items if needed!")
        
    finally:
        print(f"\n🔄 Closing browser...")
        driver.quit()

if __name__ == "__main__":
    original_method_po_1280282()
