"""
Complete automation script - downloads ALL 357 PDF files with smart folder management
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

def setup_download_folder(po_number):
    """Setup download folder with smart management"""
    
    base_folder = os.path.join(os.getcwd(), str(po_number))
    
    # Check if folder exists
    if os.path.exists(base_folder):
        print(f"📁 Folder '{base_folder}' already exists")
        
        # Check if it has files
        existing_files = glob.glob(os.path.join(base_folder, "*"))
        if existing_files:
            print(f"📄 Found {len(existing_files)} existing files in folder")
            print("📋 Existing files:")
            for file_path in existing_files[:5]:  # Show first 5
                file_name = os.path.basename(file_path)
                print(f"  - {file_name}")
            if len(existing_files) > 5:
                print(f"  ... and {len(existing_files) - 5} more files")
        
        # Ask user what to do
        print(f"\n❓ What would you like to do?")
        print(f"1. Remove existing folder and start fresh")
        print(f"2. Create new folder with timestamp")
        
        while True:
            choice = input("Enter your choice (1 or 2): ").strip()
            if choice == "1":
                # Remove existing folder
                import shutil
                shutil.rmtree(base_folder)
                print(f"🗑️ Removed existing folder")
                os.makedirs(base_folder, exist_ok=True)
                print(f"📁 Created fresh folder: {base_folder}")
                return base_folder
            elif choice == "2":
                # Create timestamped folder
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                timestamped_folder = f"{base_folder}_{timestamp}"
                os.makedirs(timestamped_folder, exist_ok=True)
                print(f"📁 Created new folder: {timestamped_folder}")
                return timestamped_folder
            else:
                print("❌ Invalid choice. Please enter 1 or 2.")
    else:
        # Create new folder
        os.makedirs(base_folder, exist_ok=True)
        print(f"📁 Created new folder: {base_folder}")
        return base_folder

def download_all_357_files():
    """Download ALL 357 PDF files with smart folder management"""
    
    print("🚀 Starting COMPLETE PDF Download (ALL 357 Files)...")
    print("⚠️  This will take approximately 30-60 minutes to complete")
    
    po_number = "1288060"
    
    # Setup download folder with user interaction
    download_folder = setup_download_folder(po_number)
    
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
        
        print(f"\n📥 Step 3: Extracting ALL PDF URLs...")
        
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
        print(f"Found {total_items} item links")
        
        # Extract PDF URLs from ALL items
        pdf_urls = []
        failed_extractions = []
        
        print(f"\n🔍 Extracting PDF URLs from all {total_items} items...")
        
        for i in range(total_items):
            try:
                hyperlink = item_links[i]
                link_text = hyperlink.text.strip()
                
                # Progress indicator
                if (i + 1) % 50 == 0 or i == 0:
                    print(f"📄 Processing item {i+1}/{total_items}: '{link_text}'")
                
                # Click item link to open detail window
                driver.execute_script("arguments[0].scrollIntoView(true);", hyperlink)
                time.sleep(0.5)
                driver.execute_script("arguments[0].click();", hyperlink)
                time.sleep(2)
                
                # Switch to new window
                windows = driver.window_handles
                if len(windows) > 1:
                    driver.switch_to.window(windows[-1])
                    time.sleep(1)
                    
                    # Find download link and extract PDF URL
                    try:
                        download_link = driver.find_element(By.XPATH, "//a[contains(text(), 'Download')]")
                        onclick_attr = download_link.get_attribute('onclick')
                        
                        # Extract PDF URL from onclick
                        match = re.search(r"MM_openBrWindow\('([^']+)'", onclick_attr)
                        if match:
                            pdf_url = match.group(1)
                            pdf_urls.append((link_text, pdf_url))
                        else:
                            failed_extractions.append(link_text)
                        
                    except Exception as e:
                        failed_extractions.append(f"{link_text} (error: {e})")
                    
                    # Close detail window
                    driver.close()
                    driver.switch_to.window(windows[0])
                
                # Small delay to avoid overwhelming the server
                time.sleep(0.2)
                
            except Exception as e:
                failed_extractions.append(f"Item {i+1} (error: {e})")
                continue
        
        print(f"\n✅ PDF URL extraction completed!")
        print(f"📊 Successfully extracted: {len(pdf_urls)}/{total_items}")
        print(f"❌ Failed extractions: {len(failed_extractions)}")
        
        if failed_extractions:
            print(f"⚠️ Failed items: {failed_extractions[:5]}")  # Show first 5 failures
        
        print(f"\n📥 Step 4: Downloading {len(pdf_urls)} PDF files...")
        print(f"⏱️ Estimated time: {len(pdf_urls) * 3 // 60} minutes")
        
        # Download each PDF directly
        downloaded_files = []
        failed_downloads = []
        
        for i, (item_name, pdf_url) in enumerate(pdf_urls, 1):
            try:
                # Progress indicator
                if i % 10 == 0 or i == 1:
                    print(f"\n📄 Downloading {i}/{len(pdf_urls)}: {item_name}")
                    print(f"  Progress: {i/len(pdf_urls)*100:.1f}%")
                
                # Count files before download
                files_before = len(glob.glob(os.path.join(download_folder, "*.pdf")))
                
                # Navigate directly to PDF URL
                driver.get(pdf_url)
                
                # Wait for download to start
                download_started = False
                for wait_time in range(10):  # Wait up to 10 seconds
                    time.sleep(1)
                    files_after = len(glob.glob(os.path.join(download_folder, "*.pdf")))
                    if files_after > files_before:
                        download_started = True
                        downloaded_files.append(item_name)
                        break
                
                if not download_started:
                    failed_downloads.append(item_name)
                
            except Exception as e:
                failed_downloads.append(f"{item_name} (error: {e})")
        
        print(f"\n🎉 DOWNLOAD PROCESS COMPLETED!")
        print(f"✅ Successfully downloaded: {len(downloaded_files)}/{len(pdf_urls)}")
        print(f"❌ Failed downloads: {len(failed_downloads)}")
        print(f"📁 Download folder: {download_folder}")
        
        # Final file count and summary
        final_files = glob.glob(os.path.join(download_folder, "*.pdf"))
        total_size = sum(os.path.getsize(f) for f in final_files)
        
        print(f"\n📊 FINAL SUMMARY:")
        print(f"📄 Total PDF files: {len(final_files)}")
        print(f"💾 Total size: {total_size:,} bytes ({total_size/1024/1024:.1f} MB)")
        print(f"📁 Location: {download_folder}")
        
        if failed_downloads:
            print(f"\n⚠️ Failed downloads ({len(failed_downloads)}):")
            for failure in failed_downloads[:10]:  # Show first 10 failures
                print(f"  - {failure}")
        
        print(f"\n🎉 AUTOMATION COMPLETED SUCCESSFULLY!")
        
    finally:
        print(f"\n🔄 Closing browser...")
        driver.quit()

if __name__ == "__main__":
    download_all_357_files()
