"""
E-BrandID Production Downloader
Interactive, configurable, and robust PDF downloader
"""

import os
import glob
import time
import argparse
import json
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager

class EBrandIDDownloader:
    def __init__(self, headless=False, timeout=5):
        self.headless = headless
        self.timeout_minutes = timeout
        self.driver = None
        self.wait = None
        
    def setup_browser(self, download_folder):
        """Setup Chrome browser with optimizations"""
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
        
        # Speed optimizations
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-images")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-plugins")
        chrome_options.add_argument("--disable-background-timer-throttling")
        
        if self.headless:
            chrome_options.add_argument("--headless")
        
        # Disable image loading via prefs
        prefs["profile.managed_default_content_settings.images"] = 2
        chrome_options.add_experimental_option("prefs", prefs)
        
        try:
            driver_path = ChromeDriverManager().install()
            service = Service(driver_path)
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
        except:
            self.driver = webdriver.Chrome(options=chrome_options)
        
        self.wait = WebDriverWait(self.driver, 10)
        
        # Set download behavior
        self.driver.execute_cdp_cmd('Page.setDownloadBehavior', {
            'behavior': 'allow',
            'downloadPath': download_folder
        })
        
        return True
    
    def login(self, username="sales10@fuchanghk.com", password="fc31051856"):
        """Login to E-BrandID"""
        print("📝 Logging in...")
        
        self.driver.get("https://app.e-brandid.com/login/login.aspx")
        
        username_field = self.wait.until(EC.presence_of_element_located((By.ID, "txtUserName")))
        password_field = self.driver.find_element(By.ID, "txtPassword")
        
        username_field.send_keys(username)
        password_field.send_keys(password)
        
        login_button = self.driver.find_element(By.XPATH, "//img[@onclick='return Login();']")
        login_button.click()
        
        self.wait.until(lambda d: "login" not in d.current_url.lower())
        print("✅ Login successful!")
        return True
    
    def navigate_to_po(self, po_number):
        """Navigate to PO page and get item links"""
        print(f"🔍 Navigating to PO {po_number}...")
        
        po_url = f"https://app.e-brandid.com/Bidnet/bidnet3/factoryPODetail.aspx?po_id={po_number}"
        self.driver.get(po_url)
        
        self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "table")))
        
        # Find item links
        tables = self.driver.find_elements(By.TAG_NAME, "table")
        item_links = []
        for table in tables:
            links = table.find_elements(By.XPATH, ".//a[contains(@onclick, 'openItemDetail')]")
            if links:
                item_links = links
                break
        
        print(f"✅ Found {len(item_links)} items in PO {po_number}")
        return item_links
    
    def monitor_downloads(self, download_folder, initial_count):
        """Intelligent download monitoring"""
        print(f"\n🔍 Monitoring downloads...")
        
        start_time = time.time()
        last_file_count = initial_count
        stable_count = 0
        stable_threshold = 30
        
        while True:
            current_files = glob.glob(os.path.join(download_folder, "*.pdf"))
            current_count = len(current_files)
            
            elapsed_time = time.time() - start_time
            elapsed_minutes = elapsed_time / 60
            
            print(f"📊 Files: {current_count} | Elapsed: {elapsed_minutes:.1f}min | Stable: {stable_count}s", end="\r")
            
            if current_count > last_file_count:
                print(f"\n📥 New download! Files: {last_file_count} → {current_count}")
                last_file_count = current_count
                stable_count = 0
            else:
                stable_count += 1
            
            if stable_count >= stable_threshold:
                print(f"\n✅ Downloads stabilized!")
                break
            
            if elapsed_minutes >= self.timeout_minutes:
                print(f"\n⏰ Timeout reached ({self.timeout_minutes} minutes)")
                break
            
            time.sleep(1)
        
        new_downloads = current_count - initial_count
        return new_downloads, current_files
    
    def process_items(self, item_links, selection_info):
        """Process selected items with hybrid speed method"""
        selected_links = self.select_items(item_links, selection_info)
        
        if not selected_links:
            print("❌ No items selected for download")
            return [], []
        
        print(f"\n⚡ Processing {len(selected_links)} items with hybrid speed method...")
        
        processed_items = []
        failed_items = []
        
        start_time = time.time()
        
        for i, hyperlink in enumerate(selected_links):
            try:
                link_text = hyperlink.text.strip()
                
                if (i + 1) % 5 == 0 or i == 0:
                    print(f"⚡ Item {i+1}/{len(selected_links)}: '{link_text}'")
                
                # Quick scroll and click
                self.driver.execute_script("arguments[0].scrollIntoView(true);", hyperlink)
                original_windows = len(self.driver.window_handles)
                hyperlink.click()
                
                # Quick wait for new window
                new_window_opened = False
                for wait_attempt in range(30):  # 3 seconds total
                    time.sleep(0.1)
                    if len(self.driver.window_handles) > original_windows:
                        new_window_opened = True
                        break
                
                if new_window_opened:
                    # Switch to new window
                    self.driver.switch_to.window(self.driver.window_handles[-1])
                    
                    # Quick find and click download
                    try:
                        download_element = WebDriverWait(self.driver, 2).until(
                            EC.presence_of_element_located((By.XPATH, "//a[contains(text(), 'Download')]"))
                        )
                        download_element.click()
                        processed_items.append(link_text)
                        
                    except TimeoutException:
                        failed_items.append(link_text)
                    
                    # Quick close and return
                    self.driver.close()
                    self.driver.switch_to.window(self.driver.window_handles[0])
                    
                else:
                    failed_items.append(link_text)
                
                time.sleep(0.5)  # Minimal delay
                
            except Exception as e:
                failed_items.append(f"Item {i+1}")
                continue
        
        processing_time = time.time() - start_time
        print(f"\n✅ Processing completed in {processing_time:.1f} seconds")
        print(f"⚡ Average: {processing_time/len(selected_links):.1f}s per item")
        
        return processed_items, failed_items
    
    def select_items(self, item_links, selection_info):
        """Select items based on user choice"""
        total_items = len(item_links)
        
        if selection_info == "all":
            return item_links
        elif selection_info.startswith("first_"):
            count = int(selection_info.split("_")[1])
            return item_links[:min(count, total_items)]
        elif selection_info.startswith("range_"):
            range_str = selection_info.split("_")[1]
            start, end = map(int, range_str.split("-"))
            return item_links[start-1:end]
        elif selection_info.startswith("pattern_"):
            pattern = selection_info.split("_", 1)[1]
            pattern = pattern.replace("*", "")
            return [link for link in item_links if pattern.lower() in link.text.lower()]
        elif selection_info == "test_5":
            return item_links[:5]
        else:
            return item_links[:10]  # Default
    
    def close(self):
        """Close browser"""
        if self.driver:
            self.driver.quit()

def handle_partial_download(total_items):
    """Handle user selection for partial downloads"""
    print(f"\n📊 Found {total_items} items in this PO")
    print("📋 Download options:")
    print("  1. First X items (quick test)")
    print("  2. Specific range (e.g., items 10-50)")
    print("  3. Pattern matching (e.g., *CARE*, *BLK)")
    print("  4. Test mode (first 5 items)")
    print("  5. Small batch (first 25 items)")
    
    while True:
        choice = input("Enter your choice (1-5): ").strip()
        
        if choice == "1":
            while True:
                try:
                    count = int(input("How many items: "))
                    if count > 0 and count <= total_items:
                        return f"first_{count}"
                    else:
                        print(f"Please enter a number between 1 and {total_items}")
                except ValueError:
                    print("Please enter a valid number")
        
        elif choice == "2":
            range_input = input("Enter range (e.g., 10-50): ").strip()
            try:
                start, end = map(int, range_input.split("-"))
                if 1 <= start <= end <= total_items:
                    return f"range_{range_input}"
                else:
                    print(f"Please enter a valid range between 1 and {total_items}")
            except:
                print("Please enter range in format: start-end (e.g., 10-50)")
        
        elif choice == "3":
            pattern = input("Enter pattern (use * for wildcard): ").strip()
            if pattern:
                return f"pattern_{pattern}"
            else:
                print("Please enter a pattern")
        
        elif choice == "4":
            return "test_5"
        
        elif choice == "5":
            return "first_25"
        
        else:
            print("Please enter a valid choice (1-5)")

def setup_download_folder(po_number):
    """Setup download folder with user interaction"""
    base_folder = os.path.join(os.getcwd(), str(po_number))
    
    if os.path.exists(base_folder):
        existing_files = glob.glob(os.path.join(base_folder, "*.pdf"))
        if existing_files:
            print(f"\n📁 Folder already contains {len(existing_files)} PDF files")
            print("❓ What would you like to do?")
            print("  1. Remove existing files and start fresh")
            print("  2. Create new folder with timestamp")
            print("  3. Continue (may have duplicates)")
            
            while True:
                choice = input("Enter your choice (1-3): ").strip()
                if choice == "1":
                    import shutil
                    shutil.rmtree(base_folder)
                    os.makedirs(base_folder, exist_ok=True)
                    print("🗑️ Removed existing files")
                    return base_folder
                elif choice == "2":
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    timestamped_folder = f"{base_folder}_{timestamp}"
                    os.makedirs(timestamped_folder, exist_ok=True)
                    print(f"📁 Created new folder: {timestamped_folder}")
                    return timestamped_folder
                elif choice == "3":
                    print("📁 Using existing folder")
                    return base_folder
                else:
                    print("Please enter 1, 2, or 3")
    else:
        os.makedirs(base_folder, exist_ok=True)
        print(f"📁 Created new folder: {base_folder}")
        return base_folder

def interactive_mode():
    """Interactive mode for user-friendly operation"""
    print("🚀 E-BrandID Production Downloader")
    print("=" * 50)
    
    # Get PO number
    while True:
        po_number = input("Enter PO number: ").strip()
        if po_number.isdigit():
            break
        else:
            print("Please enter a valid PO number (digits only)")
    
    # Setup folder
    download_folder = setup_download_folder(po_number)
    initial_files = glob.glob(os.path.join(download_folder, "*.pdf"))
    initial_count = len(initial_files)
    
    # Initialize downloader
    downloader = EBrandIDDownloader()
    
    try:
        # Setup browser
        print("\n🌐 Setting up browser...")
        downloader.setup_browser(download_folder)
        
        # Login
        downloader.login()
        
        # Navigate to PO
        item_links = downloader.navigate_to_po(po_number)
        
        if not item_links:
            print("❌ No items found in this PO")
            return
        
        # Ask about download scope
        download_all = input(f"\nDownload all {len(item_links)} items? (y/n): ").strip().lower()
        
        if download_all == 'y':
            selection_info = "all"
            print(f"✅ Will download all {len(item_links)} items")
        else:
            selection_info = handle_partial_download(len(item_links))
        
        # Confirm before starting
        print(f"\n🎯 Ready to start download with selection: {selection_info}")
        confirm = input("Continue? (y/n): ").strip().lower()
        
        if confirm != 'y':
            print("❌ Download cancelled")
            return
        
        # Process items
        print(f"\n🚀 Starting hybrid speed download...")
        start_time = time.time()
        
        processed_items, failed_items = downloader.process_items(item_links, selection_info)
        
        # Monitor downloads
        new_downloads, final_files = downloader.monitor_downloads(download_folder, initial_count)
        
        # Results
        total_time = time.time() - start_time
        total_size = sum(os.path.getsize(f) for f in final_files)
        
        print(f"\n🎉 DOWNLOAD COMPLETE!")
        print(f"⚡ Total time: {total_time/60:.1f} minutes")
        print(f"📥 New downloads: {new_downloads}")
        print(f"✅ Processed items: {len(processed_items)}")
        print(f"❌ Failed items: {len(failed_items)}")
        print(f"💾 Total size: {total_size/1024/1024:.1f} MB")
        print(f"📁 Location: {download_folder}")
        
        if new_downloads > 0:
            print(f"\n📋 Sample downloaded files:")
            for file_path in final_files[-5:]:  # Show last 5
                file_name = os.path.basename(file_path)
                file_size = os.path.getsize(file_path)
                print(f"  - {file_name} ({file_size:,} bytes)")
        
    except KeyboardInterrupt:
        print(f"\n⚠️ Download interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
    finally:
        downloader.close()

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='E-BrandID Production Downloader')
    parser.add_argument('--po', type=str, help='PO number to download')
    parser.add_argument('--all', action='store_true', help='Download all items')
    parser.add_argument('--limit', type=int, help='Limit number of items')
    parser.add_argument('--headless', action='store_true', help='Run headless')
    parser.add_argument('--timeout', type=int, default=5, help='Download timeout in minutes')
    
    args = parser.parse_args()
    
    if args.po:
        # Command line mode
        print(f"🚀 Command line mode: PO {args.po}")
        # TODO: Implement command line mode
        print("Command line mode not yet implemented. Use interactive mode.")
        interactive_mode()
    else:
        # Interactive mode
        interactive_mode()

if __name__ == "__main__":
    main()
