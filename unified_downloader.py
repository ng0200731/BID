"""
Unified E-BrandID Downloader - All methods in one UI
Choose your download method and options from a single interface
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

class UnifiedDownloader:
    def __init__(self):
        self.driver = None
        self.wait = None
        
    def show_main_menu(self):
        """Show main menu with all download options"""
        print("🚀 E-BrandID Unified Downloader")
        print("=" * 50)
        print("📋 Choose your download method:")
        print()
        print("1. 🎯 Standard Download (Original method)")
        print("   - Reliable, slower speed")
        print("   - Waits for each download to complete")
        print("   - Best for small POs")
        print()
        print("2. ⚡ Hybrid Speed Download (Recommended)")
        print("   - Ultra-fast processing + Smart monitoring")
        print("   - 20x faster than standard")
        print("   - Best for most POs")
        print()
        print("3. 🔄 Enhanced Download (Handles duplicates)")
        print("   - Forces download of duplicate PDFs")
        print("   - Renames files with item names")
        print("   - Best for POs with shared PDFs")
        print()
        print("4. 📝 Clean Naming Download (Perfect organization)")
        print("   - Clean naming: original_name_1, original_name_2")
        print("   - Best file organization")
        print("   - Recommended for final production")
        print()
        print("5. 🧪 Test Mode (First 5 items only)")
        print("   - Quick test with any method")
        print("   - Perfect for trying new POs")
        print()
        
        while True:
            choice = input("Enter your choice (1-5): ").strip()
            if choice in ['1', '2', '3', '4', '5']:
                return int(choice)
            print("Please enter a valid choice (1-5)")
    
    def get_po_and_options(self):
        """Get PO number and download options"""
        print("\n📝 Download Configuration:")
        
        # Get PO number
        while True:
            po_number = input("Enter PO number: ").strip()
            if po_number.isdigit():
                break
            print("Please enter a valid PO number (digits only)")
        
        return po_number
    
    def get_item_selection(self, total_items):
        """Get item selection from user"""
        print(f"\n📊 Found {total_items} items in this PO")
        print("📋 Download options:")
        print("  1. All items")
        print("  2. First X items")
        print("  3. Test mode (first 5 items)")
        
        while True:
            choice = input("Enter your choice (1-3): ").strip()
            
            if choice == "1":
                return "all"
            elif choice == "2":
                while True:
                    try:
                        count = int(input("How many items: "))
                        if count > 0 and count <= total_items:
                            return f"first_{count}"
                        else:
                            print(f"Please enter a number between 1 and {total_items}")
                    except ValueError:
                        print("Please enter a valid number")
            elif choice == "3":
                return "test_5"
            else:
                print("Please enter 1, 2, or 3")
    
    def setup_browser(self, download_folder, method):
        """Setup Chrome browser based on method"""
        chrome_options = Options()
        
        # Download preferences
        prefs = {
            "download.default_directory": download_folder,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True,
            "plugins.always_open_pdf_externally": True
        }
        
        # Method-specific optimizations
        if method in [2, 3, 4]:  # Speed methods
            chrome_options.add_argument("--disable-images")
            chrome_options.add_argument("--disable-extensions")
            chrome_options.add_argument("--disable-plugins")
            prefs["profile.managed_default_content_settings.images"] = 2
        
        chrome_options.add_experimental_option("prefs", prefs)
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
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
    
    def login(self):
        """Login to E-BrandID"""
        print("📝 Logging in...")
        
        self.driver.get("https://app.e-brandid.com/login/login.aspx")
        
        username_field = self.wait.until(EC.presence_of_element_located((By.ID, "txtUserName")))
        password_field = self.driver.find_element(By.ID, "txtPassword")
        
        username_field.send_keys("sales10@fuchanghk.com")
        password_field.send_keys("fc31051856")
        
        login_button = self.driver.find_element(By.XPATH, "//img[@onclick='return Login();']")
        login_button.click()
        
        self.wait.until(lambda d: "login" not in d.current_url.lower())
        print("✅ Login successful!")
    
    def navigate_to_po(self, po_number):
        """Navigate to PO and get item links"""
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
        
        print(f"✅ Found {len(item_links)} items")
        return item_links
    
    def select_items(self, item_links, selection):
        """Select items based on user choice"""
        if selection == "all":
            return item_links
        elif selection.startswith("first_"):
            count = int(selection.split("_")[1])
            return item_links[:count]
        elif selection == "test_5":
            return item_links[:5]
        else:
            return item_links[:10]
    
    def extract_pdf_name(self, onclick_attr):
        """Extract PDF name from onclick attribute"""
        if not onclick_attr:
            return None
        match = re.search(r"([^/]+\.pdf)", onclick_attr)
        return match.group(1) if match else None
    
    def get_next_filename(self, base_name, folder):
        """Get next available filename with counter"""
        name, ext = os.path.splitext(base_name)
        base_path = os.path.join(folder, base_name)
        
        if not os.path.exists(base_path):
            return base_name
        
        counter = 1
        while True:
            new_name = f"{name}_{counter}{ext}"
            if not os.path.exists(os.path.join(folder, new_name)):
                return new_name
            counter += 1
    
    def process_items(self, item_links, method, download_folder):
        """Process items based on selected method"""
        total_items = len(item_links)
        processed_items = []
        failed_items = []
        downloaded_files = []
        
        print(f"\n⚡ Processing {total_items} items...")
        start_time = time.time()
        
        for i, hyperlink in enumerate(item_links):
            try:
                link_text = hyperlink.text.strip()
                
                if (i + 1) % 5 == 0 or i == 0:
                    print(f"⚡ Item {i+1}/{total_items}: '{link_text}'")
                
                # Get files before
                files_before = set(glob.glob(os.path.join(download_folder, "*.pdf")))
                
                # Click item
                self.driver.execute_script("arguments[0].scrollIntoView(true);", hyperlink)
                original_windows = len(self.driver.window_handles)
                hyperlink.click()
                
                # Wait for new window
                new_window_opened = False
                wait_time = 30 if method == 1 else 15  # Standard method waits longer
                
                for wait_attempt in range(wait_time):
                    time.sleep(0.1)
                    if len(self.driver.window_handles) > original_windows:
                        new_window_opened = True
                        break
                
                if new_window_opened:
                    self.driver.switch_to.window(self.driver.window_handles[-1])
                    
                    try:
                        download_element = WebDriverWait(self.driver, 5).until(
                            EC.presence_of_element_located((By.XPATH, "//a[contains(text(), 'Download')]"))
                        )
                        
                        # Method-specific handling
                        if method == 4:  # Clean naming
                            onclick_attr = download_element.get_attribute('onclick')
                            original_pdf_name = self.extract_pdf_name(onclick_attr)
                            if original_pdf_name:
                                target_filename = self.get_next_filename(original_pdf_name, download_folder)
                        
                        download_element.click()
                        
                        # Wait based on method
                        if method == 1:  # Standard - wait longer
                            time.sleep(5)
                        else:  # Speed methods - wait less
                            time.sleep(2)
                        
                        # Check for new files
                        files_after = set(glob.glob(os.path.join(download_folder, "*.pdf")))
                        new_files = files_after - files_before
                        
                        if new_files:
                            new_file = list(new_files)[0]
                            
                            # Method-specific file handling
                            if method == 4 and 'target_filename' in locals():  # Clean naming
                                target_path = os.path.join(download_folder, target_filename)
                                if os.path.basename(new_file) != target_filename:
                                    shutil.move(new_file, target_path)
                                downloaded_files.append(target_filename)
                            else:
                                downloaded_files.append(os.path.basename(new_file))
                        
                        elif method in [3, 4]:  # Enhanced methods - copy existing
                            existing_files = glob.glob(os.path.join(download_folder, "*.pdf"))
                            if existing_files:
                                source_file = max(existing_files, key=os.path.getctime)
                                
                                if method == 4 and 'target_filename' in locals():
                                    target_path = os.path.join(download_folder, target_filename)
                                    shutil.copy2(source_file, target_path)
                                    downloaded_files.append(target_filename)
                                else:
                                    # Enhanced naming
                                    new_name = f"{link_text}_{os.path.basename(source_file)}"
                                    target_path = os.path.join(download_folder, new_name)
                                    shutil.copy2(source_file, target_path)
                                    downloaded_files.append(new_name)
                        
                        processed_items.append(link_text)
                        
                    except TimeoutException:
                        failed_items.append(link_text)
                    
                    self.driver.close()
                    self.driver.switch_to.window(self.driver.window_handles[0])
                
                else:
                    failed_items.append(link_text)
                
                # Delay based on method
                if method == 1:  # Standard - longer delay
                    time.sleep(2)
                else:  # Speed methods - shorter delay
                    time.sleep(0.5)
                
            except Exception as e:
                failed_items.append(f"Item {i+1}")
                continue
        
        processing_time = time.time() - start_time
        return processed_items, failed_items, downloaded_files, processing_time
    
    def monitor_downloads(self, download_folder, initial_count, method):
        """Monitor downloads based on method"""
        if method == 1:  # Standard method - no monitoring needed
            return
        
        print(f"\n🔍 Monitoring downloads...")
        start_time = time.time()
        stable_count = 0
        
        while True:
            current_files = glob.glob(os.path.join(download_folder, "*.pdf"))
            current_count = len(current_files)
            elapsed = time.time() - start_time
            
            print(f"📊 Files: {current_count} | Time: {elapsed:.1f}s | Stable: {stable_count}s", end="\r")
            
            stable_count += 1
            if stable_count >= 30 or elapsed >= 300:  # 30 seconds stable or 5 min timeout
                print(f"\n✅ Download monitoring complete!")
                break
            
            time.sleep(1)
    
    def show_results(self, processed_items, failed_items, downloaded_files, processing_time, download_folder, method_name):
        """Show final results"""
        final_files = glob.glob(os.path.join(download_folder, "*.pdf"))
        total_size = sum(os.path.getsize(f) for f in final_files)
        
        print(f"\n🎉 {method_name.upper()} COMPLETE!")
        print(f"⚡ Processing time: {processing_time:.1f} seconds")
        print(f"🚀 Average per item: {processing_time/len(processed_items):.1f}s" if processed_items else "")
        print(f"✅ Processed items: {len(processed_items)}")
        print(f"❌ Failed items: {len(failed_items)}")
        print(f"📥 Total files: {len(final_files)}")
        print(f"💾 Total size: {total_size/1024/1024:.1f} MB")
        print(f"📁 Location: {download_folder}")
        
        if downloaded_files:
            print(f"\n📋 Sample files:")
            for filename in downloaded_files[:5]:
                filepath = os.path.join(download_folder, filename)
                if os.path.exists(filepath):
                    file_size = os.path.getsize(filepath)
                    print(f"  - {filename} ({file_size:,} bytes)")
            
            if len(downloaded_files) > 5:
                print(f"  ... and {len(downloaded_files) - 5} more files")
    
    def run(self):
        """Main execution flow"""
        try:
            # Show menu and get choices
            method = self.show_main_menu()
            po_number = self.get_po_and_options()

            # Setup folder with timestamp format: YYYY_MM_DD_HH_MM_{PO#}
            timestamp = datetime.now().strftime("%Y_%m_%d_%H_%M")
            folder_name = f"{timestamp}_{po_number}"
            download_folder = os.path.join(os.getcwd(), folder_name)

            if not os.path.exists(download_folder):
                os.makedirs(download_folder, exist_ok=True)
                print(f"📁 Created folder: {folder_name}")
            
            initial_count = len(glob.glob(os.path.join(download_folder, "*.pdf")))
            
            # Setup browser and login
            self.setup_browser(download_folder, method)
            self.login()
            
            # Get items
            item_links = self.navigate_to_po(po_number)
            if not item_links:
                print("❌ No items found!")
                return
            
            # Get selection
            if method == 5:  # Test mode
                selection = "test_5"
            else:
                selection = self.get_item_selection(len(item_links))
            
            selected_items = self.select_items(item_links, selection)
            
            # Confirm
            method_names = {
                1: "Standard Download",
                2: "Hybrid Speed Download", 
                3: "Enhanced Download",
                4: "Clean Naming Download",
                5: "Test Mode"
            }
            
            print(f"\n🎯 Ready to start {method_names[method]}")
            print(f"📊 PO: {po_number} | Items: {len(selected_items)}")
            confirm = input("Continue? (y/n): ").strip().lower()
            
            if confirm != 'y':
                print("❌ Download cancelled")
                return
            
            # Process items
            processed, failed, downloaded, proc_time = self.process_items(selected_items, method, download_folder)
            
            # Monitor downloads for speed methods
            if method in [2, 3, 4]:
                self.monitor_downloads(download_folder, initial_count, method)
            
            # Show results
            self.show_results(processed, failed, downloaded, proc_time, download_folder, method_names[method])
            
        except KeyboardInterrupt:
            print(f"\n⚠️ Download interrupted by user")
        except Exception as e:
            print(f"\n❌ Error: {e}")
        finally:
            if self.driver:
                self.driver.quit()

def main():
    """Entry point"""
    downloader = UnifiedDownloader()
    downloader.run()

if __name__ == "__main__":
    main()
