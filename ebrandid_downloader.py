"""
E-BrandID File Downloader
Automated tool to login to e-brandid system and download all files from a PO page.

Milestones:
1. Login to e-brandid system
2. Navigate to specific PO detail page
3. Download all files from the table and organize in folders
"""

import os
import time
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
import urllib.parse
from pathlib import Path

class EBrandIDDownloader:
    def __init__(self, headless=False, download_path=None):
        self.headless = headless
        self.driver = None
        self.wait_timeout = 15
        self.download_path = download_path or os.getcwd()
        self.session = requests.Session()
        
    def setup_driver(self):
        """Setup Chrome WebDriver with download preferences"""
        try:
            chrome_options = Options()

            # Download preferences
            prefs = {
                "download.default_directory": self.download_path,
                "download.prompt_for_download": False,
                "download.directory_upgrade": True,
                "safebrowsing.enabled": True
            }
            chrome_options.add_experimental_option("prefs", prefs)

            if self.headless:
                chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--disable-web-security")
            chrome_options.add_argument("--allow-running-insecure-content")
            chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")

            # Try to install and setup ChromeDriver automatically
            try:
                print("Installing ChromeDriver...")
                driver_path = ChromeDriverManager().install()
                print(f"ChromeDriver installed at: {driver_path}")
                service = Service(driver_path)
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
            except Exception as e:
                print(f"ChromeDriverManager failed: {e}")
                print("Trying to use system Chrome...")
                # Try without service (use system Chrome)
                self.driver = webdriver.Chrome(options=chrome_options)

            self.wait = WebDriverWait(self.driver, self.wait_timeout)
            print("✅ WebDriver setup successful!")
            return True
        except Exception as e:
            print(f"Failed to setup WebDriver: {e}")
            print("Make sure Chrome browser is installed on your system.")
            return False
    
    def close_driver(self):
        """Close the WebDriver"""
        if self.driver:
            self.driver.quit()
            self.driver = None
    
    def milestone_1_login(self, username="sales10@fuchanghk.com", password="fc31051856"):
        """
        Milestone 1: Login to e-brandid system
        """
        login_url = "https://app.e-brandid.com/login/login.aspx"
        
        try:
            print("Milestone 1: Starting login process...")
            print(f"Navigating to: {login_url}")
            
            self.driver.get(login_url)
            time.sleep(3)
            
            # Wait for login form to appear
            print("Waiting for login form...")
            
            # Find username field
            username_selectors = [
                "input[type='text']",
                "input[name*='user']",
                "input[name*='User']",
                "input[id*='user']",
                "input[id*='User']"
            ]
            
            username_element = None
            for selector in username_selectors:
                try:
                    username_element = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                    print(f"Found username field: {selector}")
                    break
                except TimeoutException:
                    continue
            
            if not username_element:
                return False, "Could not find username field"
            
            # Find password field
            try:
                password_element = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='password']")))
                print("Found password field")
            except TimeoutException:
                return False, "Could not find password field"
            
            # Enter credentials
            print(f"Entering username: {username}")
            username_element.clear()
            username_element.send_keys(username)
            
            print("Entering password")
            password_element.clear()
            password_element.send_keys(password)
            
            time.sleep(1)
            
            # Find and click login button (it's an image with onclick="return Login();")
            try:
                # First try to find the image with Login() onclick
                login_element = self.driver.find_element(By.XPATH, "//img[@onclick='return Login();']")
                print("Found login button: image with Login() onclick")
            except NoSuchElementException:
                try:
                    # Alternative: try any image with onclick containing "Login"
                    login_element = self.driver.find_element(By.XPATH, "//img[contains(@onclick, 'Login')]")
                    print("Found login button: image with Login onclick")
                except NoSuchElementException:
                    # Fallback: try submitting form by pressing Enter
                    try:
                        print("Login button not found, trying form submission with Enter key...")
                        from selenium.webdriver.common.keys import Keys
                        password_element.send_keys(Keys.RETURN)
                        time.sleep(5)

                        # Check if login was successful
                        current_url = self.driver.current_url
                        if "login" not in current_url.lower():
                            print(f"✅ Login successful via Enter key! Current URL: {current_url}")
                            return True, "Login successful"
                        else:
                            return False, "Login failed - still on login page after Enter"
                    except Exception as e:
                        return False, f"Could not find login button or submit form: {e}"

            print("Clicking login button...")
            login_element.click()
            
            # Wait for login to complete
            time.sleep(5)
            
            # Check if login was successful
            current_url = self.driver.current_url
            if "login" not in current_url.lower():
                print(f"✅ Login successful! Current URL: {current_url}")
                return True, "Login successful"
            else:
                return False, "Login failed - still on login page"
                
        except Exception as e:
            return False, f"Login error: {str(e)}"
    
    def milestone_2_navigate_to_po(self, po_number):
        """
        Milestone 2: Navigate to specific PO detail page
        """
        try:
            print(f"Milestone 2: Navigating to PO {po_number}...")
            
            po_url = f"https://app.e-brandid.com/Bidnet/bidnet3/factoryPODetail.aspx?po_id={po_number}"
            print(f"Navigating to: {po_url}")
            
            self.driver.get(po_url)
            time.sleep(5)
            
            # Wait for page to load
            try:
                self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "table")))
                print("✅ PO page loaded successfully")
                return True, f"Successfully navigated to PO {po_number}"
            except TimeoutException:
                return False, "PO page did not load properly"
                
        except Exception as e:
            return False, f"Navigation error: {str(e)}"
    
    def milestone_3_download_files(self, po_number):
        """
        Milestone 3: Download all files from the table
        """
        try:
            print(f"Milestone 3: Starting file downloads for PO {po_number}...")
            
            # Create folder for PO
            po_folder = os.path.join(self.download_path, str(po_number))
            os.makedirs(po_folder, exist_ok=True)
            print(f"Created folder: {po_folder}")
            
            # Update download path for this PO
            self.driver.execute_cdp_cmd('Page.setDownloadBehavior', {
                'behavior': 'allow',
                'downloadPath': po_folder
            })
            
            # Find all tables and look for the one with item links
            tables = self.driver.find_elements(By.TAG_NAME, "table")
            print(f"Found {len(tables)} tables on page")

            table = None
            item_links = []

            # Search through all tables to find the one with item links
            for i, tbl in enumerate(tables):
                links = tbl.find_elements(By.XPATH, ".//a[contains(@onclick, 'openItemDetail')]")
                if links:
                    table = tbl
                    item_links = links
                    print(f"Found table {i+1} with {len(item_links)} item links")
                    break

            if not table:
                return False, "Could not find table with item links on page"

            downloaded_files = []

            for i, hyperlink in enumerate(item_links, 1):
                try:
                    print(f"\nProcessing item {i}/{len(item_links)}...")

                    link_text = hyperlink.text.strip()
                    onclick_attr = hyperlink.get_attribute('onclick')
                    print(f"Item {i}: Found hyperlink '{link_text}' with onclick: {onclick_attr}")

                    # Scroll to element to make sure it's visible
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", hyperlink)
                    time.sleep(1)

                    # Click the hyperlink (opens new window)
                    self.driver.execute_script("arguments[0].click();", hyperlink)
                    time.sleep(3)

                    # Check for new window
                    windows = self.driver.window_handles
                    if len(windows) > 1:
                        print(f"Item {i}: New window opened, switching to it...")

                        # Switch to new window
                        self.driver.switch_to.window(windows[-1])
                        time.sleep(2)

                        # Look for download link in new window
                        try:
                            download_element = self.driver.find_element(By.XPATH, "//a[contains(text(), 'Download')]")
                            print(f"Item {i}: Found download link in new window")

                            # Click download
                            print(f"Item {i}: Clicking download...")
                            self.driver.execute_script("arguments[0].click();", download_element)
                            time.sleep(2)

                            downloaded_files.append(link_text)
                            print(f"Item {i}: ✅ Download initiated for '{link_text}'")

                        except NoSuchElementException:
                            print(f"Item {i}: Could not find download link in new window")

                        # Close new window and return to main window
                        self.driver.close()
                        self.driver.switch_to.window(windows[0])
                        print(f"Item {i}: Closed new window, returned to main window")

                    else:
                        print(f"Item {i}: No new window opened, skipping")

                    time.sleep(1)

                except Exception as e:
                    print(f"Item {i}: Error processing item: {e}")
                    continue
            
            print(f"\n✅ Milestone 3 completed!")
            print(f"Processed {len(downloaded_files)} files")
            print(f"Files saved to: {po_folder}")
            
            return True, f"Downloaded {len(downloaded_files)} files to {po_folder}"
            
        except Exception as e:
            return False, f"Download error: {str(e)}"
    
    def run_complete_process(self, po_number, username="sales10@fuchanghk.com", password="fc31051856"):
        """
        Run the complete 3-milestone process
        """
        if not self.setup_driver():
            return False, "Failed to setup browser"
        
        try:
            # Milestone 1: Login
            success, message = self.milestone_1_login(username, password)
            if not success:
                return False, f"Milestone 1 failed: {message}"
            
            # Milestone 2: Navigate to PO
            success, message = self.milestone_2_navigate_to_po(po_number)
            if not success:
                return False, f"Milestone 2 failed: {message}"
            
            # Milestone 3: Download files
            success, message = self.milestone_3_download_files(po_number)
            if not success:
                return False, f"Milestone 3 failed: {message}"
            
            return True, "All milestones completed successfully!"
            
        finally:
            self.close_driver()


if __name__ == "__main__":
    # Test the downloader
    downloader = EBrandIDDownloader(headless=False)  # Set to True to hide browser
    
    po_number = "1288060"  # Test PO number
    
    print("Starting E-BrandID File Downloader...")
    print(f"Target PO: {po_number}")
    
    success, message = downloader.run_complete_process(po_number)
    
    if success:
        print(f"\n🎉 SUCCESS: {message}")
    else:
        print(f"\n❌ FAILED: {message}")
