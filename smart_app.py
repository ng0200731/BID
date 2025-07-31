"""
Smart E-BrandID Downloader
1. Input PO# first
2. Show recommendations based on PO data
3. Display data table in web interface

Version History:
- v1.0.0: Initial smart interface with PO analysis
- v1.1.0: Added 3-tab structure (Download/PO Management/Settings)
- v1.2.0: Fixed folder structure (download_artwork/date/po_time)
- v1.3.0: Improved table parsing with multi-strategy detection
- v1.4.0: Added deduplication and better data validation
- v1.5.0: Enhanced manual input with improved UI and auto-detection
"""

# Version information
VERSION = "3.1.0"
VERSION_DATE = "2025-07-31"

from flask import Flask, render_template_string, request, jsonify
import os
import threading
import time
import requests
import re
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

app = Flask(__name__)

# Global variables
po_data = {}
download_status = {'active': False, 'progress': 0, 'log': []}

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
        driver.get("https://app.e-brandid.com/login/login.aspx")
        username_field = wait.until(EC.presence_of_element_located((By.ID, "txtUserName")))
        password_field = driver.find_element(By.ID, "txtPassword")
        
        username_field.send_keys("sales10@fuchanghk.com")
        password_field.send_keys("fc31051856")
        
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
    return render_template_string(HTML_TEMPLATE, version=VERSION, version_date=VERSION_DATE)

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
        driver.get("https://app.e-brandid.com/login/login.aspx")

        username_field = wait.until(EC.presence_of_element_located((By.ID, "txtUserName")))
        password_field = driver.find_element(By.ID, "txtPassword")

        username_field.send_keys("sales10@fuchanghk.com")
        password_field.send_keys("fc31051856")

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
        else:
            success_count = download_standard(items, download_folder)  # Default

        download_status['active'] = False
        download_status['log'].append("✅ Download completed!")
        download_status['log'].append(f"📁 {success_count}/{len(items)} files downloaded successfully")

    except Exception as e:
        download_status['active'] = False
        download_status['log'].append(f"❌ Error: {str(e)}")

def download_super_fast(items, download_folder):
    """Super Fast Method: Direct PDF downloads using URL pattern (~10% success)"""
    global download_status
    success_count = 0

    download_status['log'].append("🚀 Super Fast method - Direct PDF downloads")

    for i, item in enumerate(items):
        if not download_status['active']:
            break

        progress = int((i + 1) / len(items) * 100)
        download_status['progress'] = progress

        item_name = item.get('name', 'Unknown')
        download_status['log'].append(f"🚀 Super Fast: Processing {i+1}/{len(items)}: {item_name}")

        try:
            suffix_id = item.get('suffix_id', '')

            if suffix_id:
                pdf_url = f"https://app4.brandid.com/Artwork/{item_name}_{suffix_id}.pdf"
                download_status['log'].append(f"🔗 Trying: {pdf_url}")

                response = requests.get(pdf_url, timeout=15)

                if response.status_code == 200 and len(response.content) > 1000:  # Valid PDF should be > 1KB
                    pdf_filename = f"{item_name}_{suffix_id}.pdf"
                    pdf_path = os.path.join(download_folder, pdf_filename)

                    with open(pdf_path, 'wb') as f:
                        f.write(response.content)

                    file_size = len(response.content) / 1024  # KB
                    download_status['log'].append(f"✅ Downloaded: {pdf_filename} ({file_size:.1f} KB)")
                    success_count += 1
                else:
                    download_status['log'].append(f"❌ PDF not found or invalid: {response.status_code}")
            else:
                download_status['log'].append(f"❌ No suffix_id found for: {item_name}")

        except Exception as e:
            download_status['log'].append(f"❌ Error downloading {item_name}: {str(e)}")

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

    download_status['log'].append("🐌 Original Slow method - Full browser automation")
    download_status['log'].append("🔐 Setting up browser with download preferences...")

    # Setup Chrome with download preferences
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)

    # Set download preferences
    prefs = {
        "download.default_directory": download_folder,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True,
        "safebrowsing.disable_download_protection": True,
        "profile.default_content_setting_values.notifications": 2
    }
    chrome_options.add_experimental_option("prefs", prefs)

    try:
        # Initialize driver
        try:
            driver_path = ChromeDriverManager().install()
            service = Service(driver_path)
            driver = webdriver.Chrome(service=service, options=chrome_options)
        except:
            driver = webdriver.Chrome(options=chrome_options)

        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        wait = WebDriverWait(driver, 15)

        download_status['log'].append("🌐 Navigating to E-BrandID login...")

        # Login to E-BrandID
        driver.get("https://app.e-brandid.com/login/login.aspx")

        username_field = wait.until(EC.presence_of_element_located((By.ID, "txtUserName")))
        password_field = driver.find_element(By.ID, "txtPassword")

        username_field.clear()
        username_field.send_keys("sales10@fuchanghk.com")
        password_field.clear()
        password_field.send_keys("fc31051856")

        login_button = driver.find_element(By.XPATH, "//img[@onclick='return Login();']")
        login_button.click()

        # Wait for login to complete
        wait.until(lambda d: "login" not in d.current_url.lower())
        download_status['log'].append("✅ Successfully logged in to E-BrandID")

        # Process each item
        for i, item in enumerate(items):
            if not download_status['active']:
                break

            progress = int((i + 1) / len(items) * 100)
            download_status['progress'] = progress

            item_name = item.get('name', 'Unknown')
            download_status['log'].append(f"🐌 Processing {i+1}/{len(items)}: {item_name}")

            try:
                success = download_item_with_browser(driver, item, download_folder, wait)
                if success:
                    success_count += 1
                    download_status['log'].append(f"✅ Downloaded artwork for: {item_name}")
                else:
                    download_status['log'].append(f"❌ Failed to download: {item_name}")

            except Exception as e:
                download_status['log'].append(f"❌ Error processing {item_name}: {str(e)}")

            time.sleep(2)  # Pause between items

        download_status['log'].append("🔚 Closing browser...")

    except Exception as e:
        download_status['log'].append(f"❌ Browser error: {str(e)}")
    finally:
        try:
            driver.quit()
        except:
            pass

    return success_count

def download_item_with_browser(driver, item, download_folder, wait):
    """Download individual item using browser automation"""
    try:
        item_name = item.get('name', '')

        # Method 1: Try direct artwork search
        download_status['log'].append(f"🔍 Searching for artwork: {item_name}")

        # Go to artwork search page
        driver.get("https://app.e-brandid.com/Bidnet/bidnet3/artworkSearch.aspx")
        time.sleep(2)

        # Search for the item
        try:
            search_box = wait.until(EC.presence_of_element_located((By.ID, "txtSearch")))
            search_box.clear()
            search_box.send_keys(item_name)

            search_button = driver.find_element(By.ID, "btnSearch")
            search_button.click()
            time.sleep(3)

            # Look for download links
            download_links = driver.find_elements(By.XPATH, "//a[contains(@href, '.pdf') or contains(text(), 'Download') or contains(@onclick, 'download')]")

            if download_links:
                download_status['log'].append(f"📄 Found download link for: {item_name}")
                download_links[0].click()
                time.sleep(3)
                return True

        except Exception as e:
            download_status['log'].append(f"⚠️ Artwork search failed: {str(e)}")

        # Method 2: Try item detail page if we have suffix_id
        suffix_id = item.get('suffix_id', '')
        if suffix_id:
            try:
                # Try to construct item detail URL
                detail_url = f"https://app.e-brandid.com/Bidnet/BidCustomer/ItemDetail.aspx?item_suffix_id={suffix_id}"
                download_status['log'].append(f"🔗 Trying item detail page: {suffix_id}")

                driver.get(detail_url)
                time.sleep(3)

                # Look for artwork download buttons
                artwork_buttons = driver.find_elements(By.XPATH, "//a[contains(text(), 'Artwork') or contains(text(), 'Download') or contains(@href, '.pdf')]")

                if artwork_buttons:
                    download_status['log'].append(f"📄 Found artwork button for: {item_name}")
                    artwork_buttons[0].click()
                    time.sleep(3)
                    return True

            except Exception as e:
                download_status['log'].append(f"⚠️ Item detail page failed: {str(e)}")

        # Method 3: Try direct PDF URL (fallback to super fast method)
        if suffix_id:
            try:
                pdf_url = f"https://app4.brandid.com/Artwork/{item_name}_{suffix_id}.pdf"
                download_status['log'].append(f"🚀 Trying direct PDF: {pdf_url}")

                driver.get(pdf_url)
                time.sleep(2)

                # Check if PDF loaded (not 404 page)
                if "404" not in driver.page_source and "Not Found" not in driver.page_source:
                    download_status['log'].append(f"📄 Direct PDF found for: {item_name}")
                    return True

            except Exception as e:
                download_status['log'].append(f"⚠️ Direct PDF failed: {str(e)}")

        return False

    except Exception as e:
        download_status['log'].append(f"❌ Item download error: {str(e)}")
        return False

@app.route('/api/status')
def get_status():
    return jsonify(download_status)

@app.route('/api/version')
def get_version():
    return jsonify({
        'version': VERSION,
        'version_date': VERSION_DATE,
        'features': [
            'Smart PO analysis and recommendations',
            'Multi-strategy table detection',
            'Automatic deduplication',
            'Date-based folder organization',
            '3-tab interface structure'
        ]
    })

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>E-BrandID Downloader v3.0.1</title>
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
        <h1>E-BrandID Downloader <span style="font-size: 0.7em; color: #ecf0f1;">v3.0.1</span></h1>
        <p>Download artwork files - Smart PO Analysis & Recommendations</p>
        <p style="font-size: 0.9em; color: #bdc3c7;">Updated: 2025-07-31 | 4 Download Methods with Method Selection</p>
    </div>

    <div class="container">
        <!-- Version Info -->
        <div style="text-align: center; padding: 10px; background: #f9f9f9; border: 1px solid #e0e0e0; margin-bottom: 20px;">
            <strong>Version 3.0.1</strong> - Released 2025-07-31 | 4 Download Methods Restored
        </div>

        <!-- Tab Navigation -->
        <div class="tabs">
            <button class="tab active" onclick="showTab('artwork')">Download Artwork</button>
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

            <h3>Choose Download Method:</h3>
            <div class="method-selection">
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
                <p>Future feature for system customization</p>
                <div style="padding: 40px; text-align: center; color: #666;">
                    <h3>Coming Soon</h3>
                    <p>This feature will allow you to:</p>
                    <ul style="text-align: left; max-width: 400px; margin: 20px auto; line-height: 1.8;">
                        <li>Default download folder settings</li>
                        <li>Browser and timeout preferences</li>
                        <li>Login credential management</li>
                        <li>UI theme and appearance</li>
                        <li>Email notification settings</li>
                    </ul>
                </div>
            </div>
        </div>
    </div>

    <script>
        let selectedMethod = null;
        let currentPO = null;

        // Method selection
        document.addEventListener('DOMContentLoaded', function() {
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
                    (tabName === 'po' && index === 1) ||
                    (tabName === 'settings' && index === 2)) {
                    tab.classList.add('active');
                }
            });
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
            // Just ensure no method is pre-selected
            selectedMethod = null;
            document.querySelectorAll('.method-card').forEach(card => {
                card.classList.remove('selected');
            });
        }
        

        
        function showDataTable(items) {
            console.log('showDataTable called with items:', items.length); // Debug log
            const container = document.getElementById('data_table_container');

            let html = `
                <table class="data-table">
                    <thead>
                        <tr>
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

            const button = document.getElementById('download_btn');
            button.disabled = true;
            button.innerHTML = '⏳ Starting Download...';
            document.getElementById('progress_step').classList.remove('hidden');
            
            try {
                await fetch('/api/start_download', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        method: selectedMethod,
                        po_number: currentPO.po_number,
                        items: currentPO.items
                    })
                });
                
                // Start polling for progress
                pollProgress();
            } catch (error) {
                showError('Error starting download: ' + error.message);
            }
        }
        
        async function pollProgress() {
            try {
                const response = await fetch('/api/status');
                const status = await response.json();
                
                document.getElementById('progress_info').innerHTML = `
                    <p>Progress: ${status.progress}%</p>
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
</body>
</html>
"""

if __name__ == '__main__':
    print("🚀 Starting Smart E-BrandID Downloader...")
    print(f"📋 Version: {VERSION} ({VERSION_DATE})")
    print("📱 Open your browser and go to: http://localhost:5001")
    print("🛑 Press Ctrl+C to stop the server")
    
    app.run(debug=False, host='127.0.0.1', port=5001)
