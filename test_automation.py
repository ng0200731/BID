"""
Test automation script - downloads first 3 items only
"""

from ebrandid_downloader import EBrandIDDownloader
import os

def test_automation():
    """Test the automation with just 3 items"""
    
    print("🚀 Starting E-BrandID Test Automation...")
    print("This will download the first 3 items only as a test.")
    
    # Create downloader
    downloader = EBrandIDDownloader(headless=False)
    
    # Setup driver
    if not downloader.setup_driver():
        print("❌ Failed to setup browser")
        return
    
    try:
        # Login
        print("\n📝 Step 1: Logging in...")
        success, message = downloader.milestone_1_login()
        if not success:
            print(f"❌ Login failed: {message}")
            return
        print("✅ Login successful!")
        
        # Navigate to PO
        print("\n🔍 Step 2: Navigating to PO page...")
        po_number = "1288060"
        success, message = downloader.milestone_2_navigate_to_po(po_number)
        if not success:
            print(f"❌ Navigation failed: {message}")
            return
        print("✅ Navigation successful!")
        
        # Test download process with first 3 items
        print("\n📥 Step 3: Testing download process (first 3 items)...")
        
        # Find all tables and look for the one with item links
        from selenium.webdriver.common.by import By

        tables = downloader.driver.find_elements(By.TAG_NAME, "table")
        print(f"Found {len(tables)} tables on page")

        item_links = []
        for i, table in enumerate(tables):
            links = table.find_elements(By.XPATH, ".//a[contains(@onclick, 'openItemDetail')]")
            if links:
                item_links = links
                print(f"Found table {i+1} with {len(item_links)} item links")
                break
        
        if not item_links:
            print("❌ No item links found!")
            return
        
        # Create folder
        po_folder = os.path.join(os.getcwd(), str(po_number))
        os.makedirs(po_folder, exist_ok=True)
        print(f"Created folder: {po_folder}")
        
        # Test first 3 items
        downloaded_count = 0
        for i in range(min(3, len(item_links))):
            try:
                hyperlink = item_links[i]
                link_text = hyperlink.text.strip()
                print(f"\n📄 Processing item {i+1}/3: '{link_text}'")
                
                # Scroll to element
                downloader.driver.execute_script("arguments[0].scrollIntoView(true);", hyperlink)
                downloader.driver.implicitly_wait(1)
                
                # Click the hyperlink (opens new window)
                downloader.driver.execute_script("arguments[0].click();", hyperlink)
                downloader.driver.implicitly_wait(3)
                
                # Check for new window
                windows = downloader.driver.window_handles
                if len(windows) > 1:
                    print(f"  ✅ New window opened, switching to it...")
                    
                    # Switch to new window
                    downloader.driver.switch_to.window(windows[-1])
                    downloader.driver.implicitly_wait(2)
                    
                    # Look for download link
                    try:
                        download_element = downloader.driver.find_element(By.XPATH, "//a[contains(text(), 'Download')]")
                        print(f"  ✅ Found download link")
                        
                        # Click download
                        downloader.driver.execute_script("arguments[0].click();", download_element)
                        downloader.driver.implicitly_wait(2)
                        
                        downloaded_count += 1
                        print(f"  ✅ Download initiated for '{link_text}'")
                        
                    except Exception as e:
                        print(f"  ❌ Could not find download link: {e}")
                    
                    # Close new window and return to main window
                    downloader.driver.close()
                    downloader.driver.switch_to.window(windows[0])
                    print(f"  ✅ Closed new window, returned to main window")
                    
                else:
                    print(f"  ❌ No new window opened")
                
            except Exception as e:
                print(f"  ❌ Error processing item {i+1}: {e}")
        
        print(f"\n🎉 Test completed!")
        print(f"✅ Successfully processed {downloaded_count}/3 items")
        print(f"📁 Files should be downloading to: {po_folder}")
        
    finally:
        downloader.close_driver()

if __name__ == "__main__":
    test_automation()
