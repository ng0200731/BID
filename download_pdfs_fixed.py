"""
Fixed automation script - downloads PDFs by extracting direct URLs
"""

import os
import time
import glob
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

def download_pdfs_fixed():
    """Download ALL PDFs using the direct PDF URLs from onclick attributes"""

    print("🚀 Starting Complete PDF Download (ALL 357 Files)...")
    print("⚠️  This will take approximately 30-60 minutes to complete")
    
    # Setup download folder
    download_folder = os.path.join(os.getcwd(), "1288060")
    os.makedirs(download_folder, exist_ok=True)
    print(f"📁 Download folder: {download_folder}")
    
    # Setup Chrome with download preferences
    chrome_options = Options()
    
    prefs = {
        "download.default_directory": download_folder,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True,
        "plugins.always_open_pdf_externally": True  # Download PDFs instead of viewing
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
        print("\n📝 Step 1: Logging in...")
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
        
        print("\n🔍 Step 2: Navigating to PO page...")
        po_url = "https://app.e-brandid.com/Bidnet/bidnet3/factoryPODetail.aspx?po_id=1288060"
        driver.get(po_url)
        time.sleep(5)
        print("✅ Navigation successful!")
        
        print("\n📥 Step 3: Extracting PDF URLs and downloading...")
        
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
        
        print(f"Found {len(item_links)} item links")
        
        # Process ALL items
        downloaded_files = []
        pdf_urls = []

        # Check if folder exists and ask user
        if os.path.exists(download_folder):
            existing_files = glob.glob(os.path.join(download_folder, "*.pdf"))
            if existing_files:
                print(f"\n📁 Folder already contains {len(existing_files)} PDF files")
                print("❓ What would you like to do?")
                print("1. Remove existing files and start fresh")
                print("2. Create new folder with timestamp")

                choice = input("Enter your choice (1 or 2): ").strip()
                if choice == "1":
                    import shutil
                    shutil.rmtree(download_folder)
                    os.makedirs(download_folder, exist_ok=True)
                    print("🗑️ Removed existing files")
                elif choice == "2":
                    from datetime import datetime
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    download_folder = f"{download_folder}_{timestamp}"
                    os.makedirs(download_folder, exist_ok=True)
                    print(f"📁 Created new folder: {download_folder}")

                    # Update Chrome download path
                    driver.execute_cdp_cmd('Page.setDownloadBehavior', {
                        'behavior': 'allow',
                        'downloadPath': download_folder
                    })

        print(f"\n📥 Processing ALL {len(item_links)} items...")

        for i in range(len(item_links)):
            try:
                hyperlink = item_links[i]
                link_text = hyperlink.text.strip()

                # Progress indicator
                if (i + 1) % 50 == 0 or i == 0:
                    print(f"\n📄 Processing item {i+1}/{len(item_links)}: '{link_text}'")
                
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
                    
                    # Find download link and extract PDF URL from onclick
                    try:
                        download_link = driver.find_element(By.XPATH, "//a[contains(text(), 'Download')]")
                        onclick_attr = download_link.get_attribute('onclick')
                        print(f"  ✅ Found download link with onclick: {onclick_attr}")
                        
                        # Extract PDF URL from onclick using regex
                        # Pattern: MM_openBrWindow('URL','...
                        match = re.search(r"MM_openBrWindow\('([^']+)'", onclick_attr)
                        if match:
                            pdf_url = match.group(1)
                            pdf_urls.append((link_text, pdf_url))
                            print(f"  ✅ Extracted PDF URL: {pdf_url}")
                        else:
                            print(f"  ❌ Could not extract PDF URL from onclick")
                        
                    except Exception as e:
                        print(f"  ❌ Error finding download link: {e}")
                    
                    # Close detail window
                    driver.close()
                    driver.switch_to.window(windows[0])
                    print(f"  ✅ Closed detail window")
                
                time.sleep(1)
                
            except Exception as e:
                print(f"  ❌ Error processing item {i+1}: {e}")
        
        print(f"\n📥 Step 4: Downloading {len(pdf_urls)} PDF files...")
        
        # Download each PDF directly
        for i, (item_name, pdf_url) in enumerate(pdf_urls, 1):
            try:
                print(f"\n📄 Downloading {i}/{len(pdf_urls)}: {item_name}")
                print(f"  URL: {pdf_url}")
                
                # Count files before download
                files_before = len(glob.glob(os.path.join(download_folder, "*.pdf")))
                
                # Navigate directly to PDF URL
                driver.get(pdf_url)
                
                # Wait for download to start
                print(f"  ⏳ Waiting for download to start...")
                download_started = False
                for wait_time in range(15):  # Wait up to 15 seconds
                    time.sleep(1)
                    files_after = len(glob.glob(os.path.join(download_folder, "*.pdf")))
                    if files_after > files_before:
                        download_started = True
                        print(f"  ✅ Download started! PDF files: {files_after}")
                        downloaded_files.append(item_name)
                        break
                
                if not download_started:
                    print(f"  ⚠️ Download may not have started")
                
            except Exception as e:
                print(f"  ❌ Error downloading {item_name}: {e}")
        
        print(f"\n🎉 Download process completed!")
        print(f"✅ Successfully downloaded: {len(downloaded_files)}/{len(pdf_urls)}")
        print(f"📁 Download folder: {download_folder}")
        
        # Check final file count
        final_files = glob.glob(os.path.join(download_folder, "*.pdf"))
        print(f"📄 PDF files in download folder: {len(final_files)}")
        
        if final_files:
            print("📋 Downloaded PDF files:")
            for file_path in final_files:
                file_name = os.path.basename(file_path)
                file_size = os.path.getsize(file_path)
                print(f"  - {file_name} ({file_size:,} bytes)")
        else:
            print("⚠️ No PDF files found in download folder")
            
            # Check default downloads for recent PDFs
            default_downloads = os.path.join(os.path.expanduser("~"), "Downloads")
            default_pdfs = glob.glob(os.path.join(default_downloads, "*.pdf"))
            recent_pdfs = [f for f in default_pdfs if os.path.getmtime(f) > time.time() - 300]  # Last 5 minutes
            
            if recent_pdfs:
                print(f"📋 Recent PDF files in default Downloads folder:")
                for file_path in recent_pdfs[-5:]:  # Show last 5
                    file_name = os.path.basename(file_path)
                    file_size = os.path.getsize(file_path)
                    print(f"  - {file_name} ({file_size:,} bytes)")
        
        print(f"\n📋 PDF URLs extracted:")
        for item_name, pdf_url in pdf_urls:
            print(f"  - {item_name}: {pdf_url}")
        
    finally:
        print("\n🔄 Closing browser...")
        driver.quit()

if __name__ == "__main__":
    download_pdfs_fixed()
