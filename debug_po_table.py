"""
Debug script to inspect the PO page table structure
"""

import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def debug_po_table():
    """Debug the PO page table to understand its structure"""
    
    # Setup Chrome
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    try:
        driver_path = ChromeDriverManager().install()
        service = Service(driver_path)
        driver = webdriver.Chrome(service=service, options=chrome_options)
    except:
        driver = webdriver.Chrome(options=chrome_options)
    
    wait = WebDriverWait(driver, 15)
    
    try:
        print("=== LOGGING IN ===")
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
        
        print("✅ Login successful")
        
        print("\n=== NAVIGATING TO PO PAGE ===")
        po_url = "https://app.e-brandid.com/Bidnet/bidnet3/factoryPODetail.aspx?po_id=1288060"
        driver.get(po_url)
        time.sleep(5)
        
        print("✅ PO page loaded")
        
        print("\n=== ANALYZING TABLE STRUCTURE ===")
        
        # Find all tables
        tables = driver.find_elements(By.TAG_NAME, "table")
        print(f"Found {len(tables)} tables on page")
        
        for table_idx, table in enumerate(tables):
            print(f"\n--- TABLE {table_idx + 1} ---")
            table_id = table.get_attribute('id')
            table_class = table.get_attribute('class')
            print(f"Table ID: {table_id}, Class: {table_class}")
            
            # Find rows
            rows = table.find_elements(By.TAG_NAME, "tr")
            print(f"Found {len(rows)} rows in table {table_idx + 1}")
            
            for row_idx, row in enumerate(rows):
                print(f"\n  ROW {row_idx + 1}:")
                cells = row.find_elements(By.TAG_NAME, "td")
                if not cells:
                    cells = row.find_elements(By.TAG_NAME, "th")
                    print(f"    Found {len(cells)} header cells")
                else:
                    print(f"    Found {len(cells)} data cells")
                
                for cell_idx, cell in enumerate(cells):
                    cell_text = cell.text.strip()
                    cell_html = cell.get_attribute('innerHTML')[:100] + "..." if len(cell.get_attribute('innerHTML')) > 100 else cell.get_attribute('innerHTML')
                    
                    # Look for links in this cell
                    links = cell.find_elements(By.TAG_NAME, "a")
                    
                    print(f"      CELL {cell_idx + 1}: Text='{cell_text}', Links={len(links)}")
                    if links:
                        for link_idx, link in enumerate(links):
                            link_text = link.text.strip()
                            link_href = link.get_attribute('href')
                            link_onclick = link.get_attribute('onclick')
                            print(f"        LINK {link_idx + 1}: Text='{link_text}', Href='{link_href}', OnClick='{link_onclick}'")
                    
                    if cell_html:
                        print(f"      HTML: {cell_html}")
                
                # Stop after first 5 rows to avoid too much output
                if row_idx >= 4:
                    print(f"    ... (showing first 5 rows only)")
                    break
        
        print("\n=== MANUAL INSPECTION ===")
        print("Browser window is open. Please manually inspect the page.")
        print("Press Enter when you're done inspecting...")
        input()
        
    finally:
        driver.quit()

if __name__ == "__main__":
    debug_po_table()
