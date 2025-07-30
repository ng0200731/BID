"""
Test automation with new PO# 1280282 - First 10 files
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

def extract_item_code(full_text):
    """Extract item code from text like '13685CARE22437BLK' -> '13685CARE22437'"""
    match = re.match(r'(\d+[A-Z]+\d+)', full_text)
    if match:
        return match.group(1)
    return full_text

def test_new_po_1280282():
    """Test automation with PO# 1280282 - download first 10 files"""
    
    print("🚀 Testing New PO# 1280282 (First 10 Files)")
    print("⚡ Using super-fast direct URL method")
    
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
        start_time = time.time()
        
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
        
        # Check if PO page loaded successfully
        try:
            # Look for error messages or check if we're still on login page
            current_url = driver.current_url
            page_title = driver.title
            
            if "login" in current_url.lower():
                print("❌ Still on login page - PO might not exist or access denied")
                return
            
            print(f"✅ Navigation successful!")
            print(f"   Current URL: {current_url}")
            print(f"   Page title: {page_title}")
            
        except Exception as e:
            print(f"⚠️ Could not verify page load: {e}")
        
        print(f"\n⚡ Step 3: SUPER FAST URL EXTRACTION...")
        
        # Set download behavior
        driver.execute_cdp_cmd('Page.setDownloadBehavior', {
            'behavior': 'allow',
            'downloadPath': download_folder
        })
        
        # Find all item links with openItemDetail
        item_links = driver.find_elements(By.XPATH, "//a[contains(@onclick, 'openItemDetail')]")
        total_items = len(item_links)
        print(f"Found {total_items} total item links")
        
        if total_items == 0:
            print("⚠️ No item links found! This could mean:")
            print("   - PO number doesn't exist")
            print("   - PO has no items")
            print("   - Access permissions issue")
            print("   - Page structure is different")
            
            # Let's check what's on the page
            print(f"\n🔍 Page analysis:")
            try:
                page_source = driver.page_source
                if "no items" in page_source.lower() or "not found" in page_source.lower():
                    print("   - Page indicates no items or PO not found")
                elif "access denied" in page_source.lower() or "permission" in page_source.lower():
                    print("   - Access permission issue")
                else:
                    print("   - Unknown issue - page loaded but no item links")
            except:
                print("   - Could not analyze page content")
            
            return
        
        # Extract direct URLs for first 10 items
        print(f"🔍 Extracting direct URLs from first 10 items...")
        extraction_start = time.time()
        
        direct_urls = []
        failed_extractions = []
        
        for i in range(min(10, len(item_links))):
            try:
                link = item_links[i]
                onclick_attr = link.get_attribute('onclick')
                item_text = link.text.strip()
                
                print(f"\n📄 Item {i+1}/10: {item_text}")
                
                # Extract request_id and item_suffix_id using regex
                match = re.search(r'openItemDetail\((\d+),(\d+)\)', onclick_attr)
                
                if match:
                    request_id = match.group(1)
                    suffix_id = match.group(2)
                    item_code = extract_item_code(item_text)
                    direct_url = f"https://app4.brandid.com/Artwork/{item_code}_{suffix_id}.pdf"
                    
                    direct_urls.append((item_text, item_code, suffix_id, direct_url))
                    print(f"  ✅ Extracted: {item_code}_{suffix_id}.pdf")
                    
                else:
                    failed_extractions.append(item_text)
                    print(f"  ❌ Could not extract IDs")
                
            except Exception as e:
                failed_extractions.append(f"Item {i+1} (error: {e})")
                print(f"  ❌ Error: {e}")
        
        extraction_time = time.time() - extraction_start
        print(f"\n✅ URL extraction completed in {extraction_time:.1f} seconds!")
        print(f"📊 Successfully extracted: {len(direct_urls)}/10")
        
        if failed_extractions:
            print(f"❌ Failed extractions: {len(failed_extractions)}")
        
        if len(direct_urls) == 0:
            print("❌ No URLs extracted - cannot proceed with downloads")
            return
        
        print(f"\n🚀 Step 4: SUPER FAST DOWNLOAD ({len(direct_urls)} files)...")
        download_start = time.time()
        
        # Download each PDF directly
        downloaded_files = []
        failed_downloads = []
        
        for i, (item_text, item_code, suffix_id, direct_url) in enumerate(direct_urls, 1):
            try:
                print(f"\n📄 Downloading {i}/{len(direct_urls)}: {item_text}")
                print(f"  URL: {direct_url}")
                
                # Count files before download
                files_before = len(glob.glob(os.path.join(download_folder, "*.pdf")))
                
                # Navigate directly to PDF URL
                driver.get(direct_url)
                
                # Wait for download to start
                print(f"  ⏳ Waiting for download...")
                download_started = False
                for wait_time in range(10):  # Wait up to 10 seconds
                    time.sleep(1)
                    files_after = len(glob.glob(os.path.join(download_folder, "*.pdf")))
                    if files_after > files_before:
                        download_started = True
                        print(f"  ✅ Download completed!")
                        downloaded_files.append(item_text)
                        break
                
                if not download_started:
                    failed_downloads.append(item_text)
                    print(f"  ⚠️ Download may have failed")
                
            except Exception as e:
                failed_downloads.append(f"{item_text} (error: {e})")
                print(f"  ❌ Error: {e}")
        
        total_time = time.time() - start_time
        download_time = time.time() - download_start
        
        print(f"\n🎉 TEST COMPLETED!")
        print(f"⚡ Total time: {total_time:.1f} seconds")
        print(f"📥 Download time: {download_time:.1f} seconds")
        print(f"✅ Successfully downloaded: {len(downloaded_files)}/{len(direct_urls)}")
        
        if failed_downloads:
            print(f"❌ Failed downloads: {len(failed_downloads)}")
        
        print(f"📁 Download folder: {download_folder}")
        
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
        
        print(f"\n🚀 PO {po_number} TEST SUCCESSFUL!")
        print(f"⚡ Ready to download all {total_items} items if needed!")
        
    finally:
        print(f"\n🔄 Closing browser...")
        driver.quit()

if __name__ == "__main__":
    test_new_po_1280282()
