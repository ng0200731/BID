"""
Real downloader - Actually downloads files to local computer
PO: 1284678, Method: 2 (Hybrid Speed Download)
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
    """Setup Chrome driver with download preferences"""
    print("Setting up Chrome driver...")
    
    # Create downloads directory
    download_dir = os.path.join(os.getcwd(), "downloads")
    os.makedirs(download_dir, exist_ok=True)
    
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    # Set download preferences
    prefs = {
        "download.default_directory": download_dir,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True
    }
    chrome_options.add_experimental_option("prefs", prefs)
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    return driver, download_dir

def real_download():
    """Download PO 1284678 files to local computer"""
    driver = None
    try:
        print("=== REAL DOWNLOAD STARTING ===")
        print("PO: 1284678")
        print("Method: 2 (Hybrid Speed Download)")
        print("=" * 40)
        
        driver, download_dir = setup_driver()
        wait = WebDriverWait(driver, 30)
        
        # Login
        print("Step 1: Logging in...")
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
        print("Step 2: Navigating to PO...")
        po_url = f"https://app.e-brandid.com/Bidnet/bidnet3/factoryPODetail.aspx?po_id=1284678"
        driver.get(po_url)
        
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "table")))
        time.sleep(3)
        
        # Find item links
        print("Step 3: Finding items...")
        tables = driver.find_elements(By.TAG_NAME, "table")
        item_links = []
        for table in tables:
            links = table.find_elements(By.XPATH, ".//a[contains(@onclick, 'openItemDetail')]")
            if links:
                item_links = links
                break
        
        print(f"✅ Found {len(item_links)} items to download")
        
        if not item_links:
            print("❌ No items found. PO might not exist or be empty.")
            return
        
        # Download each item
        print("Step 4: Starting downloads...")
        downloaded_count = 0
        
        for i, link in enumerate(item_links[:10]):  # Limit to first 10 items
            try:
                print(f"\n📥 Downloading item {i+1}/{min(len(item_links), 10)}...")
                
                # Get files before download
                files_before = set(glob.glob(os.path.join(download_dir, "*.pdf")))
                
                # Store original window handles
                original_windows = len(driver.window_handles)
                
                # Click item link
                driver.execute_script("arguments[0].click();", link)
                
                # Wait for new window
                new_window_opened = False
                for wait_attempt in range(15):  # 1.5 seconds max wait
                    time.sleep(0.1)
                    if len(driver.window_handles) > original_windows:
                        new_window_opened = True
                        break
                
                if new_window_opened:
                    # Switch to new window
                    driver.switch_to.window(driver.window_handles[-1])
                    
                    try:
                        # Find and click download link
                        download_element = WebDriverWait(driver, 5).until(
                            EC.presence_of_element_located((By.XPATH, "//a[contains(text(), 'Download')]"))
                        )
                        
                        download_element.click()
                        print(f"   ✅ Download initiated for item {i+1}")
                        
                        # Wait for download
                        time.sleep(2)
                        
                        # Check for new files
                        files_after = set(glob.glob(os.path.join(download_dir, "*.pdf")))
                        new_files = files_after - files_before
                        
                        if new_files:
                            new_file = list(new_files)[0]
                            filename = os.path.basename(new_file)
                            print(f"   📁 Downloaded: {filename}")
                            downloaded_count += 1
                        else:
                            print(f"   ⚠️  No new file detected for item {i+1}")
                        
                    except Exception as e:
                        print(f"   ❌ Error downloading item {i+1}: {e}")
                    
                    # Close popup window
                    driver.close()
                    driver.switch_to.window(driver.window_handles[0])
                    
                else:
                    print(f"   ❌ No popup window opened for item {i+1}")
                
                # Small delay between items
                time.sleep(1)
                
            except Exception as e:
                print(f"   ❌ Error processing item {i+1}: {e}")
                continue
        
        print(f"\n🎉 DOWNLOAD COMPLETE!")
        print(f"📊 Successfully downloaded: {downloaded_count} files")
        print(f"📁 Files saved to: {download_dir}")
        
        # List downloaded files
        pdf_files = glob.glob(os.path.join(download_dir, "*.pdf"))
        if pdf_files:
            print(f"\n📋 Downloaded files:")
            for pdf_file in pdf_files:
                filename = os.path.basename(pdf_file)
                file_size = os.path.getsize(pdf_file) / 1024  # KB
                print(f"   • {filename} ({file_size:.1f} KB)")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    real_download()
