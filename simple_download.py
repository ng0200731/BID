"""
Simple downloader - bypasses menu and downloads directly
"""
import os
import sys
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

def download_po_1284678():
    """Download PO 1284678 using hybrid method"""
    driver = None
    try:
        print("Starting download for PO: 1284678")
        print("Method: Hybrid Speed Download")
        print("=" * 40)
        
        driver, download_dir = setup_driver()
        wait = WebDriverWait(driver, 30)
        
        # Navigate to E-BrandID login page
        print("Navigating to E-BrandID login page...")
        driver.get("https://app.e-brandid.com/login/login.aspx")

        # Login
        print("Logging in...")
        username_field = wait.until(EC.presence_of_element_located((By.ID, "txtUserName")))
        password_field = driver.find_element(By.ID, "txtPassword")

        username_field.send_keys("sales10@fuchanghk.com")
        password_field.send_keys("fc31051856")

        login_button = driver.find_element(By.XPATH, "//img[@onclick='return Login();']")
        login_button.click()

        # Wait for login to complete
        wait.until(lambda d: "login" not in d.current_url.lower())
        print("Login successful!")

        # Navigate to PO page
        print(f"Navigating to PO 1284678...")
        po_url = f"https://app.e-brandid.com/Bidnet/bidnet3/factoryPODetail.aspx?po_id=1284678"
        driver.get(po_url)

        # Wait for page to load
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "table")))
        time.sleep(3)

        # Look for download links or buttons
        print("Looking for download options...")
        download_links = driver.find_elements(By.CSS_SELECTOR, "a[href*='.pdf'], button[onclick*='download'], .download")

        if download_links:
            print(f"Found {len(download_links)} download links")
            for i, link in enumerate(download_links[:10]):  # Limit to first 10
                try:
                    print(f"Downloading item {i+1}...")
                    driver.execute_script("arguments[0].click();", link)
                    time.sleep(2)  # Wait between downloads
                except Exception as e:
                    print(f"Error downloading item {i+1}: {e}")
                    continue
        else:
            print("No download links found. The PO might not exist or the website structure has changed.")

        print(f"Downloads saved to: {download_dir}")
        print("Download process completed!")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    download_po_1284678()
