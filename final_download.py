"""
Final downloader - Clear tracking of new downloads with timestamps
"""
import os
import glob
import time
import shutil
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

def setup_driver():
    """Setup Chrome driver with clear download tracking"""
    print("Setting up Chrome driver...")
    
    # Create a timestamped download directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    download_dir = os.path.join(os.getcwd(), f"PO_1284678_downloads_{timestamp}")
    os.makedirs(download_dir, exist_ok=True)
    
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    # Force downloads to our specific folder
    prefs = {
        "download.default_directory": download_dir,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": False,
        "safebrowsing.disable_download_protection": True
    }
    chrome_options.add_experimental_option("prefs", prefs)
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    print(f"📁 Downloads will be saved to: {download_dir}")
    return driver, download_dir

def monitor_downloads(download_dir, timeout=60):
    """Monitor for new downloads with detailed logging"""
    print(f"   👀 Monitoring {download_dir} for new files...")
    
    start_time = time.time()
    last_file_count = 0
    
    while time.time() - start_time < timeout:
        # Check for any files (including .crdownload for partial downloads)
        all_files = glob.glob(os.path.join(download_dir, "*"))
        pdf_files = glob.glob(os.path.join(download_dir, "*.pdf"))
        partial_files = glob.glob(os.path.join(download_dir, "*.crdownload"))
        
        current_file_count = len(all_files)
        
        if current_file_count != last_file_count:
            print(f"   📊 Files in folder: {len(all_files)} (PDFs: {len(pdf_files)}, Downloading: {len(partial_files)})")
            last_file_count = current_file_count
        
        # If we have a completed PDF, return success
        if pdf_files:
            for pdf_file in pdf_files:
                filename = os.path.basename(pdf_file)
                file_size = os.path.getsize(pdf_file) / 1024
                print(f"   ✅ FOUND: {filename} ({file_size:.1f} KB)")
            return True
        
        # Show partial downloads
        if partial_files:
            for partial in partial_files:
                filename = os.path.basename(partial)
                print(f"   ⏳ Downloading: {filename}")
        
        time.sleep(2)
    
    print(f"   ⚠️  No completed downloads after {timeout}s")
    return False

def final_download():
    """Final download attempt with clear file tracking"""
    driver = None
    try:
        print("=== FINAL DOWNLOAD ATTEMPT ===")
        print("PO: 1284678")
        print("Target: Real PDF files on your computer")
        print("=" * 50)
        
        driver, download_dir = setup_driver()
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
        print("\n📋 Step 3: Finding downloadable items...")
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
        
        # Download just the first item to test
        print(f"\n⬇️  Step 4: Downloading first item...")
        downloaded_files = []
        
        try:
            link = item_links[0]
            print(f"   🎯 Attempting download of item 1...")
            
            # Clear any existing files first
            existing_files = glob.glob(os.path.join(download_dir, "*"))
            for f in existing_files:
                os.remove(f)
            
            # Click item link
            original_windows = len(driver.window_handles)
            driver.execute_script("arguments[0].click();", link)
            
            # Wait for popup
            popup_opened = False
            for i in range(30):
                time.sleep(0.1)
                if len(driver.window_handles) > original_windows:
                    popup_opened = True
                    break
            
            if popup_opened:
                print(f"   ✅ Popup window opened")
                driver.switch_to.window(driver.window_handles[-1])
                
                try:
                    # Find download button
                    download_button = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'Download')]"))
                    )
                    
                    print(f"   🖱️  Found download button, clicking...")
                    download_button.click()
                    
                    # Monitor for download
                    if monitor_downloads(download_dir, timeout=60):
                        print(f"   🎉 Download successful!")
                        
                        # List all files in download directory
                        all_files = glob.glob(os.path.join(download_dir, "*"))
                        for file_path in all_files:
                            filename = os.path.basename(file_path)
                            file_size = os.path.getsize(file_path) / 1024
                            downloaded_files.append(file_path)
                            print(f"   📄 {filename} ({file_size:.1f} KB)")
                    
                except Exception as e:
                    print(f"   ❌ Error in popup: {e}")
                
                # Close popup
                driver.close()
                driver.switch_to.window(driver.window_handles[0])
            else:
                print(f"   ❌ No popup window opened")
        
        except Exception as e:
            print(f"   ❌ Error downloading item: {e}")
        
        # Final summary
        print(f"\n" + "="*50)
        print(f"📊 DOWNLOAD SUMMARY")
        print(f"="*50)
        print(f"📁 Download folder: {download_dir}")
        print(f"📄 Files downloaded: {len(downloaded_files)}")
        
        if downloaded_files:
            print(f"\n✅ SUCCESS! Your files are here:")
            for file_path in downloaded_files:
                print(f"   📄 {file_path}")
            
            # Open the folder for user
            print(f"\n🔗 Opening download folder...")
            os.startfile(download_dir)
        else:
            print(f"\n❌ No files were downloaded.")
            print(f"💡 The download folder still exists at: {download_dir}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    final_download()
