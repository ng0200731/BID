"""
Clean naming downloader: original_name_1, original_name_2, etc.
"""

import os
import glob
import time
import shutil
import re
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager

def extract_pdf_name_from_onclick(onclick_attr):
    """Extract original PDF name from onclick attribute"""
    if not onclick_attr:
        return None
    
    # Look for PDF URL in onclick
    # Example: MM_openBrWindow('https://app4.brandid.com/Artwork/74PATC204_8992784.pdf'
    match = re.search(r"([^/]+\.pdf)", onclick_attr)
    if match:
        return match.group(1)
    return None

def get_next_filename(base_name, folder):
    """Get next available filename with counter"""
    name, ext = os.path.splitext(base_name)
    
    # Check if base name exists
    base_path = os.path.join(folder, base_name)
    if not os.path.exists(base_path):
        return base_name
    
    # Find next available number
    counter = 1
    while True:
        new_name = f"{name}_{counter}{ext}"
        new_path = os.path.join(folder, new_name)
        if not os.path.exists(new_path):
            return new_name
        counter += 1

def clean_naming_downloader(po_number="1284678"):
    """Downloader with clean naming: original_name_1, original_name_2, etc."""
    
    print(f"🚀 Clean Naming Downloader - PO {po_number}")
    print("📝 Naming pattern: original_name_1, original_name_2, etc.")
    
    # Setup folder with timestamp format: YYYY_MM_DD_HH_MM_{PO#}
    timestamp = datetime.now().strftime("%Y_%m_%d_%H_%M")
    folder_name = f"{timestamp}_{po_number}"
    download_folder = os.path.join(os.getcwd(), folder_name)

    if not os.path.exists(download_folder):
        os.makedirs(download_folder, exist_ok=True)
        print(f"📁 Created folder: {folder_name}")
    else:
        print(f"📁 Using existing folder: {folder_name}")
    
    # Count initial files
    initial_files = glob.glob(os.path.join(download_folder, "*.pdf"))
    initial_count = len(initial_files)
    print(f"📊 Initial PDF files: {initial_count}")
    
    # Setup Chrome
    chrome_options = Options()
    
    # Download preferences
    prefs = {
        "download.default_directory": download_folder,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True,
        "plugins.always_open_pdf_externally": True,
        "profile.default_content_setting_values.automatic_downloads": 1
    }
    chrome_options.add_experimental_option("prefs", prefs)
    
    # Speed optimizations
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-images")
    chrome_options.add_argument("--disable-extensions")
    
    try:
        driver_path = ChromeDriverManager().install()
        service = Service(driver_path)
        driver = webdriver.Chrome(service=service, options=chrome_options)
    except:
        driver = webdriver.Chrome(options=chrome_options)
    
    wait = WebDriverWait(driver, 10)
    
    try:
        print(f"\n📝 Logging in...")
        driver.get("https://app.e-brandid.com/login/login.aspx")
        
        username_field = wait.until(EC.presence_of_element_located((By.ID, "txtUserName")))
        password_field = driver.find_element(By.ID, "txtPassword")
        
        username_field.send_keys("sales10@fuchanghk.com")
        password_field.send_keys("fc31051856")
        
        login_button = driver.find_element(By.XPATH, "//img[@onclick='return Login();']")
        login_button.click()
        
        wait.until(lambda d: "login" not in d.current_url.lower())
        print("✅ Login completed!")
        
        print(f"\n🔍 Navigating to PO {po_number}...")
        po_url = f"https://app.e-brandid.com/Bidnet/bidnet3/factoryPODetail.aspx?po_id={po_number}"
        driver.get(po_url)
        
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "table")))
        
        # Find item links
        tables = driver.find_elements(By.TAG_NAME, "table")
        item_links = []
        for table in tables:
            links = table.find_elements(By.XPATH, ".//a[contains(@onclick, 'openItemDetail')]")
            if links:
                item_links = links
                break
        
        total_items = len(item_links)
        print(f"✅ Found {total_items} items in PO {po_number}")
        
        if total_items == 0:
            print("❌ No item links found!")
            return
        
        # Set download behavior
        driver.execute_cdp_cmd('Page.setDownloadBehavior', {
            'behavior': 'allow',
            'downloadPath': download_folder
        })
        
        print(f"\n⚡ Processing {total_items} items with clean naming...")
        
        processed_items = []
        failed_items = []
        downloaded_files = []
        pdf_counter = {}  # Track how many times each PDF has been used
        
        start_time = time.time()
        
        for i, hyperlink in enumerate(item_links):
            try:
                link_text = hyperlink.text.strip()
                
                print(f"\n⚡ Item {i+1}/{total_items}: '{link_text}'")
                
                # Get files before download
                files_before = set(glob.glob(os.path.join(download_folder, "*.pdf")))
                
                # Quick scroll and click
                driver.execute_script("arguments[0].scrollIntoView(true);", hyperlink)
                original_windows = len(driver.window_handles)
                hyperlink.click()
                
                # Quick wait for new window
                new_window_opened = False
                for wait_attempt in range(30):  # 3 seconds total
                    time.sleep(0.1)
                    if len(driver.window_handles) > original_windows:
                        new_window_opened = True
                        break
                
                if new_window_opened:
                    # Switch to new window
                    driver.switch_to.window(driver.window_handles[-1])
                    
                    # Quick find download link and extract PDF name
                    try:
                        download_element = WebDriverWait(driver, 3).until(
                            EC.presence_of_element_located((By.XPATH, "//a[contains(text(), 'Download')]"))
                        )
                        
                        # Extract original PDF name from onclick
                        onclick_attr = download_element.get_attribute('onclick')
                        original_pdf_name = extract_pdf_name_from_onclick(onclick_attr)
                        
                        if not original_pdf_name:
                            original_pdf_name = f"unknown_{i+1}.pdf"
                        
                        print(f"  📄 Original PDF: {original_pdf_name}")
                        
                        # Determine final filename with counter
                        final_filename = get_next_filename(original_pdf_name, download_folder)
                        final_filepath = os.path.join(download_folder, final_filename)
                        
                        print(f"  📝 Target filename: {final_filename}")
                        print(f"  📥 Downloading...")
                        
                        download_element.click()
                        time.sleep(2)  # Wait for download
                        
                        # Check for new files
                        files_after = set(glob.glob(os.path.join(download_folder, "*.pdf")))
                        new_files = files_after - files_before
                        
                        if new_files:
                            # New file downloaded
                            new_file = list(new_files)[0]
                            
                            # Rename to clean format
                            if os.path.basename(new_file) != final_filename:
                                shutil.move(new_file, final_filepath)
                                print(f"  ✅ Downloaded and renamed: {final_filename}")
                            else:
                                print(f"  ✅ Downloaded: {final_filename}")
                            
                            downloaded_files.append(final_filename)
                            
                        else:
                            # No new file, copy existing and rename
                            print(f"  🔄 No new download, creating copy...")
                            
                            # Find the original PDF file in folder
                            existing_original = None
                            for existing_file in glob.glob(os.path.join(download_folder, "*.pdf")):
                                if os.path.basename(existing_file) == original_pdf_name:
                                    existing_original = existing_file
                                    break
                            
                            if not existing_original:
                                # Find any file with similar name
                                base_name = original_pdf_name.split('_')[0] if '_' in original_pdf_name else original_pdf_name.split('.')[0]
                                for existing_file in glob.glob(os.path.join(download_folder, "*.pdf")):
                                    if base_name in os.path.basename(existing_file):
                                        existing_original = existing_file
                                        break
                            
                            if existing_original:
                                shutil.copy2(existing_original, final_filepath)
                                print(f"  ✅ Copied and renamed: {final_filename}")
                                downloaded_files.append(final_filename)
                            else:
                                print(f"  ❌ No source file found for copying")
                                failed_items.append(link_text)
                                continue
                        
                        processed_items.append(link_text)
                        
                    except TimeoutException:
                        print(f"  ❌ Download link timeout")
                        failed_items.append(link_text)
                    
                    # Quick close and return
                    driver.close()
                    driver.switch_to.window(driver.window_handles[0])
                    
                else:
                    print(f"  ❌ Window timeout")
                    failed_items.append(link_text)
                
                # Minimal delay
                time.sleep(0.5)
                
            except Exception as e:
                print(f"  ❌ Error: {e}")
                failed_items.append(f"Item {i+1}")
                continue
        
        processing_time = time.time() - start_time
        
        # Final file count
        final_files = glob.glob(os.path.join(download_folder, "*.pdf"))
        total_size = sum(os.path.getsize(f) for f in final_files)
        new_downloads = len(final_files) - initial_count
        
        print(f"\n🎉 CLEAN NAMING DOWNLOAD COMPLETE!")
        print(f"⚡ Total time: {processing_time/60:.1f} minutes")
        print(f"🚀 Processing speed: {processing_time:.1f}s ({processing_time/total_items:.1f}s per item)")
        print(f"📥 New downloads: {new_downloads}")
        print(f"✅ Processed items: {len(processed_items)}/{total_items}")
        print(f"❌ Failed items: {len(failed_items)}")
        print(f"💾 Total size: {total_size/1024/1024:.1f} MB")
        print(f"📁 Location: {download_folder}")
        
        if downloaded_files:
            print(f"\n📋 Downloaded files with clean naming:")
            for filename in downloaded_files:
                filepath = os.path.join(download_folder, filename)
                if os.path.exists(filepath):
                    file_size = os.path.getsize(filepath)
                    print(f"  - {filename} ({file_size:,} bytes)")
        
        # Show naming pattern summary
        print(f"\n📝 Naming Pattern Summary:")
        unique_bases = {}
        for filename in downloaded_files:
            if '_' in filename and filename.endswith('.pdf'):
                # Check if it ends with _number.pdf
                parts = filename.rsplit('_', 1)
                if len(parts) == 2 and parts[1].replace('.pdf', '').isdigit():
                    base = parts[0] + '.pdf'
                else:
                    base = filename
            else:
                base = filename
            
            if base not in unique_bases:
                unique_bases[base] = []
            unique_bases[base].append(filename)
        
        for base, files in unique_bases.items():
            if len(files) > 1:
                print(f"  📄 {base}: {len(files)} copies ({', '.join(files)})")
            else:
                print(f"  📄 {base}: 1 copy")
        
        print(f"\n🎯 CLEAN NAMING SUCCESS!")
        print(f"✅ Pattern: original_name, original_name_1, original_name_2, etc.")
        print(f"✅ {new_downloads} files for {total_items} items")
        print(f"✅ Clean, organized filenames")
        
    finally:
        print(f"\n🔄 Closing browser...")
        driver.quit()

if __name__ == "__main__":
    clean_naming_downloader("1284678")
