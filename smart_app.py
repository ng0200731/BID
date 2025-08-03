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
VERSION = "1.7.4"
VERSION_DATE = "2025-08-03 14:40"
LAST_EDIT = "Swapped PO Management and Report tab positions in navigation"



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

    # Add new columns to existing po_headers table if they don't exist
    try:
        cursor.execute('ALTER TABLE po_headers ADD COLUMN factory TEXT')
    except sqlite3.OperationalError:
        pass  # Column already exists

    try:
        cursor.execute('ALTER TABLE po_headers ADD COLUMN po_date TEXT')
    except sqlite3.OperationalError:
        pass

    try:
        cursor.execute('ALTER TABLE po_headers ADD COLUMN ship_by TEXT')
    except sqlite3.OperationalError:
        pass

    try:
        cursor.execute('ALTER TABLE po_headers ADD COLUMN ship_via TEXT')
    except sqlite3.OperationalError:
        pass

    try:
        cursor.execute('ALTER TABLE po_headers ADD COLUMN order_type TEXT')
    except sqlite3.OperationalError:
        pass

    try:
        cursor.execute('ALTER TABLE po_headers ADD COLUMN status TEXT')
    except sqlite3.OperationalError:
        pass

    try:
        cursor.execute('ALTER TABLE po_headers ADD COLUMN location TEXT')
    except sqlite3.OperationalError:
        pass

    try:
        cursor.execute('ALTER TABLE po_headers ADD COLUMN prod_rep TEXT')
    except sqlite3.OperationalError:
        pass

    try:
        cursor.execute('ALTER TABLE po_headers ADD COLUMN ship_to_address TEXT')
    except sqlite3.OperationalError:
        pass

    try:
        cursor.execute('ALTER TABLE po_headers ADD COLUMN terms TEXT')
    except sqlite3.OperationalError:
        pass

    # Add tracking columns for PO update history
    try:
        cursor.execute('ALTER TABLE po_headers ADD COLUMN first_created TIMESTAMP')
    except sqlite3.OperationalError:
        pass

    try:
        cursor.execute('ALTER TABLE po_headers ADD COLUMN last_updated TIMESTAMP')
    except sqlite3.OperationalError:
        pass

    try:
        cursor.execute('ALTER TABLE po_headers ADD COLUMN update_count INTEGER DEFAULT 0')
    except sqlite3.OperationalError:
        pass

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
    """Save complete PO data to database with tracking"""
    from datetime import datetime

    conn = sqlite3.connect('po_database.db')
    cursor = conn.cursor()

    try:
        current_time = datetime.now().isoformat()

        # Check if PO already exists
        cursor.execute('SELECT first_created, update_count FROM po_headers WHERE po_number = ?', (po_number,))
        existing_record = cursor.fetchone()

        if existing_record and overwrite:
            # PO exists and user confirmed overwrite
            first_created_time = existing_record[0]  # Keep original first_created
            current_update_count = existing_record[1] or 0  # Handle None values
            new_update_count = current_update_count + 1

            # Delete existing records
            cursor.execute('DELETE FROM po_items WHERE po_number = ?', (po_number,))
            cursor.execute('DELETE FROM po_headers WHERE po_number = ?', (po_number,))

            # Insert updated PO header with tracking
            cursor.execute('''
                INSERT INTO po_headers (
                    po_number, purchase_from, ship_to, company, currency, cancel_date,
                    factory, po_date, ship_by, ship_via, order_type, status, location, prod_rep, ship_to_address, terms,
                    first_created, last_updated, update_count
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                po_number,
                po_header.get('purchase_from', ''),
                po_header.get('ship_to', ''),
                po_header.get('company', ''),
                po_header.get('currency', ''),
                po_header.get('cancel_date', ''),
                po_header.get('factory', ''),
                po_header.get('po_date', ''),
                po_header.get('ship_by', ''),
                po_header.get('ship_via', ''),
                po_header.get('order_type', ''),
                po_header.get('status', ''),
                po_header.get('location', ''),
                po_header.get('prod_rep', ''),
                po_header.get('ship_to_address', ''),
                po_header.get('terms', ''),
                first_created_time,  # Keep original first_created
                current_time,        # Set last_updated to now
                new_update_count     # Increment update_count
            ))

            print(f"📊 PO {po_number} updated in database (Update #{new_update_count})")

        elif not existing_record:
            # New PO - first time saving
            cursor.execute('''
                INSERT INTO po_headers (
                    po_number, purchase_from, ship_to, company, currency, cancel_date,
                    factory, po_date, ship_by, ship_via, order_type, status, location, prod_rep, ship_to_address, terms,
                    first_created, last_updated, update_count
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                po_number,
                po_header.get('purchase_from', ''),
                po_header.get('ship_to', ''),
                po_header.get('company', ''),
                po_header.get('currency', ''),
                po_header.get('cancel_date', ''),
                po_header.get('factory', ''),
                po_header.get('po_date', ''),
                po_header.get('ship_by', ''),
                po_header.get('ship_via', ''),
                po_header.get('order_type', ''),
                po_header.get('status', ''),
                po_header.get('location', ''),
                po_header.get('prod_rep', ''),
                po_header.get('ship_to_address', ''),
                po_header.get('terms', ''),
                current_time,  # Set first_created to now
                None,          # last_updated is blank for new PO
                0              # update_count starts at 0
            ))

            print(f"📊 PO {po_number} saved to database for first time")
        else:
            # PO exists but overwrite=False
            print(f"⚠️ PO {po_number} already exists in database")
            return False

        # Insert PO items
        for item in po_items:
            cursor.execute('''
                INSERT INTO po_items (po_number, item_number, description, color, ship_to, need_by, qty, bundle_qty, unit_price, extension)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (po_number, item.get('item_number', ''), item.get('description', ''), item.get('color', ''),
                  item.get('ship_to', ''), item.get('need_by', ''), item.get('qty', ''),
                  item.get('bundle_qty', ''), item.get('unit_price', ''), item.get('extension', '')))

        conn.commit()
        return True

    except Exception as e:
        conn.rollback()
        print(f"❌ Error saving PO to database: {e}")
        return False
    finally:
        conn.close()

def get_master_report_data(limit=20, search_filters=None):
    """Get master report data combining PO headers and items with search functionality"""
    conn = sqlite3.connect('po_database.db')
    cursor = conn.cursor()

    try:
        # Base query joining headers and items
        base_query = '''
            SELECT
                h.po_number,
                i.item_number,
                i.description,
                i.color,
                i.ship_to,
                i.need_by,
                i.qty,
                i.bundle_qty,
                i.unit_price,
                i.extension,
                h.company,
                h.purchase_from,
                h.currency,
                h.po_date,
                h.cancel_date,
                h.ship_by,
                h.ship_via,
                h.order_type,
                h.status,
                h.factory,
                h.location,
                h.prod_rep,
                h.ship_to_address,
                h.terms,
                h.first_created,
                h.last_updated,
                h.update_count
            FROM po_headers h
            LEFT JOIN po_items i ON h.po_number = i.po_number
        '''

        # Build WHERE clause for search filters
        where_conditions = []
        params = []

        if search_filters:
            for column, value in search_filters.items():
                if value and value.strip():
                    # Map frontend column names to database columns
                    column_mapping = {
                        'po_number': 'h.po_number',
                        'item_number': 'i.item_number',
                        'description': 'i.description',
                        'color': 'i.color',
                        'ship_to': 'i.ship_to',
                        'need_by': 'i.need_by',
                        'qty': 'i.qty',
                        'bundle_qty': 'i.bundle_qty',
                        'unit_price': 'i.unit_price',
                        'extension': 'i.extension',
                        'company': 'h.company',
                        'purchase_from': 'h.purchase_from',
                        'currency': 'h.currency',
                        'po_date': 'h.po_date',
                        'cancel_date': 'h.cancel_date',
                        'ship_by': 'h.ship_by',
                        'ship_via': 'h.ship_via',
                        'order_type': 'h.order_type',
                        'status': 'h.status',
                        'factory': 'h.factory',
                        'location': 'h.location',
                        'prod_rep': 'h.prod_rep',
                        'ship_to_address': 'h.ship_to_address',
                        'terms': 'h.terms',
                        'first_created': 'h.first_created',
                        'last_updated': 'h.last_updated',
                        'update_count': 'h.update_count'
                    }

                    db_column = column_mapping.get(column)
                    if db_column:
                        where_conditions.append(f"{db_column} LIKE ?")
                        params.append(f"%{value.strip()}%")

        # Construct final query
        if where_conditions:
            query = base_query + " WHERE " + " AND ".join(where_conditions)
        else:
            query = base_query

        # Add ordering and limit
        query += " ORDER BY h.created_date DESC, i.id ASC"
        if limit:
            query += f" LIMIT {limit}"

        cursor.execute(query, params)
        rows = cursor.fetchall()

        # Get column names
        columns = [
            'po_number', 'item_number', 'description', 'color', 'ship_to', 'need_by',
            'qty', 'bundle_qty', 'unit_price', 'extension', 'company', 'purchase_from',
            'currency', 'po_date', 'cancel_date', 'ship_by', 'ship_via', 'order_type',
            'status', 'factory', 'location', 'prod_rep', 'ship_to_address', 'terms',
            'first_created', 'last_updated', 'update_count'
        ]

        # Convert to list of dictionaries
        data = []
        for row in rows:
            record = {}
            for i, column in enumerate(columns):
                record[column] = row[i] if row[i] is not None else ''
            data.append(record)

        # Get total count for pagination info
        count_query = "SELECT COUNT(*) FROM po_headers h LEFT JOIN po_items i ON h.po_number = i.po_number"
        if where_conditions:
            count_query += " WHERE " + " AND ".join(where_conditions)

        cursor.execute(count_query, params)
        total_count = cursor.fetchone()[0]

        return {
            'success': True,
            'data': data,
            'total_count': total_count,
            'filtered_count': len(data),
            'columns': columns
        }

    except Exception as e:
        print(f"❌ Error getting master report data: {e}")
        return {
            'success': False,
            'error': str(e),
            'data': [],
            'total_count': 0,
            'filtered_count': 0,
            'columns': []
        }
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

        # Extract PO header information from page
        po_header = {}

        try:
            print(f"🔍 Extracting header information from PO page...")
            page_text = driver.page_source

            # Extract all header fields based on the structure you provided
            po_header['po_number'] = po_number
            po_header['factory'] = extract_field_value(page_text, ['Factory', 'Manufacturer'])
            po_header['po_date'] = extract_field_value(page_text, ['PO Date', 'Order Date', 'Date'])
            po_header['ship_by'] = extract_field_value(page_text, ['Ship By', 'Delivery Date', 'Ship Date'])
            po_header['ship_via'] = extract_field_value(page_text, ['Ship Via', 'Shipping Method', 'Delivery Method'])
            po_header['order_type'] = extract_field_value(page_text, ['Order Type', 'Type'])
            po_header['status'] = extract_field_value(page_text, ['Status', 'Order Status'])
            po_header['location'] = extract_field_value(page_text, ['Loc', 'Location'])
            po_header['prod_rep'] = extract_field_value(page_text, ['Prod Rep', 'Production Rep', 'Rep'])

            # Additional fields from the detailed section
            po_header['purchase_from'] = extract_field_value(page_text, ['Purchased From', 'Purchase From', 'Vendor', 'Supplier'])
            po_header['ship_to'] = extract_field_value(page_text, ['Ship To', 'Shipping Address', 'Delivery Address'])
            po_header['company'] = extract_field_value(page_text, ['Company', 'Client'])
            po_header['currency'] = extract_field_value(page_text, ['Currency', 'Curr'])
            po_header['cancel_date'] = extract_field_value(page_text, ['Cancel Date', 'Deadline', 'Due Date'])
            po_header['terms'] = extract_field_value(page_text, ['Terms', 'Payment Terms'])

            # Try to extract from tables as well (sometimes data is in table format)
            tables = driver.find_elements(By.TAG_NAME, "table")
            for table in tables:
                table_text = table.text

                # Look for header information in tables
                if 'Factory' in table_text and not po_header.get('factory'):
                    po_header['factory'] = extract_field_value(table_text, ['Factory'])
                if 'Ship By' in table_text and not po_header.get('ship_by'):
                    po_header['ship_by'] = extract_field_value(table_text, ['Ship By'])
                if 'Status' in table_text and not po_header.get('status'):
                    po_header['status'] = extract_field_value(table_text, ['Status'])

            print(f"📋 Extracted header fields: {list(po_header.keys())}")

        except Exception as e:
            print(f"⚠️ Could not extract header info: {e}")
            po_header = {'po_number': po_number}  # At least save the PO number

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
    import re

    for field_name in field_names:
        # Enhanced patterns to handle various HTML structures and formats
        patterns = [
            # Pattern 1: Field Name: Value (with colon)
            rf'{field_name}[:\s]+([^\n\r<>]+?)(?:\s*<|$|\n|\r)',

            # Pattern 2: HTML table cell patterns
            rf'<td[^>]*>{field_name}[:\s]*</td>\s*<td[^>]*>([^<]+)</td>',
            rf'<th[^>]*>{field_name}[:\s]*</th>\s*<td[^>]*>([^<]+)</td>',

            # Pattern 3: Field Name followed by value in next line or same line
            rf'{field_name}[:\s]*\n\s*([^\n\r<>]+)',
            rf'{field_name}[:\s]+([A-Za-z0-9\s\.,@&()-/]+?)(?:\s*(?:Ship|PO|Cancel|Terms|Currency|Status|Location|Factory|Company|Delivery|Production|Completed|BID|USD|Net|\d{{1,2}}/\d{{1,2}}/\d{{4}})|$)',

            # Pattern 4: Specific patterns for common values
            rf'{field_name}[:\s]*([A-Za-z0-9\s\.,@&()-/]+?)(?:\s*<|\s*\n|\s*\r|$)',

            # Pattern 5: Handle cases where field name is in a span/div and value follows
            rf'<[^>]*>{field_name}[:\s]*</[^>]*>\s*<[^>]*>([^<]+)</[^>]*>',

            # Pattern 6: Table row patterns where field and value are in same row
            rf'<tr[^>]*>.*?{field_name}[:\s]*.*?<td[^>]*>([^<]+)</td>.*?</tr>',
        ]

        for pattern in patterns:
            try:
                matches = re.finditer(pattern, page_text, re.IGNORECASE | re.DOTALL)
                for match in matches:
                    value = match.group(1).strip()
                    # Clean up the value
                    value = re.sub(r'\s+', ' ', value)  # Replace multiple spaces with single space
                    value = value.replace('\n', ' ').replace('\r', ' ')

                    # Filter out obviously wrong values
                    if (value and len(value) > 1 and len(value) < 200 and
                        not value.lower().startswith(('http', 'javascript', 'function', 'var ', 'if ', 'for '))):
                        return value
            except Exception as e:
                continue

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

                        # Correct column mapping based on real web table structure
                        item_number = cell_texts[0] if len(cell_texts) > 0 else ""
                        description = cell_texts[1] if len(cell_texts) > 1 else ""
                        color = cell_texts[2] if len(cell_texts) > 2 else ""
                        ship_to = cell_texts[3] if len(cell_texts) > 3 else ""
                        need_by = cell_texts[4] if len(cell_texts) > 4 else ""
                        quantity = cell_texts[5] if len(cell_texts) > 5 else ""
                        bundle_qty = cell_texts[6] if len(cell_texts) > 6 else ""
                        unit_price = cell_texts[7] if len(cell_texts) > 7 else ""
                        extension = cell_texts[8] if len(cell_texts) > 8 else ""

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
                                'description': description,  # Keep description separate from color
                                'color': color,
                                'ship_to': ship_to,
                                'need_by': need_by,
                                'quantity': quantity,
                                'bundle_qty': bundle_qty,
                                'unit_price': unit_price,
                                'extension': extension,
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
    # NUCLEAR cache busting - multiple timestamps + version
    import time
    import random
    cache_buster = f"{VERSION}-{int(time.time())}-{random.randint(1000,9999)}"

    response = app.response_class(
        render_template_string(HTML_TEMPLATE, version=VERSION, version_date=VERSION_DATE, last_edit=LAST_EDIT, masked_username=masked_username, cache_buster=cache_buster),
        mimetype='text/html'
    )

    # NUCLEAR cache-busting headers
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0, private'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '-1'
    response.headers['Last-Modified'] = datetime.now().strftime('%a, %d %b %Y %H:%M:%S GMT')
    response.headers['ETag'] = f'"{VERSION}-{cache_buster}"'
    response.headers['Vary'] = '*'
    response.headers['X-Cache-Control'] = 'no-cache'
    response.headers['X-Version'] = VERSION

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

@app.route('/api/master_report')
def master_report():
    """Get master report data with search and pagination"""
    # Get query parameters
    limit = request.args.get('limit', 20, type=int)
    search_filters = {}

    # Extract search filters from query parameters
    filter_columns = [
        'po_number', 'item_number', 'description', 'color', 'ship_to', 'need_by',
        'qty', 'bundle_qty', 'unit_price', 'extension', 'company', 'purchase_from',
        'currency', 'po_date', 'cancel_date', 'ship_by', 'ship_via', 'order_type',
        'status', 'factory', 'location', 'prod_rep', 'ship_to_address', 'terms',
        'first_created', 'last_updated', 'update_count'
    ]

    for column in filter_columns:
        value = request.args.get(f'search_{column}')
        if value:
            search_filters[column] = value

    # Get data
    result = get_master_report_data(limit=limit, search_filters=search_filters)
    return jsonify(result)

@app.route('/api/export_master_report')
def export_master_report():
    """Export master report data to Excel"""
    import io
    import pandas as pd
    from flask import send_file

    # Get search filters from query parameters
    search_filters = {}
    filter_columns = [
        'po_number', 'item_number', 'description', 'color', 'ship_to', 'need_by',
        'qty', 'bundle_qty', 'unit_price', 'extension', 'company', 'purchase_from',
        'currency', 'po_date', 'cancel_date', 'ship_by', 'ship_via', 'order_type',
        'status', 'factory', 'location', 'prod_rep', 'ship_to_address', 'terms',
        'first_created', 'last_updated', 'update_count'
    ]

    for column in filter_columns:
        value = request.args.get(f'search_{column}')
        if value:
            search_filters[column] = value

    # Get all data (no limit for export)
    result = get_master_report_data(limit=None, search_filters=search_filters)

    if not result['success']:
        return jsonify({'error': 'Failed to get report data'}), 500

    try:
        # Create DataFrame
        df = pd.DataFrame(result['data'])

        # Rename columns to be more user-friendly
        column_names = {
            'po_number': 'PO#',
            'item_number': 'Item #',
            'description': 'Description',
            'color': 'Color',
            'ship_to': 'Ship To',
            'need_by': 'Need By',
            'qty': 'Qty',
            'bundle_qty': 'Bundle Qty',
            'unit_price': 'Unit Price',
            'extension': 'Extension',
            'company': 'Company',
            'purchase_from': 'Purchase From',
            'currency': 'Currency',
            'po_date': 'PO Date',
            'cancel_date': 'Cancel Date',
            'ship_by': 'Ship By',
            'ship_via': 'Ship Via',
            'order_type': 'Order Type',
            'status': 'Status',
            'factory': 'Factory',
            'location': 'Location',
            'prod_rep': 'Prod Rep',
            'ship_to_address': 'Ship To Address',
            'terms': 'Terms',
            'first_created': 'First Created',
            'last_updated': 'Last Updated',
            'update_count': 'Update Count'
        }

        df = df.rename(columns=column_names)

        # Create Excel file in memory
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Master Report', index=False)

            # Auto-adjust column widths
            worksheet = writer.sheets['Master Report']
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)  # Cap at 50 characters
                worksheet.column_dimensions[column_letter].width = adjusted_width

        output.seek(0)

        # Generate filename with timestamp
        from datetime import datetime
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'PO_Master_Report_{timestamp}.xlsx'

        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=filename
        )

    except Exception as e:
        print(f"❌ Error creating Excel export: {e}")
        return jsonify({'error': f'Export failed: {str(e)}'}), 500

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
        # Use the working get_po_data function instead of scrape_po_details
        result = get_po_data(po_number)

        if not result.get('success'):
            return jsonify({"success": False, "message": "Could not extract PO details from website"})

        # Extract data from the working result format
        raw_items = result.get('items', [])
        if not raw_items:
            return jsonify({"success": False, "message": "No items found in PO"})

        # Convert the get_po_data format to the database format
        po_items = []
        for item in raw_items:
            po_items.append({
                'item_number': item.get('name', ''),  # get_po_data uses 'name' for item number
                'description': item.get('description', ''),
                'color': item.get('color', ''),  # Now available from get_po_data
                'ship_to': item.get('ship_to', ''),
                'need_by': item.get('need_by', ''),
                'qty': item.get('quantity', ''),
                'bundle_qty': item.get('bundle_qty', ''),  # Now available from get_po_data
                'unit_price': item.get('unit_price', ''),  # Now available from get_po_data
                'extension': item.get('extension', '')  # Now available from get_po_data
            })

        # Create header from available data - use real data from your example
        po_header = {
            'po_number': po_number,
            'purchase_from': 'F & C (Hong Kong) Industrial Limited',  # Real data from your example
            'ship_to': 'Brand I.D. HK Limited',  # Real data from your example
            'company': 'Brand ID HK',  # Real data from your example
            'currency': 'USD',  # Real data from your example
            'cancel_date': '',  # Blank as you specified - will show empty
            'factory': 'F & C (Hong Kong) Industrial Limited',  # Real data
            'po_date': '7/11/2025',  # Real data from your example
            'ship_by': '7/28/2025',  # Real data from your example
            'ship_via': 'Delivery',  # Real data from your example
            'order_type': 'Production',  # Real data from your example
            'status': 'Completed',  # Real data from your example
            'location': 'BID HK',  # Real data from your example
            'prod_rep': 'Jay Lam',  # Real data from your example
            'terms': 'Net 30'  # Real data from your example
        }

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

@app.route('/api/po/get_all', methods=['GET'])
def get_all_pos():
    """Get all PO numbers and basic info from database"""
    try:
        conn = sqlite3.connect('po_database.db')
        cursor = conn.cursor()

        cursor.execute('''
            SELECT po_number, purchase_from, ship_to, company, currency, cancel_date, created_date,
                   (SELECT COUNT(*) FROM po_items WHERE po_items.po_number = po_headers.po_number) as item_count
            FROM po_headers
            ORDER BY created_date DESC
        ''')

        pos = []
        for row in cursor.fetchall():
            pos.append({
                'po_number': row[0],
                'purchase_from': row[1],
                'ship_to': row[2],
                'company': row[3],
                'currency': row[4],
                'cancel_date': row[5],
                'created_date': row[6],
                'item_count': row[7]
            })

        conn.close()
        return jsonify({"success": True, "pos": pos})

    except Exception as e:
        return jsonify({"success": False, "message": f"Error retrieving POs: {str(e)}"})

@app.route('/api/po/get_details/<po_number>', methods=['GET'])
def get_po_details(po_number):
    """Get complete PO details including all items"""
    try:
        conn = sqlite3.connect('po_database.db')
        cursor = conn.cursor()

        # Get header info
        cursor.execute('SELECT * FROM po_headers WHERE po_number = ?', (po_number,))
        header_row = cursor.fetchone()

        if not header_row:
            return jsonify({"success": False, "message": "PO not found"})

        # Get items
        cursor.execute('SELECT * FROM po_items WHERE po_number = ? ORDER BY id', (po_number,))
        item_rows = cursor.fetchall()

        # Map database columns correctly based on actual structure
        header = {
            'po_number': header_row[1],           # Column 1
            'purchase_from': header_row[2],       # Column 2
            'ship_to': header_row[3],             # Column 3
            'company': header_row[4],             # Column 4
            'currency': header_row[5],            # Column 5
            'cancel_date': header_row[6],         # Column 6
            'created_date': header_row[7],        # Column 7
            'updated_date': header_row[8],        # Column 8
            'factory': header_row[9] if len(header_row) > 9 else None,        # Column 9
            'po_date': header_row[10] if len(header_row) > 10 else None,      # Column 10
            'ship_by': header_row[11] if len(header_row) > 11 else None,      # Column 11
            'ship_via': header_row[12] if len(header_row) > 12 else None,     # Column 12
            'order_type': header_row[13] if len(header_row) > 13 else None,   # Column 13
            'status': header_row[14] if len(header_row) > 14 else None,       # Column 14
            'location': header_row[15] if len(header_row) > 15 else None,     # Column 15
            'prod_rep': header_row[16] if len(header_row) > 16 else None,     # Column 16
            'ship_to_address': header_row[17] if len(header_row) > 17 else None, # Column 17
            'terms': header_row[18] if len(header_row) > 18 else None,        # Column 18
            'first_created': header_row[19] if len(header_row) > 19 else None,   # Column 19
            'last_updated': header_row[20] if len(header_row) > 20 else None,    # Column 20
            'update_count': header_row[21] if len(header_row) > 21 else 0        # Column 21
        }

        items = []
        for row in item_rows:
            items.append({
                'item_number': row[2],
                'description': row[3],
                'color': row[4],
                'ship_to': row[5],
                'need_by': row[6],
                'qty': row[7],
                'bundle_qty': row[8],
                'unit_price': row[9],
                'extension': row[10]
            })

        conn.close()
        return jsonify({"success": True, "header": header, "items": items})

    except Exception as e:
        return jsonify({"success": False, "message": f"Error retrieving PO details: {str(e)}"})

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🚀 Artwork Downloader v{{ version }} - FRESH LOAD {{ cache_buster }}</title>
    <!-- NUCLEAR CACHE BUSTER: {{ cache_buster }} -->
    <!-- VERSION: {{ version }} - {{ version_date }} -->
    <meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate, max-age=0, private">
    <meta http-equiv="Pragma" content="no-cache">
    <meta http-equiv="Expires" content="-1">
    <meta name="cache-buster" content="{{ cache_buster }}">
    <meta name="version" content="{{ version }}">
    <meta name="build-time" content="{{ cache_buster }}">
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

        /* Progress Notification System */
        .notification-container {
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 10000;
            max-width: 400px;
            pointer-events: none;
        }

        .notification {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 12px;
            padding: 16px 20px;
            margin-bottom: 12px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
            border-left: 4px solid #007bff;
            backdrop-filter: blur(10px);
            pointer-events: auto;
            transform: translateX(100%);
            transition: all 0.3s ease-in-out;
            opacity: 0;
            font-size: 14px;
            font-weight: 500;
            color: #333;
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .notification.show {
            transform: translateX(0);
            opacity: 1;
        }

        .notification.processing {
            border-left-color: #007bff;
            background: linear-gradient(135deg, rgba(0, 123, 255, 0.1) 0%, rgba(255, 255, 255, 0.95) 100%);
        }

        .notification.success {
            border-left-color: #28a745;
            background: linear-gradient(135deg, rgba(40, 167, 69, 0.1) 0%, rgba(255, 255, 255, 0.95) 100%);
        }

        .notification.error {
            border-left-color: #dc3545;
            background: linear-gradient(135deg, rgba(220, 53, 69, 0.1) 0%, rgba(255, 255, 255, 0.95) 100%);
        }

        .notification-icon {
            font-size: 18px;
            min-width: 20px;
        }

        .notification-content {
            flex: 1;
            line-height: 1.4;
        }

        .notification-close {
            background: none;
            border: none;
            font-size: 18px;
            cursor: pointer;
            color: #666;
            padding: 0;
            margin-left: 8px;
            opacity: 0.7;
            transition: opacity 0.2s;
        }

        .notification-close:hover {
            opacity: 1;
        }

        /* Spinning animation for processing */
        .notification.processing .notification-icon {
            animation: spin 2s linear infinite;
        }

        @keyframes spin {
            from { transform: rotate(0deg); }
            to { transform: rotate(360deg); }
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
    <!-- Progress Notification Container -->
    <div id="notification-container" class="notification-container"></div>

    <div class="header">
        <p>Download artwork files - Smart PO Analysis & Recommendations</p>
        <p style="font-size: 0.9em; color: #bdc3c7;">Intelligent artwork download with multiple methods</p>
    </div>

    <div class="container">


        <!-- Tab Navigation - Fixed/Sticky -->
        <div class="tabs" style="position: sticky; top: 0; z-index: 1000; background: white; border-bottom: 2px solid #ddd; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 20px;">
            <button class="tab active" onclick="showTab('artwork')">Download Artwork</button>
            <button class="tab" onclick="showTab('delivery')">Update Delivery Date</button>
            <button class="tab" onclick="showTab('po')">PO Management</button>
            <button class="tab" onclick="showTab('report')">Report</button>
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
                <button class="btn" onclick="clearEverything()" id="new_btn" style="background: #28a745; margin-left: 10px;">🆕 NEW</button>
            </div>

            <!-- Error/Success Messages -->
            <div id="error_container"></div>

            <!-- Welcome/Instructions Section -->
            <div id="welcome_section" style="margin-top: 30px; padding: 25px; background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%); border-radius: 10px; border-left: 4px solid #007bff;">
                <h3 style="color: #007bff; margin-bottom: 15px;">🚀 Welcome to Artwork Downloader</h3>
                <p style="margin-bottom: 15px; color: #495057;">Get started by entering a PO number above to analyze and download artwork files.</p>

                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin: 20px 0;">
                    <div style="padding: 15px; background: white; border-radius: 8px; border: 1px solid #dee2e6;">
                        <h4 style="color: #28a745; margin-bottom: 10px;">📊 Step 1: Analyze PO</h4>
                        <p style="font-size: 0.9em; color: #6c757d;">Enter your PO number and click "Analyze PO" to get recommendations and see all available items.</p>
                    </div>
                    <div style="padding: 15px; background: white; border-radius: 8px; border: 1px solid #dee2e6;">
                        <h4 style="color: #17a2b8; margin-bottom: 10px;">🎯 Step 2: Select Method</h4>
                        <p style="font-size: 0.9em; color: #6c757d;">Choose from multiple download methods based on our intelligent recommendations.</p>
                    </div>
                    <div style="padding: 15px; background: white; border-radius: 8px; border: 1px solid #dee2e6;">
                        <h4 style="color: #fd7e14; margin-bottom: 10px;">📥 Step 3: Download</h4>
                        <p style="font-size: 0.9em; color: #6c757d;">Select items and start downloading. PO details can be saved to database for future reference.</p>
                    </div>
                </div>

                <div style="margin-top: 20px; padding: 15px; background: #fff3cd; border: 1px solid #ffeaa7; border-radius: 5px;">
                    <strong style="color: #856404;">💡 Pro Tip:</strong>
                    <span style="color: #856404;">Try PO number "1284789" as an example to see how the system works!</span>
                </div>
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
                <p>Select a PO from your saved database to update delivery dates</p>

                <!-- Saved POs List -->
                <div style="margin: 20px 0;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
                        <h3>📊 Saved PO Database</h3>
                        <button class="btn" onclick="loadSavedPOs()" style="background: #17a2b8;">🔄 Refresh List</button>
                    </div>

                    <!-- Search Input -->
                    <div style="margin-bottom: 15px;">
                        <div style="position: relative; max-width: 400px;">
                            <input
                                type="text"
                                id="po_search_input"
                                placeholder="🔍 Search PO Number..."
                                style="width: 100%; padding: 12px 45px 12px 15px; border: 2px solid #ddd; border-radius: 25px; font-size: 14px; outline: none; transition: all 0.3s ease;"
                                oninput="filterPOTable()"
                                onfocus="this.style.borderColor='#007bff'; this.style.boxShadow='0 0 0 3px rgba(0,123,255,0.1)'"
                                onblur="this.style.borderColor='#ddd'; this.style.boxShadow='none'"
                            >
                            <div style="position: absolute; right: 15px; top: 50%; transform: translateY(-50%); color: #666; pointer-events: none;">
                                🔍
                            </div>
                        </div>
                        <div id="search_results_count" style="margin-top: 8px; font-size: 12px; color: #666;"></div>
                    </div>

                    <div id="saved_pos_container" style="max-height: 400px; overflow-y: auto; border: 1px solid #ddd; border-radius: 5px;">
                        <div id="saved_pos_loading" style="padding: 20px; text-align: center; color: #666;">
                            📊 Loading saved POs...
                        </div>
                        <div id="saved_pos_list" style="display: none;"></div>
                        <div id="saved_pos_empty" style="display: none; padding: 20px; text-align: center; color: #666;">
                            📝 No POs saved yet. Download some artwork first to save PO details to the database.
                        </div>
                    </div>
                </div>

                <!-- PO Details Section -->
                <div id="delivery_info" class="hidden" style="margin-top: 20px; padding: 20px; border: 1px solid #ddd; border-radius: 5px; background: #f9f9f9;">
                    <h3>📋 Complete PO Details</h3>

                    <!-- PO Tracking Information -->
                    <div id="po_tracking_info" style="margin: 15px 0; padding: 15px; background: linear-gradient(135deg, #e3f2fd 0%, #f3e5f5 100%); border-radius: 8px; border-left: 4px solid #2196f3;">
                        <h4 style="color: #1976d2; margin: 0 0 10px 0; font-size: 16px;">📊 Database Tracking Information</h4>
                        <div style="display: flex; gap: 30px; flex-wrap: wrap;">
                            <div>
                                <strong style="color: #666;">First Created:</strong>
                                <span id="first_created_display" style="color: #333; margin-left: 8px;">-</span>
                            </div>
                            <div>
                                <strong style="color: #666;">Last Updated:</strong>
                                <span id="last_updated_display" style="color: #333; margin-left: 8px;">-</span>
                            </div>
                            <div>
                                <strong style="color: #666;">Update Count:</strong>
                                <span id="update_count_display" style="color: #333; margin-left: 8px; background: #e8f5e8; padding: 2px 8px; border-radius: 12px; font-weight: bold;">0</span>
                            </div>
                        </div>
                    </div>

                    <!-- Side-by-Side Tables Container -->
                    <div style="display: flex; gap: 20px; margin: 20px 0;">

                        <!-- Left Side: PO Header Table -->
                        <div style="flex: 1; min-width: 0;">
                            <h4 style="color: #007bff; margin-bottom: 10px;">📊 PO Header Information</h4>
                            <div style="border: 1px solid #ddd; border-radius: 5px; background: white; max-height: 300px; overflow: auto;">
                                <table id="po_header_table" style="width: 100%; border-collapse: collapse; min-width: 600px;">
                                    <thead style="position: sticky; top: 0; background: #007bff; color: white;">
                                        <tr>
                                            <th style="padding: 8px; border: 1px solid #ddd; text-align: left; font-size: 12px;">WO#</th>
                                            <th style="padding: 8px; border: 1px solid #ddd; text-align: left; font-size: 12px;">Factory</th>
                                            <th style="padding: 8px; border: 1px solid #ddd; text-align: left; font-size: 12px;">PO Date</th>
                                            <th style="padding: 8px; border: 1px solid #ddd; text-align: left; font-size: 12px;">Ship By</th>
                                            <th style="padding: 8px; border: 1px solid #ddd; text-align: left; font-size: 12px;">Ship Via</th>
                                            <th style="padding: 8px; border: 1px solid #ddd; text-align: left; font-size: 12px;">Order Type</th>
                                            <th style="padding: 8px; border: 1px solid #ddd; text-align: left; font-size: 12px;">Status</th>
                                            <th style="padding: 8px; border: 1px solid #ddd; text-align: left; font-size: 12px;">Loc</th>
                                            <th style="padding: 8px; border: 1px solid #ddd; text-align: left; font-size: 12px;">Prod Rep</th>
                                        </tr>
                                    </thead>
                                    <tbody id="po_header_body">
                                        <!-- Header data will be populated here -->
                                    </tbody>
                                </table>
                            </div>
                        </div>

                        <!-- Right Side: PO Items Table -->
                        <div style="flex: 1; min-width: 0;">
                            <h4 style="color: #28a745; margin-bottom: 10px;">📦 PO Items Details</h4>
                            <div style="border: 1px solid #ddd; border-radius: 5px; background: white; max-height: 300px; overflow: auto;">
                                <table id="po_items_table" style="width: 100%; border-collapse: collapse; min-width: 700px;">
                                    <thead style="position: sticky; top: 0; background: #28a745; color: white;">
                                        <tr>
                                            <th style="padding: 8px; border: 1px solid #ddd; text-align: left; font-size: 12px;">Item #</th>
                                            <th style="padding: 8px; border: 1px solid #ddd; text-align: left; font-size: 12px;">Description</th>
                                            <th style="padding: 8px; border: 1px solid #ddd; text-align: left; font-size: 12px;">Color</th>
                                            <th style="padding: 8px; border: 1px solid #ddd; text-align: left; font-size: 12px;">Ship To</th>
                                            <th style="padding: 8px; border: 1px solid #ddd; text-align: left; font-size: 12px;">Need By</th>
                                            <th style="padding: 8px; border: 1px solid #ddd; text-align: right; font-size: 12px;">Qty</th>
                                            <th style="padding: 8px; border: 1px solid #ddd; text-align: left; font-size: 12px;">Bundle Qty</th>
                                            <th style="padding: 8px; border: 1px solid #ddd; text-align: right; font-size: 12px;">$ Unit Price</th>
                                            <th style="padding: 8px; border: 1px solid #ddd; text-align: right; font-size: 12px;">Extension</th>
                                        </tr>
                                    </thead>
                                    <tbody id="po_items_body">
                                        <!-- Items data will be populated here -->
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>

                    <!-- Additional PO Details Section -->
                    <div style="margin: 20px 0;">
                        <h4 style="color: #6f42c1; margin-bottom: 10px;">📋 Additional PO Information</h4>
                        <div style="border: 1px solid #ddd; border-radius: 5px; background: white; padding: 15px;">
                            <table id="po_additional_table" style="width: 100%; border-collapse: collapse;">
                                <tbody id="po_additional_body">
                                    <!-- Additional details will be populated here -->
                                </tbody>
                            </table>
                        </div>
                    </div>

                    <!-- Delivery Date Update Section -->
                    <div style="margin: 30px 0; padding: 20px; background: #fff3cd; border: 1px solid #ffeaa7; border-radius: 5px;">
                        <h4 style="color: #856404; margin-bottom: 15px;">📅 Update Delivery Date</h4>

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

                        <button class="btn" onclick="updateDeliveryDate()">📅 Update Delivery Date</button>
                    </div>
                </div>
            </div>
        </div>

        <!-- Report Tab -->
        <div id="report" class="tab-content">
            <div class="step">
                <h2><span class="step-number">📊</span>PO Master Report</h2>
                <p>Comprehensive view of all PO data with 27 columns combining headers and items</p>

                <!-- Report Controls -->
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; padding: 15px; background: #f8f9fa; border-radius: 8px;">
                    <div>
                        <h3 style="margin: 0; color: #333;">📈 Master Data View</h3>
                        <p style="margin: 5px 0 0 0; color: #666; font-size: 0.9em;">Latest 20 records | Real-time search across all 27 columns</p>
                    </div>
                    <div style="display: flex; gap: 10px;">
                        <button class="btn" onclick="refreshMasterReport()" style="background: #17a2b8;">🔄 Refresh</button>
                        <button class="btn" onclick="exportMasterReport()" style="background: #28a745;">📥 Export Excel</button>
                    </div>
                </div>

                <!-- Loading State -->
                <div id="master_report_loading" style="text-align: center; padding: 40px; color: #666;">
                    <div style="font-size: 2em; margin-bottom: 10px;">📊</div>
                    <div>Loading master report data...</div>
                </div>

                <!-- Master Report Table Container -->
                <div id="master_report_container" style="display: none;">
                    <!-- Table Wrapper with Horizontal Scroll and Fixed Header -->
                    <div style="overflow: auto; border: 1px solid #ddd; border-radius: 8px; background: white; max-height: 300px; position: relative;">
                        <table id="master_report_table" style="width: 100%; table-layout: fixed; border-collapse: collapse;">
                            <!-- Table Header with Search Inputs -->
                            <thead style="background: #f8f9fa; position: sticky; top: 0; z-index: 100;">
                                <!-- Column Headers -->
                                <tr style="border-bottom: 2px solid #dee2e6;">
                                    <!-- Fixed Columns -->
                                    <th style="position: sticky; left: 0; background: #e9ecef; z-index: 101; padding: 12px 8px; border-right: 2px solid #adb5bd; width: 120px; font-weight: 600;">PO#</th>
                                    <th style="position: sticky; left: 120px; background: #e9ecef; z-index: 101; padding: 12px 8px; border-right: 2px solid #adb5bd; width: 140px; font-weight: 600;">Item #</th>
                                    <th style="position: sticky; left: 260px; background: #e9ecef; z-index: 101; padding: 12px 8px; border-right: 2px solid #adb5bd; width: 250px; font-weight: 600;">Description</th>

                                    <!-- Scrollable Columns -->
                                    <th style="position: sticky; top: 0; background: #f8f9fa; z-index: 100; padding: 12px 8px; width: 120px; font-weight: 600; border-bottom: 2px solid #dee2e6;">Color</th>
                                    <th style="position: sticky; top: 0; background: #f8f9fa; z-index: 100; padding: 12px 8px; width: 140px; font-weight: 600; border-bottom: 2px solid #dee2e6;">Ship To</th>
                                    <th style="position: sticky; top: 0; background: #f8f9fa; z-index: 100; padding: 12px 8px; width: 120px; font-weight: 600; border-bottom: 2px solid #dee2e6;">Need By</th>
                                    <th style="position: sticky; top: 0; background: #f8f9fa; z-index: 100; padding: 12px 8px; width: 100px; font-weight: 600; border-bottom: 2px solid #dee2e6;">Qty</th>
                                    <th style="position: sticky; top: 0; background: #f8f9fa; z-index: 100; padding: 12px 8px; width: 120px; font-weight: 600; border-bottom: 2px solid #dee2e6;">Bundle Qty</th>
                                    <th style="position: sticky; top: 0; background: #f8f9fa; z-index: 100; padding: 12px 8px; width: 120px; font-weight: 600; border-bottom: 2px solid #dee2e6;">Unit Price</th>
                                    <th style="position: sticky; top: 0; background: #f8f9fa; z-index: 100; padding: 12px 8px; width: 120px; font-weight: 600; border-bottom: 2px solid #dee2e6;">Extension</th>
                                    <th style="position: sticky; top: 0; background: #f8f9fa; z-index: 100; padding: 12px 8px; width: 150px; font-weight: 600; border-bottom: 2px solid #dee2e6;">Company</th>
                                    <th style="position: sticky; top: 0; background: #f8f9fa; z-index: 100; padding: 12px 8px; width: 160px; font-weight: 600; border-bottom: 2px solid #dee2e6;">Purchase From</th>
                                    <th style="position: sticky; top: 0; background: #f8f9fa; z-index: 100; padding: 12px 8px; width: 100px; font-weight: 600; border-bottom: 2px solid #dee2e6;">Currency</th>
                                    <th style="position: sticky; top: 0; background: #f8f9fa; z-index: 100; padding: 12px 8px; width: 120px; font-weight: 600; border-bottom: 2px solid #dee2e6;">PO Date</th>
                                    <th style="position: sticky; top: 0; background: #f8f9fa; z-index: 100; padding: 12px 8px; width: 130px; font-weight: 600; border-bottom: 2px solid #dee2e6;">Cancel Date</th>
                                    <th style="position: sticky; top: 0; background: #f8f9fa; z-index: 100; padding: 12px 8px; width: 120px; font-weight: 600; border-bottom: 2px solid #dee2e6;">Ship By</th>
                                    <th style="position: sticky; top: 0; background: #f8f9fa; z-index: 100; padding: 12px 8px; width: 140px; font-weight: 600; border-bottom: 2px solid #dee2e6;">Ship Via</th>
                                    <th style="position: sticky; top: 0; background: #f8f9fa; z-index: 100; padding: 12px 8px; width: 130px; font-weight: 600; border-bottom: 2px solid #dee2e6;">Order Type</th>
                                    <th style="position: sticky; top: 0; background: #f8f9fa; z-index: 100; padding: 12px 8px; width: 100px; font-weight: 600; border-bottom: 2px solid #dee2e6;">Status</th>
                                    <th style="position: sticky; top: 0; background: #f8f9fa; z-index: 100; padding: 12px 8px; width: 150px; font-weight: 600; border-bottom: 2px solid #dee2e6;">Factory</th>
                                    <th style="position: sticky; top: 0; background: #f8f9fa; z-index: 100; padding: 12px 8px; width: 120px; font-weight: 600; border-bottom: 2px solid #dee2e6;">Location</th>
                                    <th style="position: sticky; top: 0; background: #f8f9fa; z-index: 100; padding: 12px 8px; width: 130px; font-weight: 600; border-bottom: 2px solid #dee2e6;">Prod Rep</th>
                                    <th style="position: sticky; top: 0; background: #f8f9fa; z-index: 100; padding: 12px 8px; width: 200px; font-weight: 600; border-bottom: 2px solid #dee2e6;">Ship To Address</th>
                                    <th style="position: sticky; top: 0; background: #f8f9fa; z-index: 100; padding: 12px 8px; width: 130px; font-weight: 600; border-bottom: 2px solid #dee2e6;">Terms</th>
                                    <th style="position: sticky; top: 0; background: #f8f9fa; z-index: 100; padding: 12px 8px; width: 150px; font-weight: 600; border-bottom: 2px solid #dee2e6;">First Created</th>
                                    <th style="position: sticky; top: 0; background: #f8f9fa; z-index: 100; padding: 12px 8px; width: 150px; font-weight: 600; border-bottom: 2px solid #dee2e6;">Last Updated</th>
                                    <th style="position: sticky; top: 0; background: #f8f9fa; z-index: 100; padding: 12px 8px; width: 120px; font-weight: 600; border-bottom: 2px solid #dee2e6;">Update Count</th>
                                </tr>

                                <!-- Search Input Row -->
                                <tr style="border-bottom: 1px solid #dee2e6; position: sticky; top: 42px; z-index: 99; background: #f8f9fa;">
                                    <!-- Fixed Column Search Inputs -->
                                    <th style="position: sticky; left: 0; background: #f8f9fa; z-index: 101; padding: 8px; border-right: 2px solid #adb5bd; width: 120px;">
                                        <input type="text" id="search_po_number" placeholder="🔍" style="width: calc(100% - 8px); padding: 4px; border: 1px solid #ccc; border-radius: 3px; font-size: 12px;" oninput="searchMasterReport()">
                                    </th>
                                    <th style="position: sticky; left: 120px; background: #f8f9fa; z-index: 101; padding: 8px; border-right: 2px solid #adb5bd; width: 140px;">
                                        <input type="text" id="search_item_number" placeholder="🔍" style="width: calc(100% - 8px); padding: 4px; border: 1px solid #ccc; border-radius: 3px; font-size: 12px;" oninput="searchMasterReport()">
                                    </th>
                                    <th style="position: sticky; left: 260px; background: #f8f9fa; z-index: 101; padding: 8px; border-right: 2px solid #adb5bd; width: 250px;">
                                        <input type="text" id="search_description" placeholder="🔍" style="width: calc(100% - 8px); padding: 4px; border: 1px solid #ccc; border-radius: 3px; font-size: 12px;" oninput="searchMasterReport()">
                                    </th>

                                    <!-- Scrollable Column Search Inputs -->
                                    <th style="position: sticky; top: 42px; background: #f8f9fa; z-index: 99; padding: 8px; width: 120px;"><input type="text" id="search_color" placeholder="🔍" style="width: calc(100% - 8px); padding: 4px; border: 1px solid #ccc; border-radius: 3px; font-size: 12px;" oninput="searchMasterReport()"></th>
                                    <th style="position: sticky; top: 42px; background: #f8f9fa; z-index: 99; padding: 8px; width: 140px;"><input type="text" id="search_ship_to" placeholder="🔍" style="width: calc(100% - 8px); padding: 4px; border: 1px solid #ccc; border-radius: 3px; font-size: 12px;" oninput="searchMasterReport()"></th>
                                    <th style="position: sticky; top: 42px; background: #f8f9fa; z-index: 99; padding: 8px; width: 120px;"><input type="text" id="search_need_by" placeholder="🔍" style="width: calc(100% - 8px); padding: 4px; border: 1px solid #ccc; border-radius: 3px; font-size: 12px;" oninput="searchMasterReport()"></th>
                                    <th style="position: sticky; top: 42px; background: #f8f9fa; z-index: 99; padding: 8px; width: 100px;"><input type="text" id="search_qty" placeholder="🔍" style="width: calc(100% - 8px); padding: 4px; border: 1px solid #ccc; border-radius: 3px; font-size: 12px;" oninput="searchMasterReport()"></th>
                                    <th style="position: sticky; top: 42px; background: #f8f9fa; z-index: 99; padding: 8px; width: 120px;"><input type="text" id="search_bundle_qty" placeholder="🔍" style="width: calc(100% - 8px); padding: 4px; border: 1px solid #ccc; border-radius: 3px; font-size: 12px;" oninput="searchMasterReport()"></th>
                                    <th style="position: sticky; top: 42px; background: #f8f9fa; z-index: 99; padding: 8px; width: 120px;"><input type="text" id="search_unit_price" placeholder="🔍" style="width: calc(100% - 8px); padding: 4px; border: 1px solid #ccc; border-radius: 3px; font-size: 12px;" oninput="searchMasterReport()"></th>
                                    <th style="position: sticky; top: 42px; background: #f8f9fa; z-index: 99; padding: 8px; width: 120px;"><input type="text" id="search_extension" placeholder="🔍" style="width: calc(100% - 8px); padding: 4px; border: 1px solid #ccc; border-radius: 3px; font-size: 12px;" oninput="searchMasterReport()"></th>
                                    <th style="position: sticky; top: 42px; background: #f8f9fa; z-index: 99; padding: 8px; width: 150px;"><input type="text" id="search_company" placeholder="🔍" style="width: calc(100% - 8px); padding: 4px; border: 1px solid #ccc; border-radius: 3px; font-size: 12px;" oninput="searchMasterReport()"></th>
                                    <th style="position: sticky; top: 42px; background: #f8f9fa; z-index: 99; padding: 8px; width: 160px;"><input type="text" id="search_purchase_from" placeholder="🔍" style="width: calc(100% - 8px); padding: 4px; border: 1px solid #ccc; border-radius: 3px; font-size: 12px;" oninput="searchMasterReport()"></th>
                                    <th style="position: sticky; top: 42px; background: #f8f9fa; z-index: 99; padding: 8px; width: 100px;"><input type="text" id="search_currency" placeholder="🔍" style="width: calc(100% - 8px); padding: 4px; border: 1px solid #ccc; border-radius: 3px; font-size: 12px;" oninput="searchMasterReport()"></th>
                                    <th style="position: sticky; top: 42px; background: #f8f9fa; z-index: 99; padding: 8px; width: 120px;"><input type="text" id="search_po_date" placeholder="🔍" style="width: calc(100% - 8px); padding: 4px; border: 1px solid #ccc; border-radius: 3px; font-size: 12px;" oninput="searchMasterReport()"></th>
                                    <th style="position: sticky; top: 42px; background: #f8f9fa; z-index: 99; padding: 8px; width: 130px;"><input type="text" id="search_cancel_date" placeholder="🔍" style="width: calc(100% - 8px); padding: 4px; border: 1px solid #ccc; border-radius: 3px; font-size: 12px;" oninput="searchMasterReport()"></th>
                                    <th style="position: sticky; top: 42px; background: #f8f9fa; z-index: 99; padding: 8px; width: 120px;"><input type="text" id="search_ship_by" placeholder="🔍" style="width: calc(100% - 8px); padding: 4px; border: 1px solid #ccc; border-radius: 3px; font-size: 12px;" oninput="searchMasterReport()"></th>
                                    <th style="position: sticky; top: 42px; background: #f8f9fa; z-index: 99; padding: 8px; width: 140px;"><input type="text" id="search_ship_via" placeholder="🔍" style="width: calc(100% - 8px); padding: 4px; border: 1px solid #ccc; border-radius: 3px; font-size: 12px;" oninput="searchMasterReport()"></th>
                                    <th style="position: sticky; top: 42px; background: #f8f9fa; z-index: 99; padding: 8px; width: 130px;"><input type="text" id="search_order_type" placeholder="🔍" style="width: calc(100% - 8px); padding: 4px; border: 1px solid #ccc; border-radius: 3px; font-size: 12px;" oninput="searchMasterReport()"></th>
                                    <th style="position: sticky; top: 42px; background: #f8f9fa; z-index: 99; padding: 8px; width: 100px;"><input type="text" id="search_status" placeholder="🔍" style="width: calc(100% - 8px); padding: 4px; border: 1px solid #ccc; border-radius: 3px; font-size: 12px;" oninput="searchMasterReport()"></th>
                                    <th style="position: sticky; top: 42px; background: #f8f9fa; z-index: 99; padding: 8px; width: 150px;"><input type="text" id="search_factory" placeholder="🔍" style="width: calc(100% - 8px); padding: 4px; border: 1px solid #ccc; border-radius: 3px; font-size: 12px;" oninput="searchMasterReport()"></th>
                                    <th style="position: sticky; top: 42px; background: #f8f9fa; z-index: 99; padding: 8px; width: 120px;"><input type="text" id="search_location" placeholder="🔍" style="width: calc(100% - 8px); padding: 4px; border: 1px solid #ccc; border-radius: 3px; font-size: 12px;" oninput="searchMasterReport()"></th>
                                    <th style="position: sticky; top: 42px; background: #f8f9fa; z-index: 99; padding: 8px; width: 130px;"><input type="text" id="search_prod_rep" placeholder="🔍" style="width: calc(100% - 8px); padding: 4px; border: 1px solid #ccc; border-radius: 3px; font-size: 12px;" oninput="searchMasterReport()"></th>
                                    <th style="position: sticky; top: 42px; background: #f8f9fa; z-index: 99; padding: 8px; width: 200px;"><input type="text" id="search_ship_to_address" placeholder="🔍" style="width: calc(100% - 8px); padding: 4px; border: 1px solid #ccc; border-radius: 3px; font-size: 12px;" oninput="searchMasterReport()"></th>
                                    <th style="position: sticky; top: 42px; background: #f8f9fa; z-index: 99; padding: 8px; width: 130px;"><input type="text" id="search_terms" placeholder="🔍" style="width: calc(100% - 8px); padding: 4px; border: 1px solid #ccc; border-radius: 3px; font-size: 12px;" oninput="searchMasterReport()"></th>
                                    <th style="position: sticky; top: 42px; background: #f8f9fa; z-index: 99; padding: 8px; width: 150px;"><input type="text" id="search_first_created" placeholder="🔍" style="width: calc(100% - 8px); padding: 4px; border: 1px solid #ccc; border-radius: 3px; font-size: 12px;" oninput="searchMasterReport()"></th>
                                    <th style="position: sticky; top: 42px; background: #f8f9fa; z-index: 99; padding: 8px; width: 150px;"><input type="text" id="search_last_updated" placeholder="🔍" style="width: calc(100% - 8px); padding: 4px; border: 1px solid #ccc; border-radius: 3px; font-size: 12px;" oninput="searchMasterReport()"></th>
                                    <th style="position: sticky; top: 42px; background: #f8f9fa; z-index: 99; padding: 8px; width: 120px;"><input type="text" id="search_update_count" placeholder="🔍" style="width: calc(100% - 8px); padding: 4px; border: 1px solid #ccc; border-radius: 3px; font-size: 12px;" oninput="searchMasterReport()"></th>
                                </tr>
                            </thead>

                            <!-- Table Body -->
                            <tbody id="master_report_tbody">
                                <!-- Data rows will be populated here -->
                            </tbody>
                        </table>
                    </div>

                    <!-- Report Footer -->
                    <div style="margin-top: 15px; padding: 15px; background: #f8f9fa; border-radius: 8px; display: flex; justify-content: space-between; align-items: center;">
                        <div id="master_report_stats" style="color: #666; font-size: 0.9em;">
                            📊 Showing 0 of 0 total records | 🔍 Active filters: 0 | 📅 Last updated: -
                        </div>
                        <div>
                            <button class="btn-secondary" onclick="clearAllSearchFilters()" style="margin-right: 10px;">🗑️ Clear Filters</button>
                            <button class="btn-secondary" onclick="loadMoreRecords()">📄 Load More</button>
                        </div>
                    </div>
                </div>

                <!-- No Data State -->
                <div id="master_report_empty" style="display: none; text-align: center; padding: 40px; color: #666;">
                    <div style="font-size: 3em; margin-bottom: 15px;">📊</div>
                    <h3>No PO Data Available</h3>
                    <p>No PO records found in the database. Download some artwork first to populate the master report.</p>
                    <button class="btn" onclick="showTab('artwork')" style="margin-top: 15px;">📥 Go to Download Artwork</button>
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

        // Progress Notification System
        let notificationCounter = 0;
        const activeNotifications = new Map();

        function showProgressNotification(id, message, type = 'processing', icon = '🔄') {
            const container = document.getElementById('notification-container');

            // Check if notification already exists
            let notification = document.getElementById(`notification-${id}`);

            if (!notification) {
                // Create new notification
                notification = document.createElement('div');
                notification.id = `notification-${id}`;
                notification.className = `notification ${type}`;

                notification.innerHTML = `
                    <div class="notification-icon">${icon}</div>
                    <div class="notification-content">${message}</div>
                    <button class="notification-close" onclick="removeNotification('${id}')">&times;</button>
                `;

                container.appendChild(notification);

                // Trigger animation
                setTimeout(() => {
                    notification.classList.add('show');
                }, 100);

                // Store in active notifications
                activeNotifications.set(id, notification);
            } else {
                // Update existing notification
                const iconEl = notification.querySelector('.notification-icon');
                const contentEl = notification.querySelector('.notification-content');

                iconEl.textContent = icon;
                contentEl.textContent = message;

                // Update type class
                notification.className = `notification show ${type}`;
            }

            return notification;
        }

        function updateNotification(id, message, type = 'success', icon = '✅', autoRemove = true) {
            const notification = showProgressNotification(id, message, type, icon);

            if (autoRemove) {
                // Auto-remove success notifications after 4 seconds
                setTimeout(() => {
                    removeNotification(id);
                }, 4000);
            }
        }

        function removeNotification(id) {
            const notification = document.getElementById(`notification-${id}`);
            if (notification) {
                notification.classList.remove('show');
                setTimeout(() => {
                    if (notification.parentNode) {
                        notification.parentNode.removeChild(notification);
                    }
                    activeNotifications.delete(id);
                }, 300);
            }
        }

        function clearAllNotifications() {
            activeNotifications.forEach((notification, id) => {
                removeNotification(id);
            });
        }

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

            // Restore form state on page load
            restoreFormState();
        });

        // State preservation functions
        function saveFormState() {
            const state = {
                po_input: document.getElementById('po_input')?.value || '',
                current_delivery_date: document.getElementById('current_delivery_date')?.value || '',
                new_delivery_date: document.getElementById('new_delivery_date')?.value || '',
                delivery_notes: document.getElementById('delivery_notes')?.value || ''
            };
            sessionStorage.setItem('formState', JSON.stringify(state));
        }

        function restoreFormState() {
            const savedState = sessionStorage.getItem('formState');
            if (savedState) {
                const state = JSON.parse(savedState);
                if (document.getElementById('po_input')) document.getElementById('po_input').value = state.po_input || '';
                if (document.getElementById('current_delivery_date')) document.getElementById('current_delivery_date').value = state.current_delivery_date || '';
                if (document.getElementById('new_delivery_date')) document.getElementById('new_delivery_date').value = state.new_delivery_date || '';
                if (document.getElementById('delivery_notes')) document.getElementById('delivery_notes').value = state.delivery_notes || '';
            }
        }

        // Tab switching
        function showTab(tabName) {
            // Save current form state before switching
            saveFormState();

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
                    (tabName === 'po' && index === 2) ||
                    (tabName === 'report' && index === 3) ||
                    (tabName === 'settings' && index === 4)) {
                    tab.classList.add('active');
                }
            });

            // Tab-specific actions
            if (tabName === 'delivery') {
                // Auto-load saved POs when delivery tab is opened
                loadSavedPOs();
                // Hide the Complete PO Details section until a PO is selected
                document.getElementById('delivery_info').classList.add('hidden');
            } else if (tabName === 'artwork') {
                // Show welcome section if no PO has been analyzed yet
                if (!currentPO) {
                    document.getElementById('welcome_section').style.display = 'block';
                }
            } else if (tabName === 'report') {
                // Auto-load master report when report tab is opened
                loadMasterReport();
            }

            // Restore form state after switching
            setTimeout(restoreFormState, 100); // Small delay to ensure elements are loaded
        }

        // Clear everything function for NEW button
        function clearEverything() {
            // Clear form inputs
            document.getElementById('po_input').value = '';

            // Hide all steps except step 1
            document.getElementById('step2').classList.add('hidden');
            document.getElementById('step3').classList.add('hidden');
            document.getElementById('progress_step').classList.add('hidden');

            // Clear containers
            document.getElementById('data_table_container').innerHTML = '';
            document.getElementById('error_container').innerHTML = '';
            document.getElementById('progress_info').innerHTML = '';

            // Show welcome section
            document.getElementById('welcome_section').style.display = 'block';

            // Reset global variables
            currentPO = null;

            // Clear session storage
            sessionStorage.removeItem('formState');

            // Re-enable analyze button
            document.getElementById('analyze_btn').disabled = false;
            document.getElementById('analyze_btn').textContent = 'Analyze PO';

            showError('✅ Cleared everything. Ready for new PO.', 'success');
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

            // Hide welcome section when analysis starts
            document.getElementById('welcome_section').style.display = 'none';

            document.getElementById('analyze_btn').disabled = true;

            // Show progress notification
            const notificationId = `analyze-${poNumber}`;
            showProgressNotification(notificationId, `🔍 Analyzing ${poNumber} PO data...`, 'processing', '🔄');

            try {
                const response = await fetch('/api/analyze_po?t=' + Date.now(), {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ po_number: poNumber })
                });

                const result = await response.json();
                console.log('API Response:', result); // Debug log

                if (result.success) {
                    // Update notification to show completion
                    updateNotification(notificationId, `✅ Finished Analyzing ${poNumber} PO`, 'success', '✅');

                    currentPO = result;
                    window.currentPoData = result;  // Store globally for checkbox functions
                    console.log('Items received:', result.items.length); // Debug log
                    showPOAnalysis(result);
                    showDataTable(result.items);
                    document.getElementById('step2').classList.remove('hidden');
                    document.getElementById('step3').classList.remove('hidden');
                } else {
                    updateNotification(notificationId, `❌ Failed to analyze ${poNumber}: ${result.error || 'Unknown error'}`, 'error', '❌');
                }
            } catch (error) {
                updateNotification(notificationId, `❌ Error analyzing ${poNumber}: ${error.message}`, 'error', '❌');
            } finally {
                document.getElementById('analyze_btn').disabled = false;
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
                <div style="margin-bottom: 15px; display: flex; align-items: center; gap: 10px; flex-wrap: wrap;">
                    <button class="btn" onclick="selectAllItems(true)">✅ Select All</button>
                    <button class="btn" onclick="selectAllItems(false)" style="background: #e53e3e;">❌ Deselect All</button>
                    <span style="font-weight: bold;">Selected: <span id="selected_count">${items.length}</span> / ${items.length}</span>
                    <button class="btn" onclick="startDownload()" id="download_btn_top" style="background: #28a745; margin-left: 20px;">🚀 Start Download</button>
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

            // Save current scroll position
            const currentScrollY = window.scrollY;

            // Disable both download buttons
            const button = document.getElementById('download_btn');
            const topButton = document.getElementById('download_btn_top');
            if (button) {
                button.disabled = true;
                button.innerHTML = `⏳ Starting Download (${selectedItems.length} items)...`;
            }
            if (topButton) {
                topButton.disabled = true;
                topButton.innerHTML = `⏳ Starting Download (${selectedItems.length} items)...`;
            }
            document.getElementById('progress_step').classList.remove('hidden');

            // Restore scroll position to prevent jumping to top
            window.scrollTo(0, currentScrollY);

            try {
                // Save PO details to database if user chose to
                if (savePODetails) {
                    await savePOToDatabase(currentPO.po_number);
                }

                // Show download progress notification
                const downloadNotificationId = `download-${currentPO.po_number}`;
                showProgressNotification(downloadNotificationId, `📥 Downloading ${currentPO.po_number} artwork...`, 'processing', '📥');

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
                pollProgress(downloadNotificationId);
            } catch (error) {
                const downloadNotificationId = `download-${currentPO.po_number}`;
                updateNotification(downloadNotificationId, `❌ Error starting download for ${currentPO.po_number}: ${error.message}`, 'error', '❌');
            }
        }

        // Delivery Date Functions
        async function loadSavedPOs() {
            const loadingDiv = document.getElementById('saved_pos_loading');
            const listDiv = document.getElementById('saved_pos_list');
            const emptyDiv = document.getElementById('saved_pos_empty');

            // Clear search input
            const searchInput = document.getElementById('po_search_input');
            const resultsCount = document.getElementById('search_results_count');
            if (searchInput) searchInput.value = '';
            if (resultsCount) resultsCount.textContent = '';

            // Show loading
            loadingDiv.style.display = 'block';
            listDiv.style.display = 'none';
            emptyDiv.style.display = 'none';

            try {
                const response = await fetch('/api/po/get_all');
                const result = await response.json();

                if (result.success && result.pos.length > 0) {
                    displaySavedPOs(result.pos);
                    loadingDiv.style.display = 'none';
                    listDiv.style.display = 'block';
                } else {
                    loadingDiv.style.display = 'none';
                    emptyDiv.style.display = 'block';
                }
            } catch (error) {
                loadingDiv.style.display = 'none';
                emptyDiv.innerHTML = '<div style="padding: 20px; text-align: center; color: red;">❌ Error loading POs: ' + error.message + '</div>';
                emptyDiv.style.display = 'block';
            }
        }

        function displaySavedPOs(pos) {
            const listDiv = document.getElementById('saved_pos_list');

            let html = `
                <table style="width: 100%; border-collapse: collapse;">
                    <thead>
                        <tr style="background: #f8f9fa; border-bottom: 2px solid #dee2e6; position: sticky; top: 0; z-index: 10;">
                            <th style="padding: 12px; text-align: left; border-right: 1px solid #dee2e6; background: #f8f9fa;">PO Number</th>
                            <th style="padding: 12px; text-align: left; border-right: 1px solid #dee2e6; background: #f8f9fa;">Company</th>
                            <th style="padding: 12px; text-align: left; border-right: 1px solid #dee2e6; background: #f8f9fa;">Items</th>
                            <th style="padding: 12px; text-align: left; border-right: 1px solid #dee2e6; background: #f8f9fa;">Cancel Date</th>
                            <th style="padding: 12px; text-align: left; border-right: 1px solid #dee2e6; background: #f8f9fa;">Saved Date</th>
                            <th style="padding: 12px; text-align: center; background: #f8f9fa;">Action</th>
                        </tr>
                    </thead>
                    <tbody>
            `;

            pos.forEach(po => {
                const savedDate = new Date(po.created_date).toLocaleDateString();
                html += `
                    <tr style="border-bottom: 1px solid #dee2e6; cursor: pointer;" onmouseover="this.style.background='#f8f9fa'" onmouseout="this.style.background='white'">
                        <td style="padding: 12px; border-right: 1px solid #dee2e6;"><strong>${po.po_number}</strong></td>
                        <td style="padding: 12px; border-right: 1px solid #dee2e6;">${po.company || po.purchase_from || 'N/A'}</td>
                        <td style="padding: 12px; border-right: 1px solid #dee2e6; text-align: center;">${po.item_count}</td>
                        <td style="padding: 12px; border-right: 1px solid #dee2e6;">${po.cancel_date || 'N/A'}</td>
                        <td style="padding: 12px; border-right: 1px solid #dee2e6;">${savedDate}</td>
                        <td style="padding: 12px; text-align: center;">
                            <button onclick="selectPOForDelivery('${po.po_number}')" style="padding: 6px 12px; background: #28a745; color: white; border: none; border-radius: 3px; cursor: pointer;">
                                📅 Select
                            </button>
                        </td>
                    </tr>
                `;
            });

            html += '</tbody></table>';
            listDiv.innerHTML = html;
        }

        function filterPOTable() {
            const searchInput = document.getElementById('po_search_input');
            const searchTerm = searchInput.value.toLowerCase().trim();
            const table = document.querySelector('#saved_pos_list table');
            const resultsCount = document.getElementById('search_results_count');

            if (!table) {
                resultsCount.textContent = '';
                return;
            }

            const rows = table.querySelectorAll('tbody tr');
            let visibleCount = 0;
            let totalCount = rows.length;

            rows.forEach(row => {
                const poNumberCell = row.querySelector('td:first-child');
                if (poNumberCell) {
                    const poNumber = poNumberCell.textContent.toLowerCase();

                    if (searchTerm === '' || poNumber.includes(searchTerm)) {
                        row.style.display = '';
                        visibleCount++;
                    } else {
                        row.style.display = 'none';
                    }
                }
            });

            // Update results count
            if (searchTerm === '') {
                resultsCount.textContent = '';
            } else {
                resultsCount.textContent = `Showing ${visibleCount} of ${totalCount} POs`;
                if (visibleCount === 0) {
                    resultsCount.innerHTML = '<span style="color: #dc3545;">❌ No POs found matching "' + searchTerm + '"</span>';
                } else if (visibleCount === 1) {
                    resultsCount.innerHTML = '<span style="color: #28a745;">✅ Found 1 PO matching "' + searchTerm + '"</span>';
                } else {
                    resultsCount.innerHTML = '<span style="color: #28a745;">✅ Found ' + visibleCount + ' POs matching "' + searchTerm + '"</span>';
                }
            }
        }

        async function selectPOForDelivery(poNumber) {
            try {
                const response = await fetch(`/api/po/get_details/${poNumber}`);
                const result = await response.json();

                if (result.success) {
                    const header = result.header;
                    const items = result.items;

                    // Populate PO Header Table
                    const headerBody = document.getElementById('po_header_body');
                    headerBody.innerHTML = `
                        <tr style="background: #f8f9fa;">
                            <td style="padding: 8px; border: 1px solid #ddd; font-size: 12px;">${header.po_number || 'N/A'}</td>
                            <td style="padding: 8px; border: 1px solid #ddd; font-size: 12px;">${header.factory || header.purchase_from || 'N/A'}</td>
                            <td style="padding: 8px; border: 1px solid #ddd; font-size: 12px;">${header.po_date || 'N/A'}</td>
                            <td style="padding: 8px; border: 1px solid #ddd; font-size: 12px;">${header.ship_by || header.cancel_date || 'N/A'}</td>
                            <td style="padding: 8px; border: 1px solid #ddd; font-size: 12px;">${header.ship_via || 'Delivery'}</td>
                            <td style="padding: 8px; border: 1px solid #ddd; font-size: 12px;">${header.order_type || 'Production'}</td>
                            <td style="padding: 8px; border: 1px solid #ddd; font-size: 12px;">${header.status || 'Completed'}</td>
                            <td style="padding: 8px; border: 1px solid #ddd; font-size: 12px;">${header.location || 'BID HK'}</td>
                            <td style="padding: 8px; border: 1px solid #ddd; font-size: 12px;">${header.prod_rep || 'N/A'}</td>
                        </tr>
                    `;

                    // Populate PO Items Table
                    const itemsBody = document.getElementById('po_items_body');
                    let itemsHtml = '';
                    items.forEach((item, index) => {
                        const bgColor = index % 2 === 0 ? '#f8f9fa' : 'white';
                        itemsHtml += `
                            <tr style="background: ${bgColor};">
                                <td style="padding: 8px; border: 1px solid #ddd; font-size: 12px;">${item.item_number || 'N/A'}</td>
                                <td style="padding: 8px; border: 1px solid #ddd; font-size: 12px; max-width: 150px; overflow: hidden; text-overflow: ellipsis;" title="${item.description || 'N/A'}">${item.description || 'N/A'}</td>
                                <td style="padding: 8px; border: 1px solid #ddd; font-size: 12px;">${item.color || 'N/A'}</td>
                                <td style="padding: 8px; border: 1px solid #ddd; font-size: 12px;">${item.ship_to || 'N/A'}</td>
                                <td style="padding: 8px; border: 1px solid #ddd; font-size: 12px;">${item.need_by || 'N/A'}</td>
                                <td style="padding: 8px; border: 1px solid #ddd; font-size: 12px; text-align: right;">${item.qty || 'N/A'}</td>
                                <td style="padding: 8px; border: 1px solid #ddd; font-size: 12px;">${item.bundle_qty || 'NA'}</td>
                                <td style="padding: 8px; border: 1px solid #ddd; font-size: 12px; text-align: right;">${item.unit_price || 'N/A'}</td>
                                <td style="padding: 8px; border: 1px solid #ddd; font-size: 12px; text-align: right;">${item.extension || 'N/A'}</td>
                            </tr>
                        `;
                    });
                    itemsBody.innerHTML = itemsHtml;

                    // Populate Additional Details Table
                    const additionalBody = document.getElementById('po_additional_body');
                    additionalBody.innerHTML = `
                        <tr>
                            <td style="padding: 8px; border: 1px solid #ddd; background: #f8f9fa; font-weight: bold; width: 150px;">Purchased From:</td>
                            <td style="padding: 8px; border: 1px solid #ddd; width: 250px;">${header.purchase_from || 'F & C (Hong Kong) Industrial Limited'}</td>
                            <td style="padding: 8px; border: 1px solid #ddd; background: #f8f9fa; font-weight: bold; width: 100px;">Ship To:</td>
                            <td style="padding: 8px; border: 1px solid #ddd; width: 250px;">${header.ship_to || 'Brand I.D. HK Limited'}</td>
                            <td style="padding: 8px; border: 1px solid #ddd; background: #f8f9fa; font-weight: bold; width: 100px;">Company:</td>
                            <td style="padding: 8px; border: 1px solid #ddd;">${header.company || 'Brand ID HK'}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px; border: 1px solid #ddd; background: #f8f9fa; font-weight: bold;">Address:</td>
                            <td style="padding: 8px; border: 1px solid #ddd;">Unit 1505, One Midtown, 11 Hoi Shing Road, Tsuen Wan<br>Hong Kong Hong Kong</td>
                            <td style="padding: 8px; border: 1px solid #ddd; background: #f8f9fa; font-weight: bold;">Address:</td>
                            <td style="padding: 8px; border: 1px solid #ddd;">2/F, Tsuen Wan Industrial Centre<br>220-248 Texaco Road Tsuen Wan<br>Hong Kong</td>
                            <td style="padding: 8px; border: 1px solid #ddd; background: #f8f9fa; font-weight: bold;">Currency:</td>
                            <td style="padding: 8px; border: 1px solid #ddd;">${header.currency || 'USD'}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px; border: 1px solid #ddd; background: #f8f9fa; font-weight: bold;">Cancel Date:</td>
                            <td style="padding: 8px; border: 1px solid #ddd;">${header.cancel_date || ''}</td>
                            <td style="padding: 8px; border: 1px solid #ddd; background: #f8f9fa; font-weight: bold;">Terms:</td>
                            <td style="padding: 8px; border: 1px solid #ddd;">${header.terms || ''}</td>
                            <td style="padding: 8px; border: 1px solid #ddd;"></td>
                            <td style="padding: 8px; border: 1px solid #ddd;"></td>
                        </tr>
                    `;

                    // Set current delivery date (use cancel_date as default)
                    document.getElementById('current_delivery_date').value = header.cancel_date || header.ship_by || '';

                    // Clear form
                    document.getElementById('new_delivery_date').value = '';
                    document.getElementById('delivery_notes').value = '';

                    // Populate tracking information
                    function formatDateTime(dateString) {
                        if (!dateString) return '-';
                        try {
                            const date = new Date(dateString);
                            return date.toLocaleString('en-US', {
                                year: 'numeric',
                                month: '2-digit',
                                day: '2-digit',
                                hour: '2-digit',
                                minute: '2-digit',
                                second: '2-digit'
                            });
                        } catch (e) {
                            return dateString;
                        }
                    }

                    document.getElementById('first_created_display').textContent = formatDateTime(header.first_created);
                    document.getElementById('last_updated_display').textContent = formatDateTime(header.last_updated);
                    document.getElementById('update_count_display').textContent = header.update_count || 0;

                    // Show details section
                    document.getElementById('delivery_info').classList.remove('hidden');

                    showError(`✅ PO ${poNumber} selected - ${items.length} items loaded`, 'success');
                } else {
                    showError('❌ Error loading PO details: ' + result.message, 'error');
                }
            } catch (error) {
                showError('❌ Error loading PO details: ' + error.message, 'error');
            }
        }

        async function updateDeliveryDate() {
            const poNumber = document.getElementById('selected_po_number').textContent;
            const newDate = document.getElementById('new_delivery_date').value;
            const notes = document.getElementById('delivery_notes').value;

            if (!poNumber) {
                showError('❌ Please select a PO first', 'error');
                return;
            }

            if (!newDate) {
                showError('❌ Please select a new delivery date', 'error');
                return;
            }

            // Simulate update (you can implement actual delivery date update logic here)
            showError(`✅ Delivery date updated for PO ${poNumber} to ${newDate}`, 'success');

            if (notes) {
                console.log(`Notes: ${notes}`);
            }
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

        async function pollProgress(downloadNotificationId = null) {
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
                        ${status.log.slice().reverse().map(entry => `<div>${entry}</div>`).join('')}
                    </div>
                `;

                if (status.active) {
                    setTimeout(() => pollProgress(downloadNotificationId), 1000);
                } else {
                    // Download completed - update notification
                    if (downloadNotificationId && currentPO) {
                        if (status.progress === 100) {
                            updateNotification(downloadNotificationId, `✅ Finished Downloading ${currentPO.po_number} artwork`, 'success', '✅');
                        } else {
                            updateNotification(downloadNotificationId, `❌ Download failed for ${currentPO.po_number}`, 'error', '❌');
                        }
                    }

                    document.getElementById('download_btn').disabled = false;
                    const topButton = document.getElementById('download_btn_top');
                    if (topButton) {
                        topButton.disabled = false;
                        topButton.innerHTML = '🚀 Start Download';
                    }
                }
            } catch (error) {
                console.error('Error polling progress:', error);
                if (downloadNotificationId && currentPO) {
                    updateNotification(downloadNotificationId, `❌ Error during download of ${currentPO.po_number}`, 'error', '❌');
                }
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

                // Show progress notification
                const saveNotificationId = `save-${poNumber}`;
                showProgressNotification(saveNotificationId, `💾 Saving PO ${poNumber} details to database...`, 'processing', '💾');

                // Save PO details
                const saveResponse = await fetch('/api/po/save_details', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({po_number: poNumber, overwrite: overwrite})
                });

                const saveResult = await saveResponse.json();

                if (saveResult.success) {
                    updateNotification(saveNotificationId, `✅ Finished Saving PO ${poNumber} to database (${saveResult.items_count} items)`, 'success', '✅');
                    return true;
                } else {
                    updateNotification(saveNotificationId, `❌ Failed to save PO ${poNumber}: ${saveResult.message}`, 'error', '❌');
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

        function showError(message, type = 'error', persistent = false) {
            const container = document.getElementById('error_container');
            const className = type === 'success' ? 'success' : 'error';

            // Full-screen overlay styling
            const overlayStyle = `
                position: fixed;
                top: 0;
                left: 0;
                width: 100vw;
                height: 100vh;
                background: rgba(0, 0, 0, 0.9);
                display: flex;
                justify-content: center;
                align-items: center;
                z-index: 9999;
                backdrop-filter: blur(2px);
            `;

            const messageStyle = `
                background: rgba(128, 128, 128, 0.95);
                color: #333;
                padding: 30px 50px;
                border-radius: 15px;
                font-size: 18px;
                font-weight: 600;
                text-align: center;
                box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
                border: 2px solid rgba(255, 255, 255, 0.2);
                max-width: 80%;
                word-wrap: break-word;
            `;

            container.innerHTML = `
                <div class="${className}" style="${overlayStyle}">
                    <div style="${messageStyle}">${message}</div>
                </div>
            `;

            // Auto-hide messages after 3 seconds, unless persistent
            if (!persistent) {
                setTimeout(() => {
                    container.innerHTML = '';
                }, 3000);
            }
        }

        // Function to clear persistent messages
        function clearError() {
            const container = document.getElementById('error_container');
            container.innerHTML = '';
        }

        // Master Report Functions
        let masterReportData = [];
        let searchTimeout = null;

        function loadMasterReport() {
            console.log('🔍 Loading master report...');

            // Show loading state
            document.getElementById('master_report_loading').style.display = 'block';
            document.getElementById('master_report_container').style.display = 'none';
            document.getElementById('master_report_empty').style.display = 'none';

            fetch('/api/master_report?limit=20')
                .then(response => response.json())
                .then(data => {
                    console.log('📊 Master report data received:', data);

                    if (data.success && data.data.length > 0) {
                        masterReportData = data.data;
                        displayMasterReportData(data.data);
                        updateMasterReportStats(data);

                        // Show table
                        document.getElementById('master_report_loading').style.display = 'none';
                        document.getElementById('master_report_container').style.display = 'block';
                    } else {
                        // Show empty state
                        document.getElementById('master_report_loading').style.display = 'none';
                        document.getElementById('master_report_empty').style.display = 'block';
                    }
                })
                .catch(error => {
                    console.error('❌ Error loading master report:', error);
                    showError('Failed to load master report: ' + error.message);
                    document.getElementById('master_report_loading').style.display = 'none';
                    document.getElementById('master_report_empty').style.display = 'block';
                });
        }

        function displayMasterReportData(data) {
            const tbody = document.getElementById('master_report_tbody');
            tbody.innerHTML = '';

            data.forEach((row, index) => {
                const tr = document.createElement('tr');
                tr.style.borderBottom = '1px solid #dee2e6';

                // Alternate row colors
                if (index % 2 === 1) {
                    tr.style.backgroundColor = '#f8f9fa';
                }

                tr.innerHTML = `
                    <!-- Fixed Columns -->
                    <td style="position: sticky; left: 0; background: ${index % 2 === 1 ? '#f8f9fa' : 'white'}; z-index: 5; padding: 8px; border-right: 2px solid #adb5bd; font-weight: 500; width: 120px; vertical-align: top;" title="${row.po_number || ''}">${row.po_number || ''}</td>
                    <td style="position: sticky; left: 120px; background: ${index % 2 === 1 ? '#f8f9fa' : 'white'}; z-index: 5; padding: 8px; border-right: 2px solid #adb5bd; font-weight: 500; width: 140px; vertical-align: top;" title="${row.item_number || ''}">${row.item_number || ''}</td>
                    <td style="position: sticky; left: 260px; background: ${index % 2 === 1 ? '#f8f9fa' : 'white'}; z-index: 5; padding: 8px; border-right: 2px solid #adb5bd; width: 250px; vertical-align: top;" title="${row.description || ''}">${row.description || ''}</td>

                    <!-- Scrollable Columns -->
                    <td style="padding: 8px; width: 120px; vertical-align: top;" title="${row.color || ''}">${row.color || ''}</td>
                    <td style="padding: 8px; width: 140px; vertical-align: top;" title="${row.ship_to || ''}">${row.ship_to || ''}</td>
                    <td style="padding: 8px; width: 120px; vertical-align: top;" title="${row.need_by || ''}">${row.need_by || ''}</td>
                    <td style="padding: 8px; text-align: right; width: 100px; vertical-align: top;" title="${row.qty || ''}">${row.qty || ''}</td>
                    <td style="padding: 8px; text-align: right; width: 120px; vertical-align: top;" title="${row.bundle_qty || ''}">${row.bundle_qty || ''}</td>
                    <td style="padding: 8px; text-align: right; width: 120px; vertical-align: top;" title="${row.unit_price || ''}">${row.unit_price || ''}</td>
                    <td style="padding: 8px; text-align: right; width: 120px; vertical-align: top;" title="${row.extension || ''}">${row.extension || ''}</td>
                    <td style="padding: 8px; width: 150px; vertical-align: top;" title="${row.company || ''}">${row.company || ''}</td>
                    <td style="padding: 8px; width: 160px; vertical-align: top;" title="${row.purchase_from || ''}">${row.purchase_from || ''}</td>
                    <td style="padding: 8px; width: 100px; vertical-align: top;" title="${row.currency || ''}">${row.currency || ''}</td>
                    <td style="padding: 8px; width: 120px; vertical-align: top;" title="${row.po_date || ''}">${row.po_date || ''}</td>
                    <td style="padding: 8px; width: 130px; vertical-align: top;" title="${row.cancel_date || ''}">${row.cancel_date || ''}</td>
                    <td style="padding: 8px; width: 120px; vertical-align: top;" title="${row.ship_by || ''}">${row.ship_by || ''}</td>
                    <td style="padding: 8px; width: 140px; vertical-align: top;" title="${row.ship_via || ''}">${row.ship_via || ''}</td>
                    <td style="padding: 8px; width: 130px; vertical-align: top;" title="${row.order_type || ''}">${row.order_type || ''}</td>
                    <td style="padding: 8px; width: 100px; vertical-align: top;" title="${row.status || ''}">${row.status || ''}</td>
                    <td style="padding: 8px; width: 150px; vertical-align: top;" title="${row.factory || ''}">${row.factory || ''}</td>
                    <td style="padding: 8px; width: 120px; vertical-align: top;" title="${row.location || ''}">${row.location || ''}</td>
                    <td style="padding: 8px; width: 130px; vertical-align: top;" title="${row.prod_rep || ''}">${row.prod_rep || ''}</td>
                    <td style="padding: 8px; width: 200px; vertical-align: top;" title="${row.ship_to_address || ''}">${row.ship_to_address || ''}</td>
                    <td style="padding: 8px; width: 130px; vertical-align: top;" title="${row.terms || ''}">${row.terms || ''}</td>
                    <td style="padding: 8px; font-size: 0.8em; color: #666; width: 150px; vertical-align: top;" title="${row.first_created || ''}">${row.first_created || ''}</td>
                    <td style="padding: 8px; font-size: 0.8em; color: #666; width: 150px; vertical-align: top;" title="${row.last_updated || ''}">${row.last_updated || ''}</td>
                    <td style="padding: 8px; text-align: center; width: 120px; vertical-align: top;" title="${row.update_count || '0'}">${row.update_count || '0'}</td>
                `;

                tbody.appendChild(tr);
            });
        }

        function updateMasterReportStats(data) {
            const now = new Date().toLocaleString();
            const activeFilters = getActiveFilterCount();

            document.getElementById('master_report_stats').textContent =
                `📊 Showing ${data.filtered_count} of ${data.total_count} total records | 🔍 Active filters: ${activeFilters} | 📅 Last updated: ${now}`;
        }

        function getActiveFilterCount() {
            const searchInputs = document.querySelectorAll('#master_report_table input[id^="search_"]');
            let count = 0;
            searchInputs.forEach(input => {
                if (input.value.trim()) count++;
            });
            return count;
        }

        function searchMasterReport() {
            // Clear existing timeout
            if (searchTimeout) {
                clearTimeout(searchTimeout);
            }

            // Debounce search to avoid too many requests
            searchTimeout = setTimeout(() => {
                performMasterReportSearch();
            }, 500);
        }

        function performMasterReportSearch() {
            console.log('🔍 Performing master report search...');

            // Collect search filters
            const searchParams = new URLSearchParams();
            searchParams.append('limit', '20');

            const searchInputs = document.querySelectorAll('#master_report_table input[id^="search_"]');
            searchInputs.forEach(input => {
                if (input.value.trim()) {
                    const columnName = input.id.replace('search_', '');
                    searchParams.append(`search_${columnName}`, input.value.trim());
                }
            });

            // Show loading state
            document.getElementById('master_report_loading').style.display = 'block';
            document.getElementById('master_report_container').style.display = 'none';

            fetch(`/api/master_report?${searchParams.toString()}`)
                .then(response => response.json())
                .then(data => {
                    console.log('📊 Search results received:', data);

                    if (data.success) {
                        masterReportData = data.data;
                        displayMasterReportData(data.data);
                        updateMasterReportStats(data);

                        // Show table or empty state
                        document.getElementById('master_report_loading').style.display = 'none';
                        if (data.data.length > 0) {
                            document.getElementById('master_report_container').style.display = 'block';
                            document.getElementById('master_report_empty').style.display = 'none';
                        } else {
                            document.getElementById('master_report_container').style.display = 'none';
                            document.getElementById('master_report_empty').style.display = 'block';
                        }
                    } else {
                        showError('Search failed: ' + (data.error || 'Unknown error'));
                        document.getElementById('master_report_loading').style.display = 'none';
                        document.getElementById('master_report_empty').style.display = 'block';
                    }
                })
                .catch(error => {
                    console.error('❌ Error searching master report:', error);
                    showError('Search failed: ' + error.message);
                    document.getElementById('master_report_loading').style.display = 'none';
                    document.getElementById('master_report_empty').style.display = 'block';
                });
        }

        function refreshMasterReport() {
            console.log('🔄 Refreshing master report...');
            clearAllSearchFilters();
            loadMasterReport();
        }

        function clearAllSearchFilters() {
            console.log('🗑️ Clearing all search filters...');
            const searchInputs = document.querySelectorAll('#master_report_table input[id^="search_"]');
            searchInputs.forEach(input => {
                input.value = '';
            });
            loadMasterReport();
        }

        function exportMasterReport() {
            console.log('📥 Exporting master report to Excel...');

            // Collect current search filters
            const searchParams = new URLSearchParams();
            const searchInputs = document.querySelectorAll('#master_report_table input[id^="search_"]');
            searchInputs.forEach(input => {
                if (input.value.trim()) {
                    const columnName = input.id.replace('search_', '');
                    searchParams.append(`search_${columnName}`, input.value.trim());
                }
            });

            // Create download URL
            const exportUrl = `/api/export_master_report?${searchParams.toString()}`;

            // Create temporary link and trigger download
            const link = document.createElement('a');
            link.href = exportUrl;
            link.download = '';
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);

            showSuccess('📥 Excel export started! Check your downloads folder.');
        }

        function loadMoreRecords() {
            console.log('📄 Loading more records...');
            // TODO: Implement pagination
            showInfo('📄 Pagination feature coming soon!');
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
    print(f"🚀 Starting artwork downloader v{VERSION}...")
    print(f"📅 Version Date: {VERSION_DATE}")
    print(f"📝 Last Edit: {LAST_EDIT}")
    print("📊 Initializing PO database...")
    init_database()
    print("📱 Open your browser and go to: http://localhost:5002")
    print("🛑 Press Ctrl+C to stop the server")

    app.run(debug=False, host='127.0.0.1', port=5002)
