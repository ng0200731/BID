"""
Improved downloader - Better file detection and longer wait times
"""
import os
import glob
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

def setup_driver():
    """Setup Chrome driver with better download preferences"""
    print("Setting up Chrome driver...")
    
    # Create downloads directory
    download_dir = os.path.join(os.getcwd(), "downloads")
    os.makedirs(download_dir, exist_ok=True)
    
    # Also check default downloads folder
    default_downloads = os.path.join(os.path.expanduser("~"), "Downloads")
    
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-web-security")
    chrome_options.add_argument("--allow-running-insecure-content")
    
    # Set download preferences
    prefs = {
        "download.default_directory": download_dir,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": False,
        "safebrowsing.disable_download_protection": True,
        "profile.default_content_setting_values.notifications": 2
    }
    chrome_options.add_experimental_option("prefs", prefs)
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    return driver, download_dir, default_downloads

def wait_for_download(download_dirs, files_before, max_wait=30):
    """Wait for new files to appear in any download directory"""
    print(f"   ⏳ Waiting for download (max {max_wait}s)...")
    
    for wait_time in range(max_wait):
        time.sleep(1)
        
        # Check all possible download locations
        for download_dir in download_dirs:
            if os.path.exists(download_dir):
                current_files = set(glob.glob(os.path.join(download_dir, "*.pdf")))
                new_files = current_files - files_before.get(download_dir, set())
                
                if new_files:
                    new_file = list(new_files)[0]
                    filename = os.path.basename(new_file)
                    file_size = os.path.getsize(new_file) / 1024  # KB
                    print(f"   ✅ Downloaded: {filename} ({file_size:.1f} KB)")
                    print(f"   📁 Location: {download_dir}")
                    return True
        
        # Show progress every 5 seconds
        if wait_time % 5 == 0 and wait_time > 0:
            print(f"   ⏳ Still waiting... ({wait_time}s)")
    
    print(f"   ⚠️  No file detected after {max_wait}s")
    return False

def improved_download():
    """Improved download with better file detection"""
    driver = None
    try:
        print("=== IMPROVED REAL DOWNLOAD ===")
        print("PO: 1284678")
        print("Method: 2 (Hybrid Speed Download)")
        print("=" * 40)
        
        driver, download_dir, default_downloads = setup_driver()
        download_dirs = [download_dir, default_downloads]
        wait = WebDriverWait(driver, 30)
        
        print(f"📁 Primary download folder: {download_dir}")
        print(f"📁 Backup download folder: {default_downloads}")
        
        # Login
        print("\nStep 1: Logging in...")
        driver.get("https://app.e-brandid.com/login/login.aspx")
        
        username_field = wait.until(EC.presence_of_element_located((By.ID, "txtUserName")))
        password_field = driver.find_element(By.ID, "txtPassword")
        
        username_field.send_keys("sales10@fuchanghk.com")
        password_field.send_keys("fc31051856")
        
        login_button = driver.find_element(By.XPATH, "//img[@onclick='return Login();']")
        login_button.click()
        
        wait.until(lambda d: "login" not in d.current_url.lower())
        print("✅ Login successful!")
        
        # Navigate to PO
        print("\nStep 2: Navigating to PO...")
        po_url = f"https://app.e-brandid.com/Bidnet/bidnet3/factoryPODetail.aspx?po_id=1284678"
        driver.get(po_url)
        
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "table")))
        time.sleep(3)
        
        # Find item links
        print("\nStep 3: Finding items...")
        tables = driver.find_elements(By.TAG_NAME, "table")
        item_links = []
        for table in tables:
            links = table.find_elements(By.XPATH, ".//a[contains(@onclick, 'openItemDetail')]")
            if links:
                item_links = links
                break
        
        print(f"✅ Found {len(item_links)} items to download")
        
        if not item_links:
            print("❌ No items found.")
            return
        
        # Get initial file state
        files_before = {}
        for dir_path in download_dirs:
            if os.path.exists(dir_path):
                files_before[dir_path] = set(glob.glob(os.path.join(dir_path, "*.pdf")))
            else:
                files_before[dir_path] = set()
        
        # Download first 3 items (for testing)
        print(f"\nStep 4: Starting downloads (first 3 items)...")
        downloaded_count = 0
        
        for i, link in enumerate(item_links[:3]):
            try:
                print(f"\n📥 Downloading item {i+1}/3...")
                
                # Store original window handles
                original_windows = len(driver.window_handles)
                
                # Click item link
                driver.execute_script("arguments[0].click();", link)
                
                # Wait for new window
                new_window_opened = False
                for wait_attempt in range(30):  # 3 seconds max wait
                    time.sleep(0.1)
                    if len(driver.window_handles) > original_windows:
                        new_window_opened = True
                        break
                
                if new_window_opened:
                    # Switch to new window
                    driver.switch_to.window(driver.window_handles[-1])
                    
                    try:
                        # Find and click download link
                        download_element = WebDriverWait(driver, 10).until(
                            EC.presence_of_element_located((By.XPATH, "//a[contains(text(), 'Download')]"))
                        )
                        
                        print(f"   🖱️  Clicking download button...")
                        download_element.click()
                        
                        # Wait for download with better detection
                        if wait_for_download(download_dirs, files_before, max_wait=30):
                            downloaded_count += 1
                            # Update files_before for next iteration
                            for dir_path in download_dirs:
                                if os.path.exists(dir_path):
                                    files_before[dir_path] = set(glob.glob(os.path.join(dir_path, "*.pdf")))
                        
                    except Exception as e:
                        print(f"   ❌ Error in download window: {e}")
                    
                    # Close popup window
                    driver.close()
                    driver.switch_to.window(driver.window_handles[0])
                    
                else:
                    print(f"   ❌ No popup window opened")
                
                # Delay between items
                time.sleep(2)
                
            except Exception as e:
                print(f"   ❌ Error processing item {i+1}: {e}")
                continue
        
        print(f"\n🎉 DOWNLOAD COMPLETE!")
        print(f"📊 Successfully downloaded: {downloaded_count} files")
        
        # List all PDF files in both directories
        print(f"\n📋 All PDF files found:")
        total_files = 0
        for dir_path in download_dirs:
            if os.path.exists(dir_path):
                pdf_files = glob.glob(os.path.join(dir_path, "*.pdf"))
                if pdf_files:
                    print(f"\n📁 In {dir_path}:")
                    for pdf_file in pdf_files:
                        filename = os.path.basename(pdf_file)
                        file_size = os.path.getsize(pdf_file) / 1024  # KB
                        print(f"   • {filename} ({file_size:.1f} KB)")
                        total_files += 1
        
        print(f"\n📊 Total PDF files: {total_files}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    improved_download()
