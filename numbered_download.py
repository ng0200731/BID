"""
Numbered PDF downloader - Creates numbered copies for visual clarity
Shows all 19 items as separate files with _2, _3, _4 numbering for duplicates
"""
import os
import re
import requests
import shutil
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
    """Setup Chrome driver"""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    return driver

def extract_pdf_url(onclick_attr):
    """Extract PDF URL from onclick attribute"""
    match = re.search(r"MM_openBrWindow\('([^']+\.pdf)'", onclick_attr)
    if match:
        return match.group(1)
    return None

def download_pdf(url, filename, download_dir):
    """Download PDF from URL"""
    try:
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        response = session.get(url, timeout=30)
        response.raise_for_status()
        
        file_path = os.path.join(download_dir, filename)
        with open(file_path, 'wb') as f:
            f.write(response.content)
        
        file_size = len(response.content) / 1024
        return file_path, file_size
        
    except Exception as e:
        print(f"   ❌ Error downloading {filename}: {e}")
        return None, 0

def numbered_download():
    """Download with numbered duplicates for visual clarity"""
    driver = None
    try:
        print("=== NUMBERED PDF DOWNLOAD ===")
        print("PO: 1284678")
        print("Method: Create numbered copies for visual clarity")
        print("=" * 50)
        
        # Create download directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        download_dir = os.path.join(os.getcwd(), f"PO_1284678_All_Items_{timestamp}")
        os.makedirs(download_dir, exist_ok=True)
        print(f"📁 Download directory: {download_dir}")
        
        driver = setup_driver()
        wait = WebDriverWait(driver, 30)
        
        # Login
        print("\n🔐 Step 1: Logging in...")
        driver.get("https://app.e-brandid.com/login/login.aspx")
        
        username_field = wait.until(EC.presence_of_element_located((By.ID, "txtUserName")))
        password_field = driver.find_element(By.ID, "txtPassword")
        
        username_field.send_keys("sales10@fuchanghk.com")
        password_field.send_keys("fc31051856")
        
        login_button = driver.find_element(By.XPATH, "//img[@onclick='return Login();']")
        login_button.click()
        
        wait.until(lambda d: "login" not in d.current_url.lower())
        print("   ✅ Login successful!")
        
        # Navigate to PO
        print("\n🔍 Step 2: Navigating to PO 1284678...")
        po_url = f"https://app.e-brandid.com/Bidnet/bidnet3/factoryPODetail.aspx?po_id=1284678"
        driver.get(po_url)
        
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "table")))
        time.sleep(3)
        
        # Find items
        print("\n📋 Step 3: Finding all items...")
        tables = driver.find_elements(By.TAG_NAME, "table")
        item_links = []
        for table in tables:
            links = table.find_elements(By.XPATH, ".//a[contains(@onclick, 'openItemDetail')]")
            if links:
                item_links = links
                break
        
        print(f"   ✅ Found {len(item_links)} items")
        
        if not item_links:
            print("   ❌ No items found!")
            return
        
        # Extract PDF URLs and item info
        print(f"\n📄 Step 4: Processing all {len(item_links)} items...")
        item_data = []  # Store (item_name, pdf_url, original_filename)
        
        for i, link in enumerate(item_links):
            try:
                item_name = link.text.strip()
                print(f"\n🔍 Processing item {i+1}/{len(item_links)}: {item_name}")
                
                # Click item to open popup
                original_windows = len(driver.window_handles)
                driver.execute_script("arguments[0].click();", link)
                
                # Wait for popup
                popup_opened = False
                for wait_attempt in range(30):
                    time.sleep(0.1)
                    if len(driver.window_handles) > original_windows:
                        popup_opened = True
                        break
                
                if popup_opened:
                    driver.switch_to.window(driver.window_handles[-1])
                    
                    try:
                        # Find download button and extract PDF URL
                        download_button = WebDriverWait(driver, 5).until(
                            EC.presence_of_element_located((By.XPATH, "//a[contains(text(), 'Download')]"))
                        )
                        
                        onclick_attr = download_button.get_attribute('onclick')
                        pdf_url = extract_pdf_url(onclick_attr)
                        
                        if pdf_url:
                            original_filename = os.path.basename(pdf_url)
                            item_data.append((item_name, pdf_url, original_filename))
                            print(f"   ✅ Found PDF: {original_filename}")
                        else:
                            print(f"   ❌ Could not extract PDF URL")
                    
                    except Exception as e:
                        print(f"   ❌ Error in popup: {e}")
                    
                    # Close popup
                    driver.close()
                    driver.switch_to.window(driver.window_handles[0])
                    time.sleep(0.5)
                
                else:
                    print(f"   ❌ No popup opened")
            
            except Exception as e:
                print(f"   ❌ Error processing item {i+1}: {e}")
                continue
        
        # Download with numbering logic
        print(f"\n⬇️  Step 5: Downloading with numbered duplicates...")
        download_counter = {}  # Track how many times each PDF is downloaded
        downloaded_files = []
        unique_pdfs = {}  # Cache downloaded PDF content
        
        for i, (item_name, pdf_url, original_filename) in enumerate(item_data):
            try:
                print(f"\n📥 Processing {i+1}/{len(item_data)}: {item_name}")
                
                # Remove .pdf extension for numbering
                base_name = original_filename.replace('.pdf', '')
                
                if base_name not in download_counter:
                    # First occurrence - keep original name
                    download_counter[base_name] = 1
                    final_filename = original_filename
                    print(f"   📄 First occurrence: {final_filename}")
                    
                    # Download the actual file
                    file_path, file_size = download_pdf(pdf_url, final_filename, download_dir)
                    if file_path:
                        unique_pdfs[base_name] = file_path  # Cache for copying
                        downloaded_files.append((final_filename, file_size, item_name))
                        print(f"   ✅ Downloaded: {final_filename} ({file_size:.1f} KB)")
                
                else:
                    # Subsequent occurrences - add _2, _3, etc.
                    download_counter[base_name] += 1
                    count = download_counter[base_name]
                    final_filename = f"{base_name}_{count}.pdf"
                    print(f"   📄 Duplicate #{count}: {final_filename}")
                    
                    # Copy from cached file instead of downloading again
                    if base_name in unique_pdfs:
                        source_file = unique_pdfs[base_name]
                        target_file = os.path.join(download_dir, final_filename)
                        shutil.copy2(source_file, target_file)
                        
                        file_size = os.path.getsize(target_file) / 1024
                        downloaded_files.append((final_filename, file_size, item_name))
                        print(f"   ✅ Copied: {final_filename} ({file_size:.1f} KB)")
                    else:
                        print(f"   ❌ Source file not found for copying")
                
                time.sleep(0.5)  # Brief pause
                
            except Exception as e:
                print(f"   ❌ Error processing {item_name}: {e}")
                continue
        
        # Summary
        print(f"\n" + "="*60)
        print(f"🎉 NUMBERED DOWNLOAD COMPLETE!")
        print(f"="*60)
        print(f"📊 Total items processed: {len(item_data)}")
        print(f"📄 Total files created: {len(downloaded_files)}")
        print(f"📁 Download location: {download_dir}")
        
        # Group by base filename for summary
        file_groups = {}
        for filename, file_size, item_name in downloaded_files:
            base = filename.split('_')[0] + '_' + filename.split('_')[1] if '_' in filename else filename.replace('.pdf', '')
            if base not in file_groups:
                file_groups[base] = []
            file_groups[base].append((filename, item_name))
        
        print(f"\n📋 File Groups:")
        for base, files in file_groups.items():
            print(f"\n📄 {base}.pdf group ({len(files)} files):")
            for filename, item_name in files:
                print(f"   • {filename} → {item_name}")
        
        # Open folder
        print(f"\n🔗 Opening download folder...")
        os.startfile(download_dir)
        
        print(f"\n🎯 SUCCESS! All {len(downloaded_files)} files are now on your computer!")
        print(f"💡 You can now visually see all items with numbered duplicates!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    numbered_download()
