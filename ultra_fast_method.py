"""
ULTRA FAST method - No waiting for downloads, no images, rapid processing
"""

import os
import glob
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager

def ultra_fast_method():
    """ULTRA FAST download - no waiting for completion, no images"""
    
    print("🚀 ULTRA FAST Method - PO 1280282 (ALL 28 Files)")
    print("⚡ No download waiting + No images + Rapid processing")
    
    po_number = "1280282"
    download_folder = os.path.join(os.getcwd(), str(po_number))
    
    # Setup folder
    if not os.path.exists(download_folder):
        os.makedirs(download_folder, exist_ok=True)
        print(f"📁 Created folder: {download_folder}")
    else:
        print(f"📁 Using existing folder: {download_folder}")
    
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
        print(f"\n📝 Step 1: FAST login...")
        driver.get("https://app.e-brandid.com/login/login.aspx")
        
        # Quick login
        username_field = wait.until(EC.presence_of_element_located((By.ID, "txtUserName")))
        password_field = driver.find_element(By.ID, "txtPassword")
        
        username_field.send_keys("sales10@fuchanghk.com")
        password_field.send_keys("fc31051856")
        
        login_button = driver.find_element(By.XPATH, "//img[@onclick='return Login();']")
        login_button.click()
        
        # Quick wait for login
        wait.until(lambda d: "login" not in d.current_url.lower())
        print("✅ Login completed!")
        
        print(f"\n🔍 Step 2: FAST navigation to PO {po_number}...")
        po_url = f"https://app.e-brandid.com/Bidnet/bidnet3/factoryPODetail.aspx?po_id={po_number}"
        driver.get(po_url)
        
        # Quick wait for table
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "table")))
        print("✅ PO page loaded!")
        
        print(f"\n⚡ Step 3: ULTRA FAST processing...")
        
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
        
        # ULTRA FAST processing - no download waiting!
        processed_items = []
        failed_items = []
        
        import time
        start_time = time.time()
        
        for i in range(len(item_links)):
            try:
                hyperlink = item_links[i]
                link_text = hyperlink.text.strip()
                print(f"\n⚡ Item {i+1}/{len(item_links)}: '{link_text}'")
                
                # Quick scroll
                driver.execute_script("arguments[0].scrollIntoView(true);", hyperlink)
                
                # Click immediately
                print(f"  🖱️ Clicking...")
                original_windows = len(driver.window_handles)
                hyperlink.click()
                
                # Quick wait for new window (max 3 seconds)
                new_window_opened = False
                for wait_attempt in range(30):  # 3 seconds total (0.1s each)
                    time.sleep(0.1)
                    if len(driver.window_handles) > original_windows:
                        new_window_opened = True
                        break
                
                if new_window_opened:
                    print(f"  ✅ Window opened")
                    
                    # Switch to new window
                    driver.switch_to.window(driver.window_handles[-1])
                    
                    # Quick find and click download (max 2 seconds)
                    try:
                        download_element = WebDriverWait(driver, 2).until(
                            EC.presence_of_element_located((By.XPATH, "//a[contains(text(), 'Download')]"))
                        )
                        
                        print(f"  📥 Downloading...")
                        download_element.click()
                        
                        # NO WAITING FOR DOWNLOAD COMPLETION!
                        processed_items.append(link_text)
                        print(f"  ✅ Download initiated (not waiting for completion)")
                        
                    except TimeoutException:
                        print(f"  ❌ Download link timeout")
                        failed_items.append(link_text)
                    
                    # Quick close and return
                    driver.close()
                    driver.switch_to.window(driver.window_handles[0])
                    print(f"  🔄 Returned to main")
                    
                else:
                    print(f"  ❌ Window timeout")
                    failed_items.append(link_text)
                
                # Minimal delay between items
                time.sleep(0.5)
                
            except Exception as e:
                print(f"  ❌ Error: {e}")
                failed_items.append(f"Item {i+1}")
                continue
        
        total_time = time.time() - start_time
        
        print(f"\n🎉 ULTRA FAST PROCESSING COMPLETED!")
        print(f"⚡ Total time: {total_time:.1f} seconds")
        print(f"🚀 Average per item: {total_time/len(item_links):.1f} seconds")
        print(f"✅ Processed items: {len(processed_items)}/{len(item_links)}")
        print(f"❌ Failed items: {len(failed_items)}")
        
        # Check downloads after a moment
        print(f"\n⏳ Checking downloads after 10 seconds...")
        time.sleep(10)
        
        final_files = glob.glob(os.path.join(download_folder, "*.pdf"))
        total_size = sum(os.path.getsize(f) for f in final_files)
        
        print(f"\n📊 DOWNLOAD RESULTS:")
        print(f"📄 PDF files found: {len(final_files)}")
        print(f"💾 Total size: {total_size:,} bytes ({total_size/1024/1024:.1f} MB)")
        print(f"📁 Location: {download_folder}")
        
        if final_files:
            print(f"\n📋 Downloaded files:")
            for file_path in final_files:
                file_name = os.path.basename(file_path)
                file_size = os.path.getsize(file_path)
                print(f"  - {file_name} ({file_size:,} bytes)")
        
        print(f"\n🚀 ULTRA FAST METHOD RESULTS:")
        print(f"⚡ Speed: {total_time:.1f}s for {len(item_links)} items ({total_time/len(item_links):.1f}s per item)")
        print(f"🎯 Success rate: {len(final_files)}/{len(item_links)} downloads")
        print(f"💡 Downloads may still be in progress!")
        
        if len(final_files) < len(processed_items):
            print(f"\n⏳ Some downloads may still be completing...")
            print(f"💡 Check the folder again in a few minutes")
        
        print(f"\n🚀 Ready to process all {total_items} items with ultra speed!")
        
    finally:
        print(f"\n🔄 Closing browser...")
        driver.quit()

if __name__ == "__main__":
    ultra_fast_method()
