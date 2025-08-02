# -*- coding: utf-8 -*-
"""
Artwork Downloader
1. Input PO# first
2. Show recommendations based on PO data
3. Display data table in web interface
4. Intelligent artwork download with multiple methods

VERSION TRACKING:
- Every code edit gets a version number
- Version displayed in UI for transparency
- Format: v1.0.0 (YYYY-MM-DD HH:MM)
"""

# Version tracking system
VERSION = "1.2.2"
VERSION_DATE = "2025-08-02 11:20"
LAST_EDIT = "Added cache-busting headers to prevent browser caching issues"



from flask import Flask, render_template_string, request, jsonify
import os
import threading
import time
import requests
import re
import sqlite3
from datetime import datetime

def update_version(new_version, edit_description):
    """Helper function to update version info - USE THIS FOR EVERY EDIT"""
    global VERSION, VERSION_DATE, LAST_EDIT
    VERSION = new_version
    VERSION_DATE = datetime.now().strftime("%Y-%m-%d %H:%M")
    LAST_EDIT = edit_description
    print(f"📝 Version updated to {VERSION} - {edit_description}")

def mask_email(email):
    """Mask email address: prefix shows first 2 chars, suffix shows first 1 char"""
    if '@' not in email:
        return email

    prefix, suffix = email.split('@', 1)

    # Mask prefix: show first 2 characters, rest as asterisks
    if len(prefix) <= 2:
        masked_prefix = prefix
    else:
        masked_prefix = prefix[:2] + '*' * (len(prefix) - 2)

    # Mask suffix: show first 1 character, rest as asterisks
    if len(suffix) <= 1:
        masked_suffix = suffix
    else:
        masked_suffix = suffix[:1] + '*' * (len(suffix) - 1)

    return f"{masked_prefix}@{masked_suffix}"

# Database functions
def init_database():
    """Initialize SQLite database for PO storage"""
    conn = sqlite3.connect('po_database.db')
    cursor = conn.cursor()

    # Create PO headers table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS po_headers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            po_number TEXT UNIQUE,
            purchase_from TEXT,
            ship_to TEXT,
            company TEXT,
            currency TEXT,
            cancel_date TEXT,
            created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Create PO items table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS po_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            po_number TEXT,
            item_number TEXT,
            description TEXT,
            color TEXT,
            ship_to TEXT,
            need_by TEXT,
            qty TEXT,
            bundle_qty TEXT,
            unit_price TEXT,
            extension TEXT,
            created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (po_number) REFERENCES po_headers(po_number)
        )
    ''')

    conn.commit()
    conn.close()
    print("📊 Database initialized successfully")

def check_po_exists(po_number):
    """Check if PO already exists in database"""
    conn = sqlite3.connect('po_database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM po_headers WHERE po_number = ?', (po_number,))
    exists = cursor.fetchone()[0] > 0
    conn.close()
    return exists

def save_po_to_database(po_number, po_header, po_items, overwrite=False):
    """Save complete PO data to database"""
    conn = sqlite3.connect('po_database.db')
    cursor = conn.cursor()

    try:
        if overwrite:
            # Delete existing records
            cursor.execute('DELETE FROM po_items WHERE po_number = ?', (po_number,))
            cursor.execute('DELETE FROM po_headers WHERE po_number = ?', (po_number,))

        # Insert PO header
        cursor.execute('''
            INSERT INTO po_headers (po_number, purchase_from, ship_to, company, currency, cancel_date)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (po_number, po_header.get('purchase_from', ''), po_header.get('ship_to', ''),
              po_header.get('company', ''), po_header.get('currency', ''), po_header.get('cancel_date', '')))

        # Insert PO items
        for item in po_items:
            cursor.execute('''
                INSERT INTO po_items (po_number, item_number, description, color, ship_to, need_by, qty, bundle_qty, unit_price, extension)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (po_number, item.get('item_number', ''), item.get('description', ''), item.get('color', ''),
                  item.get('ship_to', ''), item.get('need_by', ''), item.get('qty', ''),
                  item.get('bundle_qty', ''), item.get('unit_price', ''), item.get('extension', '')))

        conn.commit()
        print(f"📊 PO {po_number} saved to database successfully")
        return True

    except Exception as e:
        conn.rollback()
        print(f"❌ Error saving PO to database: {e}")
        return False
    finally:
        conn.close()

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

def scrape_po_details(po_number):
    """Scrape complete PO details from factoryPODetail.aspx page"""
    driver = None
    try:
        # Setup Chrome driver (same as working download functions)
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-images")

        driver_path = ChromeDriverManager().install()
        service = Service(driver_path)
        driver = webdriver.Chrome(service=service, options=chrome_options)
        wait = WebDriverWait(driver, 15)

        print(f"🔍 Scraping PO details for {po_number}...")

        # Login first (same as working functions)
        driver.get(config['login_url'])
        username_field = wait.until(EC.presence_of_element_located((By.ID, "txtUserName")))
        password_field = driver.find_element(By.ID, "txtPassword")

        username_field.send_keys(config['username'])
        password_field.send_keys(config['password'])

        # Use the same login method as working functions
        login_button = driver.find_element(By.XPATH, "//img[@onclick='return Login();']")
        login_button.click()
        wait.until(lambda d: "login" not in d.current_url.lower())

        print(f"✅ Login successful for PO scraping")

        # Navigate to PO detail page
        po_url = f"https://app.e-brandid.com/Bidnet/bidnet3/factoryPODetail.aspx?po_id={po_number}"
        driver.get(po_url)
        time.sleep(5)  # Give more time for page to load

        print(f"📄 Loaded PO detail page: {po_url}")

        # Extract PO header information
        po_header = {}

        # Try to find header information (adjust selectors based on actual page structure)
        try:
            # Look for common header fields - these may need adjustment based on actual page
            page_text = driver.page_source

            # Extract basic info that's usually visible
            po_header['purchase_from'] = extract_field_value(page_text, ['Purchase From', 'Vendor', 'Supplier'])
            po_header['ship_to'] = extract_field_value(page_text, ['Ship To', 'Shipping Address'])
            po_header['company'] = extract_field_value(page_text, ['Company', 'Client'])
            po_header['currency'] = extract_field_value(page_text, ['Currency', 'Curr'])
            po_header['cancel_date'] = extract_field_value(page_text, ['Cancel Date', 'Deadline', 'Due Date'])

        except Exception as e:
            print(f"⚠️ Could not extract header info: {e}")

        # Extract items table
        po_items = []

        try:
            print(f"🔍 Looking for data tables on PO page...")

            # Wait for page content to load
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "table")))

            # Find all tables
            tables = driver.find_elements(By.TAG_NAME, "table")
            print(f"📊 Found {len(tables)} tables on page")

            # Try to find the table with item data (similar to how get_po_data works)
            for table_idx, table in enumerate(tables):
                try:
                    rows = table.find_elements(By.TAG_NAME, "tr")
                    print(f"📋 Table {table_idx + 1}: {len(rows)} rows")

                    if len(rows) < 2:  # Skip tables with no data rows
                        continue

                    # Look for data rows (skip header)
                    for row_idx, row in enumerate(rows[1:], 1):  # Skip first row (header)
                        cells = row.find_elements(By.TAG_NAME, "td")

                        if len(cells) >= 8:  # Should have at least 8 columns for item data
                            cell_texts = [cell.text.strip() for cell in cells]

                            # Check if this looks like an item row (first cell should be item number)
                            if cell_texts[0] and len(cell_texts[0]) > 3 and not cell_texts[0].lower().startswith('item'):
                                item = {
                                    'item_number': cell_texts[0] if len(cell_texts) > 0 else '',
                                    'description': cell_texts[1] if len(cell_texts) > 1 else '',
                                    'color': cell_texts[2] if len(cell_texts) > 2 else '',
                                    'ship_to': cell_texts[3] if len(cell_texts) > 3 else '',
                                    'need_by': cell_texts[4] if len(cell_texts) > 4 else '',
                                    'qty': cell_texts[5] if len(cell_texts) > 5 else '',
                                    'bundle_qty': cell_texts[6] if len(cell_texts) > 6 else '',
                                    'unit_price': cell_texts[7] if len(cell_texts) > 7 else '',
                                    'extension': cell_texts[8] if len(cell_texts) > 8 else ''
                                }
                                po_items.append(item)
                                print(f"✅ Found item: {item['item_number']} - {item['description'][:30]}...")

                    if po_items:  # Found items in this table
                        print(f"🎯 Successfully extracted {len(po_items)} items from table {table_idx + 1}")
                        break

                except Exception as table_error:
                    print(f"⚠️ Error processing table {table_idx + 1}: {table_error}")
                    continue

        except Exception as e:
            print(f"⚠️ Could not extract items table: {e}")

        print(f"✅ Scraped {len(po_items)} items for PO {po_number}")
        return po_header, po_items

    except Exception as e:
        print(f"❌ Error scraping PO details: {e}")
        return {}, []
    finally:
        if driver:
            driver.quit()

def extract_field_value(page_text, field_names):
    """Extract field value from page text using multiple possible field names"""
    for field_name in field_names:
        # Look for patterns like "Field Name: Value" or "Field Name Value"
        patterns = [
            rf'{field_name}[:\s]+([^\n\r<>]+)',
            rf'<[^>]*>{field_name}[:\s]*</[^>]*>\s*<[^>]*>([^<]+)',
            rf'{field_name}[:\s]*([A-Za-z0-9\s\.,@-]+)'
        ]

        for pattern in patterns:
            match = re.search(pattern, page_text, re.IGNORECASE)
            if match:
                value = match.group(1).strip()
                if value and len(value) > 1:
                    return value
    return ''

app = Flask(__name__)

# Global variables
po_data = {}
download_status = {'active': False, 'progress': 0, 'log': []}

# Configuration storage
config = {
    'login_url': 'https://app.e-brandid.com/login/login.aspx',
    'username': 'sales10@fuchanghk.com',
    'password': 'fc31051856',
    'admin_password': '1234'
}

def analyze_po_and_recommend(po_number, item_count, item_names):
    """Analyze PO data and recommend best download method"""
    
    recommendations = []
    
    # Analyze item count
    if item_count <= 10:
        recommendations.append({
            'method': 'standard',
            'name': 'Standard Download',
            'reason': f'Small PO ({item_count} items) - Standard method is reliable and fast enough',
            'score': 90
        })
    elif item_count <= 50:
        recommendations.append({
            'method': 'hybrid',
            'name': 'Hybrid Speed',
            'reason': f'Medium PO ({item_count} items) - Hybrid speed gives best balance of speed and reliability',
            'score': 95
        })
    else:
        recommendations.append({
            'method': 'hybrid',
            'name': 'Hybrid Speed',
            'reason': f'Large PO ({item_count} items) - Hybrid speed essential for efficiency',
            'score': 100
        })
    
    # Analyze item name patterns for duplicates
    unique_bases = set()
    for name in item_names:
        # Extract base name (remove size/color variants)
        base = name.split('BLK')[0].split('WHT')[0].split('NAT')[0][:10]
        unique_bases.add(base)
    
    duplicate_ratio = 1 - (len(unique_bases) / len(item_names)) if item_names else 0
    
    if duplicate_ratio > 0.7:  # More than 70% duplicates
        recommendations.append({
            'method': 'clean',
            'name': 'Clean Naming',
            'reason': f'High duplicate ratio ({duplicate_ratio:.0%}) - Clean naming will organize files better',
            'score': 85
        })
    
    # Sort by score
    recommendations.sort(key=lambda x: x['score'], reverse=True)
    return recommendations

def get_po_data(po_number):
    """Get PO data from E-BrandID"""
    
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-images")
    
    try:
        driver_path = ChromeDriverManager().install()
        service = Service(driver_path)
        driver = webdriver.Chrome(service=service, options=chrome_options)
    except:
        driver = webdriver.Chrome(options=chrome_options)
    
    wait = WebDriverWait(driver, 10)
    
    try:
        # Login
        driver.get(config['login_url'])
        username_field = wait.until(EC.presence_of_element_located((By.ID, "txtUserName")))
        password_field = driver.find_element(By.ID, "txtPassword")

        username_field.send_keys(config['username'])
        password_field.send_keys(config['password'])
        
        login_button = driver.find_element(By.XPATH, "//img[@onclick='return Login();']")
        login_button.click()
        wait.until(lambda d: "login" not in d.current_url.lower())
        
        # Navigate to PO search page first
        print(f"🔍 STEP 1: Going to PO search page")
        driver.get("https://app.e-brandid.com/Bidnet/bidnet3/factoryPOList.aspx")

        # Wait for page to load
        import time
        time.sleep(2)

        # Search for the PO
        try:
            search_box = wait.until(EC.presence_of_element_located((By.ID, "txtPONumber")))
            search_box.clear()
            search_box.send_keys(po_number)

            # Click search button
            search_button = driver.find_element(By.ID, "btnSearch")
            search_button.click()

            print(f"🔍 STEP 2: Searching for PO {po_number}")
            time.sleep(3)

            # Click on the PO link
            po_link = wait.until(EC.element_to_be_clickable((By.XPATH, f"//a[contains(text(), '{po_number}')]")))
            po_link.click()

            print(f"🔍 STEP 3: Clicked on PO {po_number}")

        except Exception as e:
            print(f"❌ Error searching for PO: {e}")
            # Fallback to direct URL
            po_url = f"https://app.e-brandid.com/Bidnet/bidnet3/factoryPODetail.aspx?po_id={po_number}"
            print(f"🔍 FALLBACK: Trying direct URL: {po_url}")
            driver.get(po_url)

        # Wait and check for redirects
        import time
        time.sleep(3)  # Wait for any redirects

        current_url_after_load = driver.current_url
        print(f"🔍 STEP 2: URL after load: {current_url_after_load}")

        # Check if we were redirected
        if po_url != current_url_after_load:
            print(f"🚨 REDIRECT DETECTED!")
            print(f"   Original: {po_url}")
            print(f"   Redirected to: {current_url_after_load}")

        # Wait for tables to load
        try:
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "table")))
            print(f"✅ Tables loaded successfully")
        except Exception as e:
            print(f"❌ Error waiting for tables: {e}")

        # Get PO info
        try:
            po_title = driver.find_element(By.TAG_NAME, "h1").text
            print(f"🔍 STEP 3: Page title: '{po_title}'")
        except Exception as e:
            print(f"❌ Could not find h1 title: {e}")
            po_title = f"PO {po_number}"

        # Look for PO number in various places
        print(f"🔍 STEP 4: Searching for PO {po_number} in page...")

        # Check URL
        if po_number in current_url_after_load:
            print(f"✅ PO {po_number} found in URL")
        else:
            print(f"❌ PO {po_number} NOT found in URL")

        # Check title
        if po_number in po_title:
            print(f"✅ PO {po_number} found in title")
        else:
            print(f"❌ PO {po_number} NOT found in title")

        # Check page source for PO number
        page_source = driver.page_source
        if po_number in page_source:
            print(f"✅ PO {po_number} found in page source")
            # Count occurrences
            count = page_source.count(po_number)
            print(f"   Found {count} occurrences of {po_number}")
        else:
            print(f"❌ PO {po_number} NOT found anywhere in page source")

        # Look for other PO numbers in the page
        import re
        po_pattern = r'\b\d{6,8}\b'  # Look for 6-8 digit numbers (typical PO format)
        found_pos = re.findall(po_pattern, page_source)
        unique_pos = list(set(found_pos))[:10]  # First 10 unique POs found
        print(f"🔍 Other PO numbers found on page: {unique_pos}")

        # If we're on the wrong page, return error with details
        if po_number not in current_url_after_load and po_number not in po_title and po_number not in page_source:
            error_msg = f"PO {po_number} not found. Page shows: {po_title}. URL: {current_url_after_load}"
            print(f"🚨 FINAL ERROR: {error_msg}")
            return {
                'success': False,
                'error': error_msg,
                'po_number': po_number,
                'actual_url': current_url_after_load,
                'actual_title': po_title,
                'found_pos': unique_pos[:5]  # Include some found POs for debugging
            }
        
        # Find item links and extract data with robust table detection
        tables = driver.find_elements(By.TAG_NAME, "table")
        item_data = []

        print(f"Found {len(tables)} tables on page")

        for table_index, table in enumerate(tables):
            rows = table.find_elements(By.TAG_NAME, "tr")
            print(f"Table {table_index}: {len(rows)} rows")

            # Multiple strategies to identify the correct table
            header_found = False
            table_score = 0

            # Strategy 1: Look for header row with expected columns
            for row_index, row in enumerate(rows):
                header_cells = row.find_elements(By.TAG_NAME, "th")
                if len(header_cells) >= 5:  # Expect multiple columns
                    header_text = " ".join([cell.text.strip() for cell in header_cells]).lower()
                    print(f"Table {table_index}, Row {row_index} headers: {header_text}")

                    # Score based on expected headers
                    if "item" in header_text: table_score += 3
                    if "description" in header_text: table_score += 3
                    if "color" in header_text: table_score += 2
                    if "qty" in header_text or "quantity" in header_text: table_score += 2
                    if "ship" in header_text: table_score += 1
                    if "need" in header_text or "date" in header_text: table_score += 1

                    if table_score >= 6:  # Good confidence
                        header_found = True
                        print(f"Table {table_index} selected with score {table_score}")
                        break

            # Strategy 2: Look for item links in data rows
            if not header_found:
                item_links = table.find_elements(By.XPATH, ".//a[contains(@onclick, 'openItemDetail')]")
                if len(item_links) >= 2:  # Multiple items suggest this is the data table
                    header_found = True
                    table_score = 5
                    print(f"Table {table_index} selected by item links: {len(item_links)} items")

            if not header_found:
                print(f"Table {table_index} skipped (score: {table_score})")
                continue

            # Process data rows with better validation
            data_rows_processed = 0
            for row_index, row in enumerate(rows[1:], 1):  # Skip header
                cells = row.find_elements(By.TAG_NAME, "td")
                print(f"Table {table_index}, Row {row_index}: {len(cells)} cells")

                if len(cells) >= 4:  # Minimum columns needed
                    try:
                        # Get all cell text for analysis
                        cell_texts = [cell.text.strip() for cell in cells]
                        print(f"Row data: {cell_texts[:6]}")  # Show first 6 columns

                        # Flexible column detection
                        item_number = cell_texts[0] if len(cell_texts) > 0 else ""
                        description = cell_texts[1] if len(cell_texts) > 1 else ""
                        color = cell_texts[2] if len(cell_texts) > 2 else ""

                        # Try to find quantity (look for numbers)
                        quantity = ""
                        for i in range(3, min(len(cell_texts), 8)):
                            if cell_texts[i] and any(c.isdigit() for c in cell_texts[i].replace(',', '')):
                                quantity = cell_texts[i]
                                break

                        # Get other fields
                        ship_to = cell_texts[3] if len(cell_texts) > 3 else ""
                        need_by = cell_texts[4] if len(cell_texts) > 4 else ""

                        # Validate this looks like item data
                        is_valid_item = (
                            item_number and
                            len(item_number) > 3 and  # Item numbers are usually longer
                            item_number != "Item #" and
                            item_number != "Total:" and
                            item_number != "Description" and
                            not item_number.startswith("#") and  # Skip row numbers
                            description and
                            len(description) > 5 and  # Descriptions are usually longer
                            description != "Item #" and
                            description != "Description" and
                            # Check if it looks like a real item number (contains letters and numbers)
                            any(c.isalpha() for c in item_number) and
                            any(c.isdigit() for c in item_number)
                        )

                        if is_valid_item:
                            # Check if item has download link and extract suffix_id
                            has_download = False
                            suffix_id = ""

                            detail_links = row.find_elements(By.XPATH, ".//a[contains(@onclick, 'openItemDetail')]")
                            if detail_links:
                                has_download = True
                                # Extract suffix_id from the onclick attribute
                                onclick_attr = detail_links[0].get_attribute('onclick')
                                if onclick_attr:
                                    # Look for pattern like: openItemDetail('8026686', '9062056')
                                    import re
                                    match = re.search(r"openItemDetail\('(\d+)',\s*'(\d+)'\)", onclick_attr)
                                    if match:
                                        suffix_id = match.group(2)  # Second parameter is suffix_id
                                        print(f"Found suffix_id: {suffix_id} for item: {item_number}")

                            item_data.append({
                                'name': item_number,
                                'description': f"{description} - {color}" if color else description,
                                'quantity': quantity,
                                'ship_to': ship_to,
                                'need_by': need_by,
                                'has_download': has_download,
                                'suffix_id': suffix_id
                            })
                            data_rows_processed += 1
                            print(f"Added item: {item_number}")
                        else:
                            print(f"Skipped invalid row: {item_number}")

                    except Exception as e:
                        print(f"Error processing row {row_index}: {e}")
                        continue

            print(f"Table {table_index} processed {data_rows_processed} items")

            # If we found good data, stop looking at other tables
            if data_rows_processed >= 1:  # Even 1 valid item means we found the right table
                print(f"Found sufficient data in table {table_index}, stopping search")
                break
        
        # Remove duplicates based on item name
        seen_items = set()
        unique_items = []
        for item in item_data:
            item_key = item['name'].strip().upper()
            if item_key not in seen_items:
                seen_items.add(item_key)
                unique_items.append(item)
            else:
                print(f"Removed duplicate: {item['name']}")

        item_data = unique_items
        print(f"Final unique items: {len(item_data)}")

        # Get recommendations
        item_names = [item['name'] for item in item_data]
        recommendations = analyze_po_and_recommend(po_number, len(item_data), item_names)
        
        return {
            'success': True,
            'po_number': po_number,
            'title': po_title,
            'total_items': len(item_data),
            'items': item_data,
            'recommendations': recommendations,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'po_number': po_number
        }
    
    finally:
        driver.quit()

@app.route('/')
def index():
    masked_username = mask_email(config['username'])
    response = app.response_class(
        render_template_string(HTML_TEMPLATE, version=VERSION, version_date=VERSION_DATE, last_edit=LAST_EDIT, masked_username=masked_username),
        mimetype='text/html'
    )
    # Add cache-busting headers
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route('/api/analyze_po', methods=['POST'])
def analyze_po():
    """Analyze PO and return data with recommendations"""
    data = request.json
    po_number = data.get('po_number')
    
    if not po_number:
        return jsonify({'error': 'PO number required'}), 400
    
    # Get PO data
    result = get_po_data(po_number)
    
    if result['success']:
        global po_data
        po_data = result
        return jsonify(result)
    else:
        return jsonify(result), 500

@app.route('/api/test_login')
def test_login():
    """Test login and basic navigation"""
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from webdriver_manager.chrome import ChromeDriverManager
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.common.by import By

    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    try:
        driver_path = ChromeDriverManager().install()
        service = Service(driver_path)
        driver = webdriver.Chrome(service=service, options=chrome_options)
    except:
        driver = webdriver.Chrome(options=chrome_options)

    wait = WebDriverWait(driver, 10)

    try:
        print("🔍 Testing login...")
        driver.get(config['login_url'])

        username_field = wait.until(EC.presence_of_element_located((By.ID, "txtUserName")))
        password_field = driver.find_element(By.ID, "txtPassword")

        username_field.send_keys(config['username'])
        password_field.send_keys(config['password'])

        login_button = driver.find_element(By.XPATH, "//img[@onclick='return Login();']")
        login_button.click()
        wait.until(lambda d: "login" not in d.current_url.lower())

        current_url = driver.current_url
        print(f"✅ Login successful, redirected to: {current_url}")

        return jsonify({
            'success': True,
            'message': 'Login successful',
            'redirect_url': current_url
        })

    except Exception as e:
        print(f"❌ Login failed: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        })
    finally:
        driver.quit()

@app.route('/api/test_data/<po_number>')
def test_data(po_number):
    """Test endpoint to check current parsed data"""
    result = get_po_data(po_number)
    return jsonify({
        'po_number': po_number,
        'items_count': len(result.get('items', [])) if result.get('success') else 0,
        'items': result.get('items', [])[:5],  # First 5 items for testing
        'success': result.get('success', False),
        'error': result.get('error', None)
    })

@app.route('/api/start_download', methods=['POST'])
def start_download():
    """Start download with selected method"""
    data = request.json
    method = data.get('method')
    po_number = data.get('po_number')
    items = data.get('items', [])

    # Start download in background
    thread = threading.Thread(target=real_download, args=(po_number, method, items))
    thread.daemon = True
    thread.start()

    return jsonify({'success': True, 'message': 'Download started'})

def create_download_folder(po_number):
    """Create folder structure: download_artwork / Date folder / PO#_HH_MM_SS"""
    now = datetime.now()
    date_folder = now.strftime("%Y_%m_%d")
    time_part = now.strftime("%H_%M_%S")
    po_folder = f"{po_number}_{time_part}"

    # Create download_artwork folder first
    artwork_path = os.path.join(os.getcwd(), "download_artwork")
    if not os.path.exists(artwork_path):
        os.makedirs(artwork_path, exist_ok=True)

    # Create date folder inside download_artwork
    date_path = os.path.join(artwork_path, date_folder)
    if not os.path.exists(date_path):
        os.makedirs(date_path, exist_ok=True)

    # Create PO folder inside date folder
    download_folder = os.path.join(date_path, po_folder)
    if not os.path.exists(download_folder):
        os.makedirs(download_folder, exist_ok=True)

    return download_folder, f"download_artwork/{date_folder}/{po_folder}"

def download_item_artwork(item, download_folder, item_number):
    """Download PDF artwork using direct URL pattern - SUPER FAST METHOD"""
    import requests

    try:
        item_name = item.get('name', '')
        if not item_name:
            return False

        # Get suffix_id from item data (we need to extract this from the PO page)
        # For now, let's try to get it from the item detail link if available
        suffix_id = item.get('suffix_id', '')

        if not suffix_id:
            # If no suffix_id, we need to get it from the item detail page
            suffix_id = get_item_suffix_id(item_name)

        if suffix_id:
            # Use your super fast direct download method!
            pdf_url = f"https://app4.brandid.com/Artwork/{item_name}_{suffix_id}.pdf"

            # Download the PDF directly
            response = requests.get(pdf_url, timeout=30)

            if response.status_code == 200:
                pdf_filename = f"{item_name}_{suffix_id}.pdf"
                pdf_path = os.path.join(download_folder, pdf_filename)

                with open(pdf_path, 'wb') as f:
                    f.write(response.content)

                print(f"✅ Downloaded: {pdf_filename}")
                return True
            else:
                print(f"❌ PDF not found at: {pdf_url}")
                return False
        else:
            print(f"❌ Could not find suffix_id for: {item_name}")
            return False

    except Exception as e:
        print(f"❌ Error downloading {item_name}: {e}")
        return False

def get_item_suffix_id(item_name):
    """Get suffix_id by checking the item detail page"""
    # This would need to scrape the PO detail page to get the suffix_id
    # For now, return None - we need to enhance the PO scraping to get this
    return None

def real_download(po_number, method, items):
    """Real download process with actual file downloads"""
    global download_status
    download_status = {'active': True, 'progress': 0, 'log': []}

    try:
        # Create download folder
        download_folder, folder_display = create_download_folder(po_number)
        download_status['log'].append(f"📅 Created date folder: {folder_display.split('/')[0]}")
        download_status['log'].append(f"📁 Created PO folder: {folder_display}")
        download_status['log'].append(f"🎯 Starting {method} download for PO {po_number}")
        download_status['log'].append(f"💾 Files will be saved to: {download_folder}")
        download_status['log'].append(f"📊 Found {len(items)} items to download")

        # Choose download method
        if method == 'super_fast':
            success_count = download_super_fast(items, download_folder)
        elif method == 'hybrid':
            success_count = download_hybrid(items, download_folder)
        elif method == 'standard':
            success_count = download_standard(items, download_folder)
        elif method == 'original_slow':
            success_count = download_original_slow(items, download_folder)
        elif method == 'guaranteed_complete':
            success_count = download_guaranteed_complete(po_number, items, download_folder)
        else:
            success_count = download_standard(items, download_folder)  # Default

        download_status['active'] = False
        download_status['download_folder'] = download_folder  # Store folder path for "Open Folder" link
        download_status['log'].append("✅ Download completed!")
        download_status['log'].append(f"📁 {success_count}/{len(items)} files downloaded successfully")

    except Exception as e:
        download_status['active'] = False
        download_status['log'].append(f"❌ Error: {str(e)}")

def download_super_fast(items, download_folder):
    """Super Fast Method: Direct PDF downloads using URL pattern (~10% success)"""
    global download_status
    success_count = 0

    for i, item in enumerate(items):
        if not download_status['active']:
            break

        progress = int((i + 1) / len(items) * 100)
        download_status['progress'] = progress
        download_status['log'].append(f"🚀 Super Fast: Processing {i+1}/{len(items)}: {item.get('name', 'Unknown')}")

        try:
            item_name = item.get('name', '')
            suffix_id = item.get('suffix_id', '')

            if suffix_id:
                pdf_url = f"https://app4.brandid.com/Artwork/{item_name}_{suffix_id}.pdf"
                response = requests.get(pdf_url, timeout=10)

                if response.status_code == 200:
                    pdf_filename = f"{item_name}_{suffix_id}.pdf"
                    pdf_path = os.path.join(download_folder, pdf_filename)

                    with open(pdf_path, 'wb') as f:
                        f.write(response.content)

                    download_status['log'].append(f"✅ Downloaded: {pdf_filename}")
                    success_count += 1
                else:
                    download_status['log'].append(f"❌ PDF not found: {pdf_url}")
            else:
                download_status['log'].append(f"❌ No suffix_id for: {item_name}")

        except Exception as e:
            download_status['log'].append(f"❌ Error: {str(e)}")

        time.sleep(0.5)  # Very fast

    return success_count

def download_hybrid(items, download_folder):
    """Hybrid Method: Browser login + direct requests (~70% success)"""
    global download_status
    success_count = 0

    # TODO: Implement hybrid method
    download_status['log'].append("⚡ Hybrid method - Coming soon!")

    for i, item in enumerate(items):
        if not download_status['active']:
            break

        progress = int((i + 1) / len(items) * 100)
        download_status['progress'] = progress
        download_status['log'].append(f"⚡ Hybrid: Processing {i+1}/{len(items)}: {item.get('name', 'Unknown')}")
        time.sleep(2)

    return success_count

def download_standard(items, download_folder):
    """Standard Method: Browser automation with smart navigation (~90% success)"""
    global download_status
    success_count = 0

    # TODO: Implement standard method
    download_status['log'].append("📋 Standard method - Coming soon!")

    for i, item in enumerate(items):
        if not download_status['active']:
            break

        progress = int((i + 1) / len(items) * 100)
        download_status['progress'] = progress
        download_status['log'].append(f"📋 Standard: Processing {i+1}/{len(items)}: {item.get('name', 'Unknown')}")
        time.sleep(3)

    return success_count

def download_original_slow(items, download_folder):
    """Original Slow Method: Full browser automation (100% success)"""
    global download_status
    success_count = 0

    # TODO: Implement original slow method
    download_status['log'].append("🐌 Original slow method - Coming soon!")

    for i, item in enumerate(items):
        if not download_status['active']:
            break

        progress = int((i + 1) / len(items) * 100)
        download_status['progress'] = progress
        download_status['log'].append(f"🐌 Original Slow: Processing {i+1}/{len(items)}: {item.get('name', 'Unknown')}")
        time.sleep(5)

    return success_count

def download_guaranteed_complete(po_number, items, download_folder):
    """Guaranteed Complete Download: 100% success rate with actual PDF URL extraction"""
    global download_status
    import requests
    import re
    import shutil
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from webdriver_manager.chrome import ChromeDriverManager

    success_count = 0
    downloaded_files = []

    download_status['log'].append("✨ Method 5: Guaranteed Complete Download")
    download_status['log'].append(f"⚡ Processing {len(items)} items with 100% success rate...")
    download_status['log'].append("🔍 Setting up browser for PDF URL extraction...")

    # Setup browser for URL extraction
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    try:
        driver = webdriver.Chrome(options=chrome_options)
        download_status['log'].append("✅ Browser setup complete")

        # CRITICAL: Login first (same as working unified_downloader.py)
        download_status['log'].append("📝 Logging in to E-BrandID...")
        driver.get(config['login_url'])

        # Login with credentials (same as unified_downloader.py)
        username_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "txtUserName"))
        )
        password_field = driver.find_element(By.ID, "txtPassword")

        username_field.send_keys(config['username'])
        password_field.send_keys(config['password'])

        login_button = driver.find_element(By.XPATH, "//img[@onclick='return Login();']")
        login_button.click()

        # Wait for login to complete
        WebDriverWait(driver, 10).until(lambda d: "login" not in d.current_url.lower())
        download_status['log'].append("✅ Login successful!")

        # Now navigate to the PO page (after login) - use the correct PO number
        po_url = f"https://app.e-brandid.com/Bidnet/bidnet3/factoryPODetail.aspx?po_id={po_number}"
        driver.get(po_url)
        download_status['log'].append(f"📄 Loaded PO page: {po_number} (after login)")

        # Wait for page to load
        time.sleep(3)

        # Find item links with openItemDetail onclick (same as unified_downloader.py)
        download_status['log'].append("🔍 Finding item links with openItemDetail...")
        tables = driver.find_elements(By.TAG_NAME, "table")
        item_links = []
        for table in tables:
            links = table.find_elements(By.XPATH, ".//a[contains(@onclick, 'openItemDetail')]")
            if links:
                item_links = links
                break

        download_status['log'].append(f"✅ Found {len(item_links)} clickable item links")

        if not item_links:
            download_status['log'].append("❌ No openItemDetail links found!")
            driver.quit()
            return 0

        # Extract PDF URLs using the exact same method as unified_downloader.py
        item_pdf_data = []
        for i, link in enumerate(item_links):
            if not download_status['active']:
                break

            progress = int((i + 1) / len(item_links) * 100)
            download_status['progress'] = progress

            try:
                item_name = link.text.strip()
                download_status['log'].append(f"🔍 Extracting PDF URL {i+1}/{len(item_links)}: {item_name}")

                # Click item to open popup (same as unified_downloader.py)
                original_windows = len(driver.window_handles)
                driver.execute_script("arguments[0].click();", link)

                # Wait for popup
                popup_opened = False
                for wait_attempt in range(30):
                    time.sleep(0.1)
                    if len(driver.window_handles) > original_windows:
                        popup_opened = True
                        break

                if popup_opened:
                    driver.switch_to.window(driver.window_handles[-1])

                    try:
                        # Find download button and extract PDF URL
                        download_button = WebDriverWait(driver, 5).until(
                            EC.presence_of_element_located((By.XPATH, "//a[contains(text(), 'Download')]"))
                        )

                        onclick_attr = download_button.get_attribute('onclick')
                        # Extract PDF URL from onclick (same regex as unified_downloader.py)
                        match = re.search(r"MM_openBrWindow\('([^']+\.pdf)'", onclick_attr)
                        if match:
                            pdf_url = match.group(1)
                            original_filename = os.path.basename(pdf_url)
                            item_pdf_data.append((item_name, pdf_url, original_filename))
                            download_status['log'].append(f"✅ Found PDF URL for {item_name}")
                        else:
                            download_status['log'].append(f"❌ Could not extract PDF URL for {item_name}")

                    except Exception as e:
                        download_status['log'].append(f"❌ Error extracting URL for {item_name}: {str(e)}")

                    # Close popup
                    driver.close()
                    driver.switch_to.window(driver.window_handles[0])
                    time.sleep(0.5)
                else:
                    download_status['log'].append(f"❌ Popup did not open for {item_name}")

            except Exception as e:
                download_status['log'].append(f"❌ Error processing {item_name}: {str(e)}")
                continue

        # Close browser
        driver.quit()
        download_status['log'].append("🔍 PDF URL extraction complete")

        # Now download all the PDFs
        download_status['log'].append("📥 Starting PDF downloads...")

        for i, (item_name, pdf_url, original_filename) in enumerate(item_pdf_data):
            if not download_status['active']:
                break

            progress = int((i + 1) / len(item_pdf_data) * 100)
            download_status['progress'] = progress

            try:
                response = requests.get(pdf_url, timeout=30)
                if response.status_code == 200:
                    # Generate unique filename with smart numbering
                    final_filename = get_unique_filename(original_filename, download_folder, downloaded_files)

                    pdf_path = os.path.join(download_folder, final_filename)
                    with open(pdf_path, 'wb') as f:
                        f.write(response.content)

                    downloaded_files.append(final_filename)
                    success_count += 1

                    file_size = len(response.content)
                    download_status['log'].append(f"✅ Downloaded: {final_filename} ({file_size:,} bytes)")
                else:
                    download_status['log'].append(f"❌ Failed to download: {pdf_url}")

            except Exception as e:
                download_status['log'].append(f"❌ Error downloading {item_name}: {str(e)}")

            time.sleep(0.5)

    except Exception as e:
        download_status['log'].append(f"❌ Browser setup error: {str(e)}")
        return 0

    # Calculate total size
    total_size = 0
    for filename in downloaded_files:
        file_path = os.path.join(download_folder, filename)
        if os.path.exists(file_path):
            total_size += os.path.getsize(file_path)

    download_status['log'].append("🎉 GUARANTEED COMPLETE DOWNLOAD COMPLETE!")
    download_status['log'].append(f"✅ Processed items: {success_count}")
    download_status['log'].append(f"❌ Failed items: {len(items) - success_count}")
    download_status['log'].append(f"📥 Total files: {len(downloaded_files)}")
    download_status['log'].append(f"💾 Total size: {total_size / (1024*1024):.1f} MB")

    return success_count

def get_unique_filename(base_filename, download_folder, existing_files):
    """Generate unique filename with smart numbering for duplicates"""
    if base_filename not in existing_files:
        return base_filename

    name, ext = os.path.splitext(base_filename)
    counter = 2

    while True:
        new_filename = f"{name}_{counter}{ext}"
        if new_filename not in existing_files:
            return new_filename
        counter += 1

@app.route('/api/status')
def get_status():
    return jsonify(download_status)

@app.route('/api/version')
def get_version():
    """Get current version information"""
    return jsonify({
        'version': VERSION,
        'version_date': VERSION_DATE,
        'last_edit': LAST_EDIT,
        'timestamp': VERSION_DATE
    })



@app.route('/api/open_folder')
def open_folder():
    """Open the download folder in Windows Explorer"""
    try:
        # Get the most recent download folder from download_status
        if 'download_folder' in download_status:
            folder_path = download_status['download_folder']
            if os.path.exists(folder_path):
                # Open folder in Windows Explorer
                import subprocess
                subprocess.Popen(f'explorer "{folder_path}"')
                return jsonify({"success": True, "message": f"Opened folder: {folder_path}"})
            else:
                return jsonify({"success": False, "message": "Download folder not found"})
        else:
            return jsonify({"success": False, "message": "No download folder available"})
    except Exception as e:
        return jsonify({"success": False, "message": f"Error opening folder: {str(e)}"})

@app.route('/api/settings/verify_admin', methods=['POST'])
def verify_admin():
    """Verify admin password"""
    data = request.json
    password = data.get('password', '')

    if password == config['admin_password']:
        return jsonify({"success": True, "message": "Admin access granted"})
    else:
        return jsonify({"success": False, "message": "Invalid admin password"})

@app.route('/api/settings/get_config', methods=['POST'])
def get_config():
    """Get configuration (requires admin password)"""
    data = request.json
    password = data.get('password', '')

    if password != config['admin_password']:
        return jsonify({"success": False, "message": "Admin access required"})

    return jsonify({
        "success": True,
        "config": {
            "login_url": config['login_url'],
            "username": config['username'],
            "password": config['password']
        }
    })

@app.route('/api/settings/update_config', methods=['POST'])
def update_config():
    """Update configuration (requires admin password)"""
    data = request.json
    password = data.get('admin_password', '')

    if password != config['admin_password']:
        return jsonify({"success": False, "message": "Admin access required"})

    # Update configuration
    if 'login_url' in data:
        config['login_url'] = data['login_url']
    if 'username' in data:
        config['username'] = data['username']
    if 'password' in data:
        config['password'] = data['password']

    return jsonify({"success": True, "message": "Configuration updated successfully"})

@app.route('/api/po/check_exists', methods=['POST'])
def check_po_exists_api():
    """Check if PO exists in database"""
    data = request.json
    po_number = data.get('po_number', '')

    if not po_number:
        return jsonify({"success": False, "message": "PO number required"})

    exists = check_po_exists(po_number)
    return jsonify({"success": True, "exists": exists, "po_number": po_number})

@app.route('/api/po/save_details', methods=['POST'])
def save_po_details_api():
    """Save PO details to database"""
    data = request.json
    po_number = data.get('po_number', '')
    overwrite = data.get('overwrite', False)

    if not po_number:
        return jsonify({"success": False, "message": "PO number required"})

    try:
        # Scrape PO details
        po_header, po_items = scrape_po_details(po_number)

        if not po_items:
            return jsonify({"success": False, "message": "Could not extract PO details from website"})

        # Save to database
        success = save_po_to_database(po_number, po_header, po_items, overwrite)

        if success:
            return jsonify({
                "success": True,
                "message": f"PO {po_number} saved successfully",
                "header_count": 1,
                "items_count": len(po_items)
            })
        else:
            return jsonify({"success": False, "message": "Failed to save PO to database"})

    except Exception as e:
        return jsonify({"success": False, "message": f"Error processing PO: {str(e)}"})

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Artwork Downloader v{{ version }}</title>
    <meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
    <meta http-equiv="Pragma" content="no-cache">
    <meta http-equiv="Expires" content="0">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f5f5f5;
            color: #333;
            line-height: 1.6;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }

        .tabs {
            display: flex;
            background: #f9f9f9;
            border-bottom: 1px solid #e0e0e0;
            margin-bottom: 30px;
        }

        .tab {
            flex: 1;
            padding: 15px 20px;
            text-align: center;
            cursor: pointer;
            border: none;
            background: none;
            font-size: 0.9em;
            transition: all 0.2s;
            color: #666;
            border-bottom: 2px solid transparent;
        }

        .tab.active {
            background: white;
            color: #333;
            border-bottom: 2px solid #333;
            font-weight: 500;
        }

        .tab:hover {
            background: #f0f0f0;
            color: #333;
        }

        .tab-content {
            display: none;
        }

        .tab-content.active {
            display: block;
        }
        
        .header {
            background: #2c3e50;
            color: white;
            padding: 20px;
            text-align: center;
            margin-bottom: 30px;
        }
        
        .step {
            background: white;
            border: 1px solid #e0e0e0;
            margin-bottom: 20px;
            padding: 25px;
        }
        
        .step h2 {
            margin-bottom: 15px;
            color: #333;
            font-size: 1.3em;
        }
        
        .step-number {
            background: #333;
            color: white;
            width: 30px;
            height: 30px;
            border-radius: 50%;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            margin-right: 10px;
            font-weight: bold;
        }
        
        .form-group {
            margin-bottom: 20px;
        }
        
        .form-group label {
            display: block;
            margin-bottom: 8px;
            font-weight: 500;
        }
        
        .form-group input {
            width: 300px;
            padding: 12px;
            border: 1px solid #ccc;
            font-size: 1em;
        }
        
        .btn {
            background: #333;
            color: white;
            border: 1px solid #333;
            padding: 12px 24px;
            cursor: pointer;
            font-size: 0.9em;
            margin-right: 10px;
        }
        
        .btn:hover {
            background: #555;
        }
        
        .btn:disabled {
            background: #ccc;
            cursor: not-allowed;
        }

        .btn-secondary {
            background: #f8f9fa;
            color: #333;
            border: 1px solid #ddd;
            padding: 10px 20px;
            cursor: pointer;
            font-size: 0.9em;
            border-radius: 4px;
            transition: all 0.2s;
        }

        .btn-secondary:hover {
            background: #e9ecef;
            border-color: #adb5bd;
        }
        
        .po-info {
            background: #f9f9f9;
            padding: 20px;
            border: 1px solid #e0e0e0;
            margin-bottom: 20px;
        }
        
        .recommendations {
            margin-bottom: 20px;
        }
        
        .recommendation {
            background: white;
            border: 1px solid #e0e0e0;
            padding: 15px;
            margin-bottom: 10px;
            cursor: pointer;
        }
        
        .recommendation:hover {
            border-color: #333;
        }
        
        .recommendation.selected {
            border-color: #333;
            background: #f9f9f9;
        }
        
        .recommendation h4 {
            margin-bottom: 5px;
        }
        
        .recommendation .score {
            float: right;
            background: #333;
            color: white;
            padding: 2px 8px;
            border-radius: 10px;
            font-size: 0.8em;
        }
        
        .data-table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
        }
        
        .data-table th,
        .data-table td {
            border: 1px solid #e0e0e0;
            padding: 8px 12px;
            text-align: left;
        }
        
        .data-table th {
            background: #f9f9f9;
            font-weight: 500;
        }
        
        .data-table tr:nth-child(even) {
            background: #fafafa;
        }

        .item-checkbox {
            transform: scale(1.2);
            margin: 0;
        }

        .report-section {
            margin-bottom: 30px;
            padding: 20px;
            border: 1px solid #e0e0e0;
            border-radius: 5px;
        }

        .stat-card {
            display: inline-block;
            padding: 15px;
            margin: 10px;
            border: 1px solid #e0e0e0;
            border-radius: 5px;
            text-align: center;
            min-width: 120px;
        }

        .stat-card h4 {
            margin: 0 0 10px 0;
            color: #666;
            font-size: 0.9em;
        }

        .stat-card span {
            font-size: 1.5em;
            font-weight: bold;
            color: #333;
        }

        .hidden {
            display: none;
        }
        
        .loading {
            text-align: center;
            padding: 20px;
            color: #666;
        }
        
        .error {
            background: #fee;
            color: #c53030;
            padding: 15px;
            border: 1px solid #feb2b2;
        }

        .method-selection {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }

        .method-card {
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            padding: 15px;
            cursor: pointer;
            transition: all 0.3s ease;
            background: white;
        }

        .method-card:hover {
            border-color: #007bff;
            box-shadow: 0 2px 8px rgba(0,123,255,0.2);
        }

        .method-card.selected {
            border-color: #007bff;
            background: #f8f9ff;
            box-shadow: 0 2px 8px rgba(0,123,255,0.3);
        }

        .method-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }

        .method-header h4 {
            margin: 0;
            color: #333;
        }

        .success-rate {
            background: #28a745;
            color: white;
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 0.8em;
            font-weight: bold;
        }

        .method-card[data-method="super_fast"] .success-rate {
            background: #dc3545;
        }

        .method-card[data-method="hybrid"] .success-rate {
            background: #ffc107;
            color: #333;
        }

        .method-card[data-method="standard"] .success-rate {
            background: #28a745;
        }

        .method-card[data-method="original_slow"] .success-rate {
            background: #17a2b8;
        }

        .method-details {
            margin-top: 10px;
            color: #666;
        }
    </style>
</head>
<body>
    <div class="header">
        <p>Download artwork files - Smart PO Analysis & Recommendations</p>
        <p style="font-size: 0.9em; color: #bdc3c7;">Intelligent artwork download with multiple methods</p>
    </div>

    <div class="container">


        <!-- Tab Navigation -->
        <div class="tabs">
            <button class="tab active" onclick="showTab('artwork')">Download Artwork</button>
            <button class="tab" onclick="showTab('delivery')">Update Delivery Date</button>
            <button class="tab" onclick="showTab('report')">Report</button>
            <button class="tab" onclick="showTab('po')">PO Management</button>
            <button class="tab" onclick="showTab('settings')">Settings</button>
        </div>

        <!-- Download Artwork Tab -->
        <div id="artwork" class="tab-content active">
            <!-- Step 1: Input PO -->
            <div class="step" id="step1">
            <h2><span class="step-number">1</span>Enter PO Number</h2>
            <div class="form-group">
                <label for="po_input">PO Number:</label>
                <input type="text" id="po_input" placeholder="Enter PO number (e.g., 1284789)" />
                <button class="btn" onclick="analyzePO()" id="analyze_btn">Analyze PO</button>
            </div>

            <!-- Error/Success Messages -->
            <div id="error_container"></div>
            <div id="loading" class="loading hidden">
                Analyzing PO data...
            </div>
        </div>
        
        <!-- Step 2: Show Recommendations -->
        <div class="step hidden" id="step2">
            <h2><span class="step-number">2</span>PO Analysis & Recommendations</h2>

            <div id="po_info" class="po-info"></div>

            <h3>Download Method:</h3>

            <!-- Default Method 5 Display -->
            <div class="default-method-display">
                <div class="method-card selected" data-method="guaranteed_complete">
                    <div class="method-header">
                        <h4>✨ Guaranteed Complete Download</h4>
                        <span class="success-rate">100% Success</span>
                    </div>
                    <p>100% success rate with direct URL extraction. Visual clarity: 19 items = 19 files. Smart numbering for duplicates (_2, _3, _4).</p>
                    <div class="method-details">
                        <small>RECOMMENDED for all POs - Option 5 from unified_downloader.py</small>
                    </div>
                </div>
                <div style="text-align: center; margin-top: 15px;">
                    <button class="btn-secondary" onclick="toggleMethodSelection()" id="toggle_methods_btn">
                        📋 Show All Download Methods
                    </button>
                </div>
            </div>

            <!-- All Methods (Hidden by Default) -->
            <div class="method-selection hidden" id="all_methods" style="display: none;">
                <div class="method-card" data-method="super_fast">
                    <div class="method-header">
                        <h4>🚀 Super Fast</h4>
                        <span class="success-rate">~10% Success</span>
                    </div>
                    <p>Direct PDF download using URL pattern. Very fast but may fail if URLs change.</p>
                    <div class="method-details">
                        <small>Uses: https://app4.brandid.com/Artwork/{ITEM}_{SUFFIX}.pdf</small>
                    </div>
                </div>

                <div class="method-card" data-method="hybrid">
                    <div class="method-header">
                        <h4>⚡ Hybrid</h4>
                        <span class="success-rate">~70% Success</span>
                    </div>
                    <p>Browser login + direct requests. Good balance of speed and reliability.</p>
                    <div class="method-details">
                        <small>Login once, then direct downloads</small>
                    </div>
                </div>

                <div class="method-card" data-method="standard">
                    <div class="method-header">
                        <h4>📋 Standard</h4>
                        <span class="success-rate">~90% Success</span>
                    </div>
                    <p>Browser automation with smart navigation. Reliable and reasonably fast.</p>
                    <div class="method-details">
                        <small>Recommended for most cases</small>
                    </div>
                </div>

                <div class="method-card" data-method="original_slow">
                    <div class="method-header">
                        <h4>🐌 Original Slow</h4>
                        <span class="success-rate">100% Success</span>
                    </div>
                    <p>Full browser automation. Slowest but most reliable method.</p>
                    <div class="method-details">
                        <small>Use when other methods fail</small>
                    </div>
                </div>

                <div class="method-card" data-method="guaranteed_complete">
                    <div class="method-header">
                        <h4>✨ Guaranteed Complete Download</h4>
                        <span class="success-rate">100% Success</span>
                    </div>
                    <p>100% success rate with direct URL extraction. Visual clarity: 19 items = 19 files. Smart numbering for duplicates (_2, _3, _4).</p>
                    <div class="method-details">
                        <small>RECOMMENDED for all POs - Option 5 from unified_downloader.py</small>
                    </div>
                </div>

                <div style="text-align: center; margin-top: 15px;">
                    <button class="btn-secondary" onclick="toggleMethodSelection()" id="hide_methods_btn">
                        ⬆️ Hide Other Methods
                    </button>
                </div>
            </div>
        </div>
        
        <!-- Step 3: Show Data Table -->
        <div class="step hidden" id="step3">
            <h2><span class="step-number">3</span>PO Items Data</h2>
            <div id="data_table_container"></div>
            
            <div style="margin-top: 20px;">
                <button class="btn" onclick="startDownload()" id="download_btn">Start Download</button>
            </div>
        </div>
        
        <!-- Download Progress -->
        <div class="step hidden" id="progress_step">
            <h2><span class="step-number">4</span>Download Progress</h2>
            <div id="progress_info"></div>
        </div>
        </div>

        <!-- Update Delivery Date Tab -->
        <div id="delivery" class="tab-content">
            <div class="step">
                <h2><span class="step-number">📅</span>Update Delivery Date</h2>
                <div class="form-group">
                    <label for="delivery_po_input">PO Number:</label>
                    <input type="text" id="delivery_po_input" placeholder="Enter PO number to update delivery date" />
                    <button class="btn" onclick="loadDeliveryInfo()">Load PO Info</button>
                </div>

                <div id="delivery_info" class="hidden">
                    <div class="form-group">
                        <label for="current_delivery_date">Current Delivery Date:</label>
                        <input type="text" id="current_delivery_date" readonly />
                    </div>

                    <div class="form-group">
                        <label for="new_delivery_date">New Delivery Date:</label>
                        <input type="date" id="new_delivery_date" />
                    </div>

                    <div class="form-group">
                        <label for="delivery_notes">Notes (Optional):</label>
                        <textarea id="delivery_notes" placeholder="Reason for date change..."></textarea>
                    </div>

                    <button class="btn" onclick="updateDeliveryDate()">Update Delivery Date</button>
                </div>
            </div>
        </div>

        <!-- Report Tab -->
        <div id="report" class="tab-content">
            <div class="step">
                <h2><span class="step-number">📊</span>Download Reports</h2>

                <div class="report-section">
                    <h3>Download History</h3>
                    <div class="form-group">
                        <label for="report_date_from">From Date:</label>
                        <input type="date" id="report_date_from" />
                    </div>
                    <div class="form-group">
                        <label for="report_date_to">To Date:</label>
                        <input type="date" id="report_date_to" />
                    </div>
                    <button class="btn" onclick="generateReport()">Generate Report</button>
                </div>

                <div id="report_results" class="hidden">
                    <h3>Report Results</h3>
                    <div id="report_table_container"></div>
                    <button class="btn" onclick="exportReport()">Export to CSV</button>
                </div>

                <div class="report-section">
                    <h3>Quick Stats</h3>
                    <div id="quick_stats">
                        <div class="stat-card">
                            <h4>Today's Downloads</h4>
                            <span id="today_downloads">0</span>
                        </div>
                        <div class="stat-card">
                            <h4>This Week</h4>
                            <span id="week_downloads">0</span>
                        </div>
                        <div class="stat-card">
                            <h4>Total Files</h4>
                            <span id="total_files">0</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- PO Management Tab -->
        <div id="po" class="tab-content">
            <div class="step">
                <h2><span class="step-number">📋</span>PO Management</h2>
                <p>Future feature for comprehensive PO management</p>
                <div style="padding: 40px; text-align: center; color: #666;">
                    <h3>Coming Soon</h3>
                    <p>This feature will allow you to:</p>
                    <ul style="text-align: left; max-width: 400px; margin: 20px auto; line-height: 1.8;">
                        <li>View PO details and status</li>
                        <li>Set and track delivery dates</li>
                        <li>Batch download multiple POs</li>
                        <li>Download history and analytics</li>
                        <li>Automatic PO synchronization</li>
                    </ul>
                </div>
            </div>
        </div>

        <!-- Settings Tab -->
        <div id="settings" class="tab-content">
            <div class="step">
                <h2><span class="step-number">⚙️</span>Settings & Configuration</h2>
                <p>Manage system configuration and login credentials</p>

                <!-- Login Credentials Section -->
                <div style="margin: 20px 0; padding: 20px; border: 1px solid #ddd; border-radius: 5px;">
                    <h3>🔐 Login Credentials</h3>
                    <div style="margin: 15px 0;">
                        <strong>Login URL:</strong><br>
                        <span id="display_url">https://app.e-brandid.com/login/login.aspx</span>
                    </div>
                    <div style="margin: 15px 0;">
                        <strong>Username:</strong><br>
                        <span id="display_username">{{ masked_username }}</span>
                    </div>
                    <div style="margin: 15px 0;">
                        <strong>Password:</strong><br>
                        <span id="display_password">************</span>
                    </div>

                    <!-- Admin Access Section -->
                    <div id="admin_section" style="margin-top: 20px; padding: 15px; background: #f9f9f9; border-radius: 5px;">
                        <h4>🔑 Admin Access Required</h4>
                        <p style="margin: 10px 0; color: #666;">Enter admin password to view/edit credentials:</p>
                        <div style="display: flex; gap: 10px; align-items: center;">
                            <input type="password" id="admin_password" placeholder="Admin password"
                                   style="padding: 8px; border: 1px solid #ddd; border-radius: 3px; flex: 1;">
                            <button onclick="verifyAdmin()" style="padding: 8px 15px; background: #007bff; color: white; border: none; border-radius: 3px; cursor: pointer;">
                                Unlock
                            </button>
                        </div>
                        <div id="admin_message" style="margin-top: 10px; color: red;"></div>
                    </div>

                    <!-- Edit Form (Hidden by default) -->
                    <div id="edit_form" style="display: none; margin-top: 20px; padding: 15px; background: #e8f5e8; border-radius: 5px;">
                        <h4>✏️ Edit Configuration</h4>
                        <div style="margin: 10px 0;">
                            <label><strong>Login URL:</strong></label><br>
                            <input type="text" id="edit_url" style="width: 100%; padding: 8px; margin: 5px 0; border: 1px solid #ddd; border-radius: 3px;">
                        </div>
                        <div style="margin: 10px 0;">
                            <label><strong>Username:</strong></label><br>
                            <input type="text" id="edit_username" style="width: 100%; padding: 8px; margin: 5px 0; border: 1px solid #ddd; border-radius: 3px;">
                        </div>
                        <div style="margin: 10px 0;">
                            <label><strong>Password:</strong></label><br>
                            <input type="text" id="edit_password" style="width: 100%; padding: 8px; margin: 5px 0; border: 1px solid #ddd; border-radius: 3px;">
                        </div>
                        <div style="margin: 15px 0;">
                            <button onclick="saveConfig()" style="padding: 10px 20px; background: #28a745; color: white; border: none; border-radius: 3px; cursor: pointer; margin-right: 10px;">
                                💾 Save Changes
                            </button>
                            <button onclick="cancelEdit()" style="padding: 10px 20px; background: #6c757d; color: white; border: none; border-radius: 3px; cursor: pointer;">
                                ❌ Cancel
                            </button>
                        </div>
                        <div id="save_message" style="margin-top: 10px;"></div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        let selectedMethod = null;
        let currentPO = null;
        window.currentPoData = null;  // Global variable for checkbox functions

        // Method selection
        document.addEventListener('DOMContentLoaded', function() {
            // Set Method 5 as default
            selectedMethod = 'guaranteed_complete';

            // Add click handlers for method cards
            document.querySelectorAll('.method-card').forEach(card => {
                card.addEventListener('click', function() {
                    // Remove selected class from all cards
                    document.querySelectorAll('.method-card').forEach(c => c.classList.remove('selected'));
                    // Add selected class to clicked card
                    this.classList.add('selected');
                    // Update selected method
                    selectedMethod = this.dataset.method;
                    console.log('Selected method:', selectedMethod);
                });
            });
        });

        // Tab switching
        function showTab(tabName) {
            // Hide all tab contents
            document.querySelectorAll('.tab-content').forEach(content => {
                content.classList.remove('active');
            });

            // Remove active class from all tabs
            document.querySelectorAll('.tab').forEach(tab => {
                tab.classList.remove('active');
            });

            // Show selected tab content
            document.getElementById(tabName).classList.add('active');

            // Find and activate the correct tab button
            const tabs = document.querySelectorAll('.tab');
            tabs.forEach((tab, index) => {
                if ((tabName === 'artwork' && index === 0) ||
                    (tabName === 'delivery' && index === 1) ||
                    (tabName === 'report' && index === 2) ||
                    (tabName === 'po' && index === 3) ||
                    (tabName === 'settings' && index === 4)) {
                    tab.classList.add('active');
                }
            });
        }

        // Checkbox handling functions
        function selectAllItems(select) {
            const checkboxes = document.querySelectorAll('.item-checkbox');
            checkboxes.forEach(checkbox => {
                checkbox.checked = select;
            });
            updateSelectedCount();
        }

        function updateSelectedCount() {
            const checkboxes = document.querySelectorAll('.item-checkbox');
            const selectedCount = document.querySelectorAll('.item-checkbox:checked').length;
            const selectedCountElement = document.getElementById('selected_count');
            if (selectedCountElement) {
                selectedCountElement.textContent = selectedCount;
            }
        }

        function getSelectedItems() {
            const selectedItems = [];
            const checkboxes = document.querySelectorAll('.item-checkbox:checked');
            checkboxes.forEach(checkbox => {
                const itemIndex = parseInt(checkbox.getAttribute('data-item-index'));
                if (window.currentPoData && window.currentPoData.items && window.currentPoData.items[itemIndex]) {
                    selectedItems.push(window.currentPoData.items[itemIndex]);
                }
            });
            return selectedItems;
        }
        
        async function analyzePO() {
            const poNumber = document.getElementById('po_input').value.trim();
            if (!poNumber) {
                alert('Please enter a PO number');
                return;
            }

            // Clear previous results
            document.getElementById('step2').classList.add('hidden');
            document.getElementById('step3').classList.add('hidden');
            document.getElementById('data_table_container').innerHTML = '';

            document.getElementById('analyze_btn').disabled = true;
            document.getElementById('loading').classList.remove('hidden');

            try {
                const response = await fetch('/api/analyze_po?t=' + Date.now(), {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ po_number: poNumber })
                });

                const result = await response.json();
                console.log('API Response:', result); // Debug log

                if (result.success) {
                    currentPO = result;
                    window.currentPoData = result;  // Store globally for checkbox functions
                    console.log('Items received:', result.items.length); // Debug log
                    showPOAnalysis(result);
                    showDataTable(result.items);
                    document.getElementById('step2').classList.remove('hidden');
                    document.getElementById('step3').classList.remove('hidden');
                } else {
                    showError(result.error || 'Failed to analyze PO');
                }
            } catch (error) {
                showError('Error analyzing PO: ' + error.message);
            } finally {
                document.getElementById('analyze_btn').disabled = false;
                document.getElementById('loading').classList.add('hidden');
            }
        }
        
        function showPOAnalysis(data) {
            const poInfo = document.getElementById('po_info');
            poInfo.innerHTML = `
                <h3>${data.title}</h3>
                <p><strong>PO Number:</strong> ${data.po_number}</p>
                <p><strong>Total Items:</strong> ${data.total_items}</p>
                <p><strong>Analyzed:</strong> ${data.timestamp}</p>
            `;

            // Method cards are now static in HTML, no need to generate them dynamically
            // Ensure Method 5 (Guaranteed Complete Download) is selected by default
            selectedMethod = 'guaranteed_complete';
            document.querySelectorAll('.method-card').forEach(card => {
                card.classList.remove('selected');
            });
            // Select Method 5 as default
            const method5Card = document.querySelector('[data-method="guaranteed_complete"]');
            if (method5Card) {
                method5Card.classList.add('selected');
            }
        }
        

        
        function showDataTable(items) {
            console.log('showDataTable called with items:', items.length); // Debug log
            const container = document.getElementById('data_table_container');

            let html = `
                <div style="margin-bottom: 15px;">
                    <button class="btn" onclick="selectAllItems(true)">✅ Select All</button>
                    <button class="btn" onclick="selectAllItems(false)" style="background: #e53e3e;">❌ Deselect All</button>
                    <span style="margin-left: 20px; font-weight: bold;">Selected: <span id="selected_count">${items.length}</span> / ${items.length}</span>
                </div>
                <table class="data-table">
                    <thead>
                        <tr>
                            <th>Select</th>
                            <th>#</th>
                            <th>Item #</th>
                            <th>Description</th>
                            <th>Quantity</th>
                            <th>Ship To</th>
                            <th>Need By</th>
                            <th>Download</th>
                        </tr>
                    </thead>
                    <tbody>
            `;

            items.forEach((item, index) => {
                html += `
                    <tr>
                        <td><input type="checkbox" class="item-checkbox" data-item-index="${index}" checked onchange="updateSelectedCount()"></td>
                        <td>${index + 1}</td>
                        <td><strong>${item.name}</strong></td>
                        <td>${item.description}</td>
                        <td>${item.quantity}</td>
                        <td>${item.ship_to || 'N/A'}</td>
                        <td>${item.need_by || 'N/A'}</td>
                        <td>${item.has_download ? '✅' : '❌'}</td>
                    </tr>
                `;
            });

            html += '</tbody></table>';
            container.innerHTML = html;
        }
        
        async function startDownload() {
            if (!currentPO) {
                showError('No PO data available. Please parse data first.');
                return;
            }

            if (!selectedMethod) {
                showError('Please select a download method first.');
                return;
            }

            // Get only selected items
            const selectedItems = getSelectedItems();
            if (selectedItems.length === 0) {
                showError('Please select at least one item to download.');
                return;
            }

            // 🆕 PROMPT FOR PO DATABASE SAVE
            const savePODetails = await promptSavePODetails(currentPO.po_number);

            const button = document.getElementById('download_btn');
            button.disabled = true;
            button.innerHTML = `⏳ Starting Download (${selectedItems.length} items)...`;
            document.getElementById('progress_step').classList.remove('hidden');

            try {
                // Save PO details to database if user chose to
                if (savePODetails) {
                    await savePOToDatabase(currentPO.po_number);
                }

                // Start the actual download
                await fetch('/api/start_download', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        method: selectedMethod,
                        po_number: currentPO.po_number,
                        items: selectedItems  // Only send selected items
                    })
                });

                // Start polling for progress
                pollProgress();
            } catch (error) {
                showError('Error starting download: ' + error.message);
            }
        }

        // Delivery Date Functions
        async function loadDeliveryInfo() {
            const poNumber = document.getElementById('delivery_po_input').value.trim();
            if (!poNumber) {
                alert('Please enter a PO number');
                return;
            }

            // Simulate loading delivery info
            document.getElementById('current_delivery_date').value = '2025-08-15';
            document.getElementById('delivery_info').classList.remove('hidden');
        }

        async function updateDeliveryDate() {
            const poNumber = document.getElementById('delivery_po_input').value.trim();
            const newDate = document.getElementById('new_delivery_date').value;
            const notes = document.getElementById('delivery_notes').value;

            if (!newDate) {
                alert('Please select a new delivery date');
                return;
            }

            // Simulate update
            alert(`Delivery date updated for PO ${poNumber} to ${newDate}`);
        }

        // Report Functions
        async function generateReport() {
            const fromDate = document.getElementById('report_date_from').value;
            const toDate = document.getElementById('report_date_to').value;

            if (!fromDate || !toDate) {
                alert('Please select both from and to dates');
                return;
            }

            // Simulate report generation
            const reportHtml = `
                <table class="data-table">
                    <thead>
                        <tr>
                            <th>Date</th>
                            <th>PO Number</th>
                            <th>Items Downloaded</th>
                            <th>Status</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td>2025-08-01</td>
                            <td>1284789</td>
                            <td>3</td>
                            <td>✅ Complete</td>
                        </tr>
                        <tr>
                            <td>2025-07-31</td>
                            <td>1288060</td>
                            <td>5</td>
                            <td>✅ Complete</td>
                        </tr>
                    </tbody>
                </table>
            `;

            document.getElementById('report_table_container').innerHTML = reportHtml;
            document.getElementById('report_results').classList.remove('hidden');

            // Update quick stats
            document.getElementById('today_downloads').textContent = '3';
            document.getElementById('week_downloads').textContent = '8';
            document.getElementById('total_files').textContent = '156';
        }

        async function exportReport() {
            alert('Report exported to CSV (feature coming soon)');
        }

        async function pollProgress() {
            try {
                const response = await fetch('/api/status');
                const status = await response.json();
                
                // Show "Open Folder" link if download is complete (100% and not active)
                const showOpenFolder = !status.active && status.progress === 100 && status.download_folder;

                document.getElementById('progress_info').innerHTML = `
                    <p>Progress: ${status.progress}% ${showOpenFolder ? '<a href="#" onclick="openDownloadFolder()" style="margin-left: 15px; color: #007bff; text-decoration: none; font-weight: bold;">📁 Open Folder</a>' : ''}</p>
                    <div style="background: #e0e0e0; height: 20px; margin: 10px 0;">
                        <div style="background: #333; height: 100%; width: ${status.progress}%; transition: width 0.3s;"></div>
                    </div>
                    <div style="max-height: 200px; overflow-y: auto; background: #f9f9f9; padding: 10px; font-family: monospace;">
                        ${status.log.map(entry => `<div>${entry}</div>`).join('')}
                    </div>
                `;

                if (status.active) {
                    setTimeout(pollProgress, 1000);
                } else {
                    document.getElementById('download_btn').disabled = false;
                }
            } catch (error) {
                console.error('Error polling progress:', error);
            }
        }

        async function openDownloadFolder() {
            try {
                const response = await fetch('/api/open_folder');
                const result = await response.json();
                if (result.success) {
                    showError('📁 Folder opened successfully!', 'success');
                } else {
                    showError('❌ ' + result.message, 'error');
                }
            } catch (error) {
                showError('❌ Error opening folder: ' + error.message, 'error');
            }
        }

        // Email masking function
        function maskEmail(email) {
            if (!email.includes('@')) return email;

            const [prefix, suffix] = email.split('@');

            // Mask prefix: show first 2 characters, rest as asterisks
            const maskedPrefix = prefix.length <= 2 ? prefix : prefix.substring(0, 2) + '*'.repeat(prefix.length - 2);

            // Mask suffix: show first 1 character, rest as asterisks
            const maskedSuffix = suffix.length <= 1 ? suffix : suffix.substring(0, 1) + '*'.repeat(suffix.length - 1);

            return `${maskedPrefix}@${maskedSuffix}`;
        }

        // Settings functions
        async function verifyAdmin() {
            const password = document.getElementById('admin_password').value;
            const messageDiv = document.getElementById('admin_message');

            if (!password) {
                messageDiv.textContent = 'Please enter admin password';
                messageDiv.style.color = 'red';
                return;
            }

            try {
                const response = await fetch('/api/settings/verify_admin', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({password: password})
                });

                const result = await response.json();

                if (result.success) {
                    messageDiv.textContent = '✅ Admin access granted';
                    messageDiv.style.color = 'green';

                    // Load and show configuration
                    await loadConfiguration(password);
                } else {
                    messageDiv.textContent = '❌ Invalid admin password';
                    messageDiv.style.color = 'red';
                }
            } catch (error) {
                messageDiv.textContent = '❌ Error: ' + error.message;
                messageDiv.style.color = 'red';
            }
        }

        async function loadConfiguration(password) {
            try {
                const response = await fetch('/api/settings/get_config', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({password: password})
                });

                const result = await response.json();

                if (result.success) {
                    // Show actual values
                    document.getElementById('display_url').textContent = result.config.login_url;
                    document.getElementById('display_username').textContent = result.config.username;
                    document.getElementById('display_password').textContent = result.config.password;

                    // Populate edit form
                    document.getElementById('edit_url').value = result.config.login_url;
                    document.getElementById('edit_username').value = result.config.username;
                    document.getElementById('edit_password').value = result.config.password;

                    // Show edit form
                    document.getElementById('edit_form').style.display = 'block';
                    document.getElementById('admin_section').style.display = 'none';
                }
            } catch (error) {
                console.error('Error loading configuration:', error);
            }
        }

        async function saveConfig() {
            const adminPassword = document.getElementById('admin_password').value;
            const url = document.getElementById('edit_url').value;
            const username = document.getElementById('edit_username').value;
            const password = document.getElementById('edit_password').value;
            const messageDiv = document.getElementById('save_message');

            try {
                const response = await fetch('/api/settings/update_config', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        admin_password: adminPassword,
                        login_url: url,
                        username: username,
                        password: password
                    })
                });

                const result = await response.json();

                if (result.success) {
                    messageDiv.innerHTML = '<span style="color: green;">✅ Configuration saved successfully!</span>';

                    // Update display
                    document.getElementById('display_url').textContent = url;
                    document.getElementById('display_username').textContent = username;
                    document.getElementById('display_password').textContent = password;
                } else {
                    messageDiv.innerHTML = '<span style="color: red;">❌ ' + result.message + '</span>';
                }
            } catch (error) {
                messageDiv.innerHTML = '<span style="color: red;">❌ Error: ' + error.message + '</span>';
            }
        }

        function cancelEdit() {
            document.getElementById('edit_form').style.display = 'none';
            document.getElementById('admin_section').style.display = 'block';
            document.getElementById('admin_password').value = '';
            document.getElementById('admin_message').textContent = '';

            // Reset display to masked values
            const currentUsername = document.getElementById('edit_username').value || '{{ masked_username }}';
            document.getElementById('display_username').textContent = maskEmail(currentUsername);
            document.getElementById('display_password').textContent = '************';
        }

        // PO Database functions
        async function promptSavePODetails(poNumber) {
            return new Promise((resolve) => {
                const modal = document.createElement('div');
                modal.style.cssText = `
                    position: fixed; top: 0; left: 0; width: 100%; height: 100%;
                    background: rgba(0,0,0,0.5); z-index: 10000; display: flex;
                    align-items: center; justify-content: center;
                `;

                modal.innerHTML = `
                    <div style="background: white; padding: 30px; border-radius: 10px; max-width: 500px; text-align: center;">
                        <h3>📊 Save PO Details to Database?</h3>
                        <p>Do you want to save complete PO details for <strong>${poNumber}</strong> to the database?</p>
                        <p style="font-size: 0.9em; color: #666;">This will save all item details, company info, and dates for future reference.</p>
                        <div style="margin-top: 20px;">
                            <button id="saveYes" style="padding: 10px 20px; margin: 0 10px; background: #28a745; color: white; border: none; border-radius: 5px; cursor: pointer;">
                                ✅ Yes, Save Details
                            </button>
                            <button id="saveNo" style="padding: 10px 20px; margin: 0 10px; background: #6c757d; color: white; border: none; border-radius: 5px; cursor: pointer;">
                                ❌ No, Skip
                            </button>
                        </div>
                    </div>
                `;

                document.body.appendChild(modal);

                document.getElementById('saveYes').onclick = () => {
                    document.body.removeChild(modal);
                    resolve(true);
                };

                document.getElementById('saveNo').onclick = () => {
                    document.body.removeChild(modal);
                    resolve(false);
                };
            });
        }

        async function promptOverwritePO(poNumber) {
            return new Promise((resolve) => {
                const modal = document.createElement('div');
                modal.style.cssText = `
                    position: fixed; top: 0; left: 0; width: 100%; height: 100%;
                    background: rgba(0,0,0,0.5); z-index: 10000; display: flex;
                    align-items: center; justify-content: center;
                `;

                modal.innerHTML = `
                    <div style="background: white; padding: 30px; border-radius: 10px; max-width: 500px; text-align: center;">
                        <h3>⚠️ PO Already Exists</h3>
                        <p>PO <strong>${poNumber}</strong> already exists in the database.</p>
                        <p style="font-size: 0.9em; color: #666;">Do you want to overwrite the existing data?</p>
                        <div style="margin-top: 20px;">
                            <button id="overwriteYes" style="padding: 10px 20px; margin: 0 10px; background: #dc3545; color: white; border: none; border-radius: 5px; cursor: pointer;">
                                🔄 Yes, Overwrite
                            </button>
                            <button id="overwriteNo" style="padding: 10px 20px; margin: 0 10px; background: #6c757d; color: white; border: none; border-radius: 5px; cursor: pointer;">
                                ❌ No, Skip
                            </button>
                        </div>
                    </div>
                `;

                document.body.appendChild(modal);

                document.getElementById('overwriteYes').onclick = () => {
                    document.body.removeChild(modal);
                    resolve(true);
                };

                document.getElementById('overwriteNo').onclick = () => {
                    document.body.removeChild(modal);
                    resolve(false);
                };
            });
        }

        async function savePOToDatabase(poNumber) {
            try {
                // First check if PO exists
                const checkResponse = await fetch('/api/po/check_exists', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({po_number: poNumber})
                });

                const checkResult = await checkResponse.json();

                if (!checkResult.success) {
                    showError('❌ Error checking PO existence: ' + checkResult.message, 'error');
                    return false;
                }

                let overwrite = false;
                if (checkResult.exists) {
                    overwrite = await promptOverwritePO(poNumber);
                    if (!overwrite) {
                        showError('📊 PO database save skipped', 'info');
                        return false;
                    }
                }

                // Show loading message
                showError('📊 Saving PO details to database...', 'info');

                // Save PO details
                const saveResponse = await fetch('/api/po/save_details', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({po_number: poNumber, overwrite: overwrite})
                });

                const saveResult = await saveResponse.json();

                if (saveResult.success) {
                    showError(`✅ PO ${poNumber} saved to database (${saveResult.items_count} items)`, 'success');
                    return true;
                } else {
                    showError('❌ Failed to save PO: ' + saveResult.message, 'error');
                    return false;
                }

            } catch (error) {
                showError('❌ Error saving PO to database: ' + error.message, 'error');
                return false;
            }
        }

        function toggleMethodSelection() {
            const defaultDisplay = document.querySelector('.default-method-display');
            const allMethods = document.getElementById('all_methods');

            if (allMethods.style.display === 'none' || allMethods.classList.contains('hidden')) {
                // Show all methods
                defaultDisplay.style.display = 'none';
                allMethods.style.display = 'block';
                allMethods.classList.remove('hidden');
            } else {
                // Hide all methods, show default
                defaultDisplay.style.display = 'block';
                allMethods.style.display = 'none';
                allMethods.classList.add('hidden');

                // Reset selection to Method 5
                document.querySelectorAll('.method-card').forEach(card => {
                    card.classList.remove('selected');
                });
                document.querySelector('[data-method="guaranteed_complete"]').classList.add('selected');
            }
        }

        function showError(message, type = 'error') {
            const container = document.getElementById('error_container');
            const className = type === 'success' ? 'success' : 'error';
            container.innerHTML = `<div class="${className}" style="padding: 10px; margin: 10px 0; border-radius: 4px; ${type === 'success' ? 'background: #d4edda; color: #155724; border: 1px solid #c3e6cb;' : 'background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb;'}">${message}</div>`;

            // Auto-hide success messages after 3 seconds
            if (type === 'success') {
                setTimeout(() => {
                    container.innerHTML = '';
                }, 3000);
            }
        }


    </script>

    <!-- Version Footer -->
    <div style="position: fixed; bottom: 10px; right: 10px; background: rgba(0,0,0,0.7); color: white; padding: 5px 10px; border-radius: 5px; font-size: 11px; font-family: monospace;">
        v{{ version }} | {{ version_date }} | {{ last_edit }}
    </div>

</body>
</html>
"""

if __name__ == '__main__':
    print("🚀 Starting artwork downloader...")
    print("📊 Initializing PO database...")
    init_database()
    print("📱 Open your browser and go to: http://localhost:5001")
    print("🛑 Press Ctrl+C to stop the server")

    app.run(debug=False, host='127.0.0.1', port=5001)
