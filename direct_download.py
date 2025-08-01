"""
Direct PDF downloader - Extract PDF URLs and download directly
"""
import os
import re
import requests
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
    chrome_options.add_argument("--headless")  # Run in background
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    return driver

def extract_pdf_url(onclick_attr):
    """Extract PDF URL from onclick attribute"""
    # Look for pattern: MM_openBrWindow('URL','...')
    match = re.search(r"MM_openBrWindow\('([^']+\.pdf)'", onclick_attr)
    if match:
        return match.group(1)
    return None

def download_pdf(url, filename, download_dir):
    """Download PDF from URL"""
    try:
        print(f"   📥 Downloading: {filename}")
        
        # Create session with headers
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        response = session.get(url, timeout=30)
        response.raise_for_status()
        
        # Save file
        file_path = os.path.join(download_dir, filename)
        with open(file_path, 'wb') as f:
            f.write(response.content)
        
        file_size = len(response.content) / 1024  # KB
        print(f"   ✅ Downloaded: {filename} ({file_size:.1f} KB)")
        return file_path
        
    except Exception as e:
        print(f"   ❌ Error downloading {filename}: {e}")
        return None

def direct_download():
    """Direct download of PDF files"""
    driver = None
    try:
        print("=== DIRECT PDF DOWNLOAD ===")
        print("PO: 1284678")
        print("Method: Extract PDF URLs and download directly")
        print("=" * 50)
        
        # Create download directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        download_dir = os.path.join(os.getcwd(), f"PO_1284678_PDFs_{timestamp}")
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
        print("\n📋 Step 3: Finding items and extracting PDF URLs...")
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
        
        # Extract PDF URLs from each item
        print(f"\n📄 Step 4: Extracting PDF URLs...")
        pdf_urls = []
        
        for i, link in enumerate(item_links[:10]):  # Process first 10 items
            try:
                print(f"\n🔍 Processing item {i+1}: {link.text}")
                
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
                            # Extract filename from URL
                            filename = os.path.basename(pdf_url)
                            pdf_urls.append((pdf_url, filename))
                            print(f"   ✅ Found PDF: {filename}")
                            print(f"   🔗 URL: {pdf_url}")
                        else:
                            print(f"   ❌ Could not extract PDF URL")
                    
                    except Exception as e:
                        print(f"   ❌ Error in popup: {e}")
                    
                    # Close popup
                    driver.close()
                    driver.switch_to.window(driver.window_handles[0])
                    time.sleep(1)  # Brief pause between items
                
                else:
                    print(f"   ❌ No popup opened for item {i+1}")
            
            except Exception as e:
                print(f"   ❌ Error processing item {i+1}: {e}")
                continue
        
        # Download all PDFs
        print(f"\n⬇️  Step 5: Downloading {len(pdf_urls)} PDF files...")
        downloaded_files = []
        
        for i, (pdf_url, filename) in enumerate(pdf_urls):
            print(f"\n📥 Downloading {i+1}/{len(pdf_urls)}: {filename}")
            
            file_path = download_pdf(pdf_url, filename, download_dir)
            if file_path:
                downloaded_files.append(file_path)
            
            time.sleep(1)  # Brief pause between downloads
        
        # Summary
        print(f"\n" + "="*50)
        print(f"🎉 DOWNLOAD COMPLETE!")
        print(f"="*50)
        print(f"📊 Total items processed: {len(item_links[:10])}")
        print(f"📄 PDF URLs found: {len(pdf_urls)}")
        print(f"✅ Files downloaded: {len(downloaded_files)}")
        print(f"📁 Download location: {download_dir}")
        
        if downloaded_files:
            print(f"\n📋 Downloaded files:")
            for file_path in downloaded_files:
                filename = os.path.basename(file_path)
                file_size = os.path.getsize(file_path) / 1024
                print(f"   📄 {filename} ({file_size:.1f} KB)")
            
            # Open folder
            print(f"\n🔗 Opening download folder...")
            os.startfile(download_dir)
            
            print(f"\n🎯 SUCCESS! Your PO 1284678 artwork files are now on your computer!")
        else:
            print(f"\n❌ No files were downloaded successfully.")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    direct_download()
