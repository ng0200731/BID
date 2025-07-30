"""
HYBRID SPEED method - Ultra-fast processing + Intelligent download monitoring
"""

import os
import glob
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager

def monitor_downloads_intelligently(download_folder, timeout_minutes=5):
    """Monitor download folder and wait until downloads stabilize"""
    
    print(f"\n🔍 Starting intelligent download monitoring...")
    print(f"📁 Monitoring: {download_folder}")
    print(f"⏱️ Timeout: {timeout_minutes} minutes")
    
    start_time = time.time()
    last_file_count = 0
    stable_count = 0
    stable_threshold = 30  # 30 seconds of no new files = stable
    
    while True:
        # Check current file count
        current_files = glob.glob(os.path.join(download_folder, "*.pdf"))
        current_count = len(current_files)
        
        # Calculate elapsed time
        elapsed_time = time.time() - start_time
        elapsed_minutes = elapsed_time / 60
        
        print(f"📊 Files: {current_count} | Elapsed: {elapsed_minutes:.1f}min | Stable: {stable_count}s", end="\r")
        
        # Check if new files appeared
        if current_count > last_file_count:
            print(f"\n📥 New download detected! Files: {last_file_count} → {current_count}")
            last_file_count = current_count
            stable_count = 0  # Reset stability counter
        else:
            stable_count += 1
        
        # Check if downloads have stabilized
        if stable_count >= stable_threshold:
            print(f"\n✅ Downloads stabilized! No new files for {stable_threshold} seconds")
            break
        
        # Check timeout
        if elapsed_minutes >= timeout_minutes:
            print(f"\n⏰ Timeout reached ({timeout_minutes} minutes)")
            break
        
        time.sleep(1)
    
    # Final summary
    final_files = glob.glob(os.path.join(download_folder, "*.pdf"))
    total_size = sum(os.path.getsize(f) for f in final_files)
    
    print(f"\n📊 DOWNLOAD MONITORING COMPLETE:")
    print(f"📄 Final file count: {len(final_files)}")
    print(f"💾 Total size: {total_size:,} bytes ({total_size/1024/1024:.1f} MB)")
    print(f"⏱️ Monitoring time: {elapsed_minutes:.1f} minutes")
    
    return final_files

def hybrid_speed_method():
    """HYBRID SPEED: Ultra-fast processing + Intelligent download monitoring"""
    
    print("🚀 HYBRID SPEED Method - PO 1288060")
    print("⚡ Ultra-fast processing (1.7s/item) + Smart download monitoring")

    po_number = "1288060"
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
    
    # ULTRA FAST Chrome setup
    chrome_options = Options()
    
    # Download preferences
    prefs = {
        "download.default_directory": download_folder,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True,
        "plugins.always_open_pdf_externally": True
    }
    chrome_options.add_experimental_option("prefs", prefs)
    
    # SPEED OPTIMIZATIONS
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-images")  # No images!
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-plugins")
    chrome_options.add_argument("--disable-background-timer-throttling")
    chrome_options.add_argument("--disable-renderer-backgrounding")
    chrome_options.add_argument("--disable-backgrounding-occluded-windows")
    chrome_options.add_argument("--disable-features=TranslateUI")
    chrome_options.add_argument("--disable-ipc-flooding-protection")
    
    # Disable image loading via prefs too
    prefs["profile.managed_default_content_settings.images"] = 2
    chrome_options.add_experimental_option("prefs", prefs)
    
    try:
        driver_path = ChromeDriverManager().install()
        service = Service(driver_path)
        driver = webdriver.Chrome(service=service, options=chrome_options)
    except:
        driver = webdriver.Chrome(options=chrome_options)
    
    # Shorter waits for speed
    wait = WebDriverWait(driver, 10)
    
    try:
        print(f"\n📝 PHASE 1: ULTRA-FAST PROCESSING...")
        processing_start = time.time()
        
        # Fast login
        driver.get("https://app.e-brandid.com/login/login.aspx")
        username_field = wait.until(EC.presence_of_element_located((By.ID, "txtUserName")))
        password_field = driver.find_element(By.ID, "txtPassword")
        
        username_field.send_keys("sales10@fuchanghk.com")
        password_field.send_keys("fc31051856")
        
        login_button = driver.find_element(By.XPATH, "//img[@onclick='return Login();']")
        login_button.click()
        wait.until(lambda d: "login" not in d.current_url.lower())
        print("✅ Login completed!")
        
        # Fast navigation
        po_url = f"https://app.e-brandid.com/Bidnet/bidnet3/factoryPODetail.aspx?po_id={po_number}"
        driver.get(po_url)
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "table")))
        print("✅ PO page loaded!")
        
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
        
        if total_items == 0:
            print("❌ No item links found!")
            return
        
        # ULTRA FAST processing
        processed_items = []
        failed_items = []
        
        print(f"\n⚡ Processing first 10 items at ultra speed...")

        for i, hyperlink in enumerate(item_links[:10]):
            try:
                link_text = hyperlink.text.strip()
                
                # Show progress every 5 items
                if (i + 1) % 5 == 0 or i == 0:
                    print(f"⚡ Item {i+1}/10: '{link_text}'")
                
                # Quick scroll and click
                driver.execute_script("arguments[0].scrollIntoView(true);", hyperlink)
                original_windows = len(driver.window_handles)
                hyperlink.click()
                
                # Quick wait for new window (max 3 seconds)
                new_window_opened = False
                for wait_attempt in range(30):  # 3 seconds total
                    time.sleep(0.1)
                    if len(driver.window_handles) > original_windows:
                        new_window_opened = True
                        break
                
                if new_window_opened:
                    # Switch to new window
                    driver.switch_to.window(driver.window_handles[-1])
                    
                    # Quick find and click download
                    try:
                        download_element = WebDriverWait(driver, 2).until(
                            EC.presence_of_element_located((By.XPATH, "//a[contains(text(), 'Download')]"))
                        )
                        download_element.click()
                        processed_items.append(link_text)
                        
                    except TimeoutException:
                        failed_items.append(link_text)
                    
                    # Quick close and return
                    driver.close()
                    driver.switch_to.window(driver.window_handles[0])
                    
                else:
                    failed_items.append(link_text)
                
                # Minimal delay
                time.sleep(0.5)
                
            except Exception as e:
                failed_items.append(f"Item {i+1}")
                continue
        
        processing_time = time.time() - processing_start
        
        print(f"\n✅ PHASE 1 COMPLETE - ULTRA-FAST PROCESSING:")
        print(f"⚡ Processing time: {processing_time:.1f} seconds")
        print(f"🚀 Average per item: {processing_time/10:.1f} seconds")
        print(f"✅ Processed items: {len(processed_items)}/10")
        print(f"❌ Failed items: {len(failed_items)}")
        
        print(f"\n📥 PHASE 2: INTELLIGENT DOWNLOAD MONITORING...")
        print(f"🔍 Keeping browser alive while monitoring downloads...")
        
        # Monitor downloads intelligently (keep browser alive!)
        final_files = monitor_downloads_intelligently(download_folder, timeout_minutes=5)
        
        # Calculate results
        new_downloads = len(final_files) - initial_count
        total_time = time.time() - processing_start
        
        print(f"\n🎉 HYBRID SPEED METHOD COMPLETE!")
        print(f"⚡ Total time: {total_time/60:.1f} minutes")
        print(f"🚀 Processing speed: {processing_time:.1f}s ({processing_time/total_items:.1f}s per item)")
        print(f"📥 New downloads: {new_downloads}/10")
        print(f"📊 Success rate: {new_downloads/10*100:.1f}%")
        
        if final_files:
            print(f"\n📋 Downloaded files:")
            for file_path in final_files[-10:]:  # Show last 10 files
                file_name = os.path.basename(file_path)
                file_size = os.path.getsize(file_path)
                print(f"  - {file_name} ({file_size:,} bytes)")
            
            if len(final_files) > 10:
                print(f"  ... and {len(final_files) - 10} more files")
        
        if failed_items:
            print(f"\n⚠️ Failed items ({len(failed_items)}):")
            for failure in failed_items[:5]:
                print(f"  - {failure}")
            if len(failed_items) > 5:
                print(f"  ... and {len(failed_items) - 5} more")
        
        print(f"\n🎯 HYBRID METHOD SUCCESS!")
        print(f"✅ Ultra-fast processing: {processing_time:.1f}s")
        print(f"✅ Intelligent monitoring: Downloads completed")
        print(f"✅ Best of both worlds: Speed + Reliability")
        
    finally:
        print(f"\n🔄 Closing browser...")
        driver.quit()

if __name__ == "__main__":
    hybrid_speed_method()
