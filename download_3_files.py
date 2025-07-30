"""
Enhanced automation script - downloads first 3 items with better download handling
"""

import os
import time
import glob
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

def download_3_files():
    """Download first 3 files with enhanced download handling"""
    
    print("🚀 Starting Enhanced E-BrandID Download (First 3 Files)...")
    
    # Setup download folder
    download_folder = os.path.join(os.getcwd(), "1288060")
    os.makedirs(download_folder, exist_ok=True)
    print(f"📁 Download folder: {download_folder}")
    
    # Setup Chrome with explicit download preferences
    chrome_options = Options()
    
    # Download preferences
    prefs = {
        "download.default_directory": download_folder,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True,
        "safebrowsing.disable_download_protection": True,
        "profile.default_content_setting_values.notifications": 2
    }
    chrome_options.add_experimental_option("prefs", prefs)
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-web-security")
    chrome_options.add_argument("--allow-running-insecure-content")
    
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
        
        print("\n📥 Step 3: Finding and downloading files...")
        
        # Set download behavior via CDP
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
        
        # Download first 3 files
        downloaded_files = []
        for i in range(min(3, len(item_links))):
            try:
                hyperlink = item_links[i]
                link_text = hyperlink.text.strip()
                print(f"\n📄 Processing item {i+1}/3: '{link_text}'")
                
                # Count files before download
                files_before = len(glob.glob(os.path.join(download_folder, "*")))
                
                # Scroll and click
                driver.execute_script("arguments[0].scrollIntoView(true);", hyperlink)
                time.sleep(1)
                driver.execute_script("arguments[0].click();", hyperlink)
                time.sleep(3)
                
                # Handle new window
                windows = driver.window_handles
                if len(windows) > 1:
                    print(f"  ✅ New window opened")
                    driver.switch_to.window(windows[-1])
                    time.sleep(2)
                    
                    # Find and click download
                    try:
                        download_element = driver.find_element(By.XPATH, "//a[contains(text(), 'Download')]")
                        print(f"  ✅ Found download link")
                        
                        # Click download
                        driver.execute_script("arguments[0].click();", download_element)
                        print(f"  ✅ Clicked download")
                        
                        # Wait for download to start/complete
                        print(f"  ⏳ Waiting for download...")
                        download_started = False
                        for wait_time in range(30):  # Wait up to 30 seconds
                            time.sleep(1)
                            files_after = len(glob.glob(os.path.join(download_folder, "*")))
                            if files_after > files_before:
                                download_started = True
                                print(f"  ✅ Download started! Files in folder: {files_after}")
                                break
                        
                        if download_started:
                            downloaded_files.append(link_text)
                        else:
                            print(f"  ⚠️ Download may not have started")
                        
                    except Exception as e:
                        print(f"  ❌ Error with download: {e}")
                    
                    # Close window
                    driver.close()
                    driver.switch_to.window(windows[0])
                    print(f"  ✅ Closed window")
                
                time.sleep(2)
                
            except Exception as e:
                print(f"  ❌ Error processing item {i+1}: {e}")
        
        print(f"\n🎉 Download process completed!")
        print(f"✅ Attempted downloads: {len(downloaded_files)}")
        print(f"📁 Download folder: {download_folder}")
        
        # Check final file count
        final_files = glob.glob(os.path.join(download_folder, "*"))
        print(f"📄 Files in download folder: {len(final_files)}")
        
        if final_files:
            print("📋 Downloaded files:")
            for file_path in final_files:
                file_name = os.path.basename(file_path)
                file_size = os.path.getsize(file_path)
                print(f"  - {file_name} ({file_size} bytes)")
        else:
            print("⚠️ No files found in download folder")
            print("Files might be downloading to default Downloads folder")
            
            # Check default downloads
            default_downloads = os.path.join(os.path.expanduser("~"), "Downloads")
            default_files = glob.glob(os.path.join(default_downloads, "*"))
            recent_files = [f for f in default_files if os.path.getmtime(f) > time.time() - 300]  # Last 5 minutes
            
            if recent_files:
                print(f"📋 Recent files in default Downloads folder:")
                for file_path in recent_files[-10:]:  # Show last 10
                    file_name = os.path.basename(file_path)
                    file_size = os.path.getsize(file_path)
                    print(f"  - {file_name} ({file_size} bytes)")
        
    finally:
        print("\n🔄 Closing browser...")
        driver.quit()

if __name__ == "__main__":
    download_3_files()
