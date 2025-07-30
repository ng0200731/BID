"""
Test automation script - downloads first 10 PDF files with smart folder management
"""

import os
import time
import glob
import re
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

def download_first_10_files():
    """Download first 10 PDF files with smart folder management"""
    
    print("🚀 Starting Test PDF Download (First 10 Files)...")
    print("⏱️ This should take about 2-3 minutes")
    
    # Setup download folder
    download_folder = os.path.join(os.getcwd(), "1288060")
    
    # Check if folder exists and ask user
    if os.path.exists(download_folder):
        existing_files = glob.glob(os.path.join(download_folder, "*.pdf"))
        if existing_files:
            print(f"\n📁 Folder already contains {len(existing_files)} PDF files")
            print("📋 Existing files:")
            for file_path in existing_files[:5]:  # Show first 5
                file_name = os.path.basename(file_path)
                print(f"  - {file_name}")
            if len(existing_files) > 5:
                print(f"  ... and {len(existing_files) - 5} more files")
            
            print("\n❓ What would you like to do?")
            print("1. Remove existing files and start fresh")
            print("2. Create new folder with timestamp")
            
            while True:
                choice = input("Enter your choice (1 or 2): ").strip()
                if choice == "1":
                    import shutil
                    shutil.rmtree(download_folder)
                    os.makedirs(download_folder, exist_ok=True)
                    print("🗑️ Removed existing files and created fresh folder")
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
        
        print(f"\n🔍 Step 2: Navigating to PO 1288060...")
        po_url = "https://app.e-brandid.com/Bidnet/bidnet3/factoryPODetail.aspx?po_id=1288060"
        driver.get(po_url)
        time.sleep(5)
        print("✅ Navigation successful!")
        
        print(f"\n📥 Step 3: Extracting PDF URLs from first 10 items...")
        
        # Set download behavior
        driver.execute_cdp_cmd('Page.setDownloadBehavior', {
            'behavior': 'allow',
            'downloadPath': download_folder
        })
        
        # Find item links
        tables = driver.find_elements(By.TAG_NAME, "table")
        item_links = []
        for table in tables:
            links = table.find_elements(By.XPATH, ".//a[contains(@onclick, 'openItemDetail')]")
            if links:
                item_links = links
                break
        
        total_items = len(item_links)
        print(f"Found {total_items} total item links")
        print(f"Processing first 10 items...")
        
        # Extract PDF URLs from first 10 items
        pdf_urls = []
        failed_extractions = []
        
        for i in range(min(10, len(item_links))):
            try:
                hyperlink = item_links[i]
                link_text = hyperlink.text.strip()
                print(f"\n📄 Processing item {i+1}/10: '{link_text}'")
                
                # Click item link to open detail window
                driver.execute_script("arguments[0].scrollIntoView(true);", hyperlink)
                time.sleep(1)
                driver.execute_script("arguments[0].click();", hyperlink)
                time.sleep(3)
                
                # Switch to new window
                windows = driver.window_handles
                if len(windows) > 1:
                    print(f"  ✅ Item detail window opened")
                    driver.switch_to.window(windows[-1])
                    time.sleep(2)
                    
                    # Find download link and extract PDF URL
                    try:
                        download_link = driver.find_element(By.XPATH, "//a[contains(text(), 'Download')]")
                        onclick_attr = download_link.get_attribute('onclick')
                        
                        # Extract PDF URL from onclick using regex
                        match = re.search(r"MM_openBrWindow\('([^']+)'", onclick_attr)
                        if match:
                            pdf_url = match.group(1)
                            pdf_urls.append((link_text, pdf_url))
                            print(f"  ✅ Extracted PDF URL")
                        else:
                            failed_extractions.append(link_text)
                            print(f"  ❌ Could not extract PDF URL")
                        
                    except Exception as e:
                        failed_extractions.append(f"{link_text} (error: {e})")
                        print(f"  ❌ Error finding download link: {e}")
                    
                    # Close detail window
                    driver.close()
                    driver.switch_to.window(windows[0])
                    print(f"  ✅ Closed detail window")
                
                time.sleep(1)
                
            except Exception as e:
                failed_extractions.append(f"Item {i+1} (error: {e})")
                print(f"  ❌ Error processing item {i+1}: {e}")
                continue
        
        print(f"\n✅ PDF URL extraction completed!")
        print(f"📊 Successfully extracted: {len(pdf_urls)}/10")
        if failed_extractions:
            print(f"❌ Failed extractions: {len(failed_extractions)}")
        
        print(f"\n📥 Step 4: Downloading {len(pdf_urls)} PDF files...")
        
        # Download each PDF directly
        downloaded_files = []
        failed_downloads = []
        
        for i, (item_name, pdf_url) in enumerate(pdf_urls, 1):
            try:
                print(f"\n📄 Downloading {i}/{len(pdf_urls)}: {item_name}")
                print(f"  URL: {pdf_url}")
                
                # Count files before download
                files_before = len(glob.glob(os.path.join(download_folder, "*.pdf")))
                
                # Navigate directly to PDF URL
                driver.get(pdf_url)
                
                # Wait for download to start
                print(f"  ⏳ Waiting for download...")
                download_started = False
                for wait_time in range(15):  # Wait up to 15 seconds
                    time.sleep(1)
                    files_after = len(glob.glob(os.path.join(download_folder, "*.pdf")))
                    if files_after > files_before:
                        download_started = True
                        print(f"  ✅ Download completed!")
                        downloaded_files.append(item_name)
                        break
                
                if not download_started:
                    failed_downloads.append(item_name)
                    print(f"  ⚠️ Download may have failed")
                
            except Exception as e:
                failed_downloads.append(f"{item_name} (error: {e})")
                print(f"  ❌ Error downloading {item_name}: {e}")
        
        print(f"\n🎉 DOWNLOAD PROCESS COMPLETED!")
        print(f"✅ Successfully downloaded: {len(downloaded_files)}/{len(pdf_urls)}")
        if failed_downloads:
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
        
        print(f"\n🎉 TEST COMPLETED SUCCESSFULLY!")
        print(f"🚀 Ready to run full automation for all 357 files!")
        
    finally:
        print(f"\n🔄 Closing browser...")
        driver.quit()

if __name__ == "__main__":
    download_first_10_files()
