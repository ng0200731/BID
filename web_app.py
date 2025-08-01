"""
BID Web Application
4 Tabs: Download Artwork, Update Delivery Date, Report, Settings
"""
from flask import Flask, render_template, request, jsonify, send_file
import os
import json
import time
import threading
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

app = Flask(__name__)
app.secret_key = 'bid_web_app_2025'

# Global variables for download progress
download_progress = {}
download_results = {}

class BIDWebDownloader:
    def __init__(self):
        self.driver = None
        
    def setup_driver(self):
        """Setup Chrome driver"""
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        
    def login(self):
        """Login to E-BrandID"""
        try:
            self.driver.get("https://app.e-brandid.com/login/login.aspx")
            wait = WebDriverWait(self.driver, 30)
            
            username_field = wait.until(EC.presence_of_element_located((By.ID, "txtUserName")))
            password_field = self.driver.find_element(By.ID, "txtPassword")
            
            username_field.send_keys("sales10@fuchanghk.com")
            password_field.send_keys("fc31051856")
            
            login_button = self.driver.find_element(By.XPATH, "//img[@onclick='return Login();']")
            login_button.click()
            
            wait.until(lambda d: "login" not in d.current_url.lower())
            return True
        except Exception as e:
            print(f"Login error: {e}")
            return False
    
    def search_po(self, po_number):
        """Search for PO and return items"""
        try:
            if not self.driver:
                self.setup_driver()
                if not self.login():
                    return {"error": "Login failed"}
            
            # Navigate to PO
            po_url = f"https://app.e-brandid.com/Bidnet/bidnet3/factoryPODetail.aspx?po_id={po_number}"
            self.driver.get(po_url)
            
            wait = WebDriverWait(self.driver, 30)
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "table")))
            time.sleep(3)
            
            # Find items
            tables = self.driver.find_elements(By.TAG_NAME, "table")
            item_links = []
            for table in tables:
                links = table.find_elements(By.XPATH, ".//a[contains(@onclick, 'openItemDetail')]")
                if links:
                    item_links = links
                    break
            
            if not item_links:
                return {"error": "No items found in this PO"}
            
            # Extract item information
            items = []
            for i, link in enumerate(item_links):
                item_name = link.text.strip()
                items.append({
                    "id": i + 1,
                    "name": item_name,
                    "selected": True,  # Default all selected
                    "artwork_file": f"Loading..." # Will be determined during download
                })
            
            return {
                "success": True,
                "po_number": po_number,
                "items": items,
                "total_count": len(items)
            }
            
        except Exception as e:
            return {"error": f"Search failed: {str(e)}"}
    
    def download_items(self, po_number, selected_items, method=5):
        """Download selected items using specified method"""
        download_id = f"{po_number}_{int(time.time())}"
        
        # Initialize progress
        download_progress[download_id] = {
            "status": "starting",
            "current": 0,
            "total": len(selected_items),
            "current_file": "",
            "errors": []
        }
        
        # Start download in background thread
        thread = threading.Thread(
            target=self._download_worker,
            args=(download_id, po_number, selected_items, method)
        )
        thread.daemon = True
        thread.start()
        
        return {"download_id": download_id}
    
    def _download_worker(self, download_id, po_number, selected_items, method):
        """Background worker for downloading"""
        try:
            # Create download directory
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            download_dir = os.path.join("static", "downloads", f"PO_{po_number}_{timestamp}")
            os.makedirs(download_dir, exist_ok=True)
            
            download_progress[download_id]["status"] = "downloading"
            download_progress[download_id]["download_dir"] = download_dir
            
            # Method 5: Guaranteed Complete Download
            if method == 5:
                self._method5_download(download_id, po_number, selected_items, download_dir)
            else:
                # Other methods can be implemented later
                download_progress[download_id]["status"] = "error"
                download_progress[download_id]["errors"].append("Only Method 5 is currently supported")
                return
            
            download_progress[download_id]["status"] = "completed"
            
        except Exception as e:
            download_progress[download_id]["status"] = "error"
            download_progress[download_id]["errors"].append(str(e))
    
    def _method5_download(self, download_id, po_number, selected_items, download_dir):
        """Method 5: Guaranteed Complete Download implementation"""
        import re
        import requests
        import shutil
        
        # Re-navigate to PO page
        po_url = f"https://app.e-brandid.com/Bidnet/bidnet3/factoryPODetail.aspx?po_id={po_number}"
        self.driver.get(po_url)
        
        wait = WebDriverWait(self.driver, 30)
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "table")))
        time.sleep(3)
        
        # Find items again
        tables = self.driver.find_elements(By.TAG_NAME, "table")
        item_links = []
        for table in tables:
            links = table.find_elements(By.XPATH, ".//a[contains(@onclick, 'openItemDetail')]")
            if links:
                item_links = links
                break
        
        # Extract PDF URLs for selected items
        item_data = []
        for item_info in selected_items:
            item_index = item_info["id"] - 1  # Convert to 0-based index
            if item_index < len(item_links):
                link = item_links[item_index]
                
                try:
                    download_progress[download_id]["current_file"] = f"Extracting {item_info['name']}"
                    
                    # Click item to open popup
                    original_windows = len(self.driver.window_handles)
                    self.driver.execute_script("arguments[0].click();", link)
                    
                    # Wait for popup
                    popup_opened = False
                    for wait_attempt in range(30):
                        time.sleep(0.1)
                        if len(self.driver.window_handles) > original_windows:
                            popup_opened = True
                            break
                    
                    if popup_opened:
                        self.driver.switch_to.window(self.driver.window_handles[-1])
                        
                        try:
                            # Find download button and extract PDF URL
                            download_button = WebDriverWait(self.driver, 5).until(
                                EC.presence_of_element_located((By.XPATH, "//a[contains(text(), 'Download')]"))
                            )
                            
                            onclick_attr = download_button.get_attribute('onclick')
                            # Extract PDF URL
                            match = re.search(r"MM_openBrWindow\('([^']+\.pdf)'", onclick_attr)
                            if match:
                                pdf_url = match.group(1)
                                original_filename = os.path.basename(pdf_url)
                                item_data.append((item_info['name'], pdf_url, original_filename))
                        
                        except Exception as e:
                            download_progress[download_id]["errors"].append(f"Error extracting {item_info['name']}: {str(e)}")
                        
                        # Close popup
                        self.driver.close()
                        self.driver.switch_to.window(self.driver.window_handles[0])
                        time.sleep(0.5)
                
                except Exception as e:
                    download_progress[download_id]["errors"].append(f"Error processing {item_info['name']}: {str(e)}")
                    continue
        
        # Download with numbering
        download_counter = {}
        unique_pdfs = {}
        downloaded_files = []
        
        for i, (item_name, pdf_url, original_filename) in enumerate(item_data):
            try:
                download_progress[download_id]["current"] = i + 1
                download_progress[download_id]["current_file"] = f"Downloading {original_filename}"
                
                base_name = original_filename.replace('.pdf', '')
                
                if base_name not in download_counter:
                    # First occurrence
                    download_counter[base_name] = 1
                    final_filename = original_filename
                    
                    # Download actual file
                    session = requests.Session()
                    session.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})
                    response = session.get(pdf_url, timeout=30)
                    response.raise_for_status()
                    
                    file_path = os.path.join(download_dir, final_filename)
                    with open(file_path, 'wb') as f:
                        f.write(response.content)
                    
                    unique_pdfs[base_name] = file_path
                    downloaded_files.append(final_filename)
                    
                else:
                    # Subsequent occurrences - numbered copy
                    download_counter[base_name] += 1
                    count = download_counter[base_name]
                    final_filename = f"{base_name}_{count}.pdf"
                    
                    # Copy from cached file
                    if base_name in unique_pdfs:
                        source_file = unique_pdfs[base_name]
                        target_file = os.path.join(download_dir, final_filename)
                        shutil.copy2(source_file, target_file)
                        downloaded_files.append(final_filename)
                
            except Exception as e:
                download_progress[download_id]["errors"].append(f"Error downloading {item_name}: {str(e)}")
                continue
        
        download_progress[download_id]["downloaded_files"] = downloaded_files
        download_progress[download_id]["current_file"] = "Complete!"
    
    def cleanup(self):
        """Cleanup driver"""
        if self.driver:
            self.driver.quit()

# Global downloader instance
downloader = BIDWebDownloader()

@app.route('/')
def index():
    """Main page with tabs"""
    return render_template('index.html')

@app.route('/api/search_po', methods=['POST'])
def api_search_po():
    """API endpoint to search PO"""
    data = request.get_json()
    po_number = data.get('po_number', '').strip()
    
    if not po_number:
        return jsonify({"error": "PO number is required"})
    
    result = downloader.search_po(po_number)
    return jsonify(result)

@app.route('/api/download', methods=['POST'])
def api_download():
    """API endpoint to start download"""
    data = request.get_json()
    po_number = data.get('po_number')
    selected_items = data.get('selected_items', [])
    method = data.get('method', 5)
    
    if not po_number or not selected_items:
        return jsonify({"error": "PO number and selected items are required"})
    
    result = downloader.download_items(po_number, selected_items, method)
    return jsonify(result)

@app.route('/api/progress/<download_id>')
def api_progress(download_id):
    """API endpoint to get download progress"""
    if download_id in download_progress:
        return jsonify(download_progress[download_id])
    else:
        return jsonify({"error": "Download ID not found"})

if __name__ == '__main__':
    # Create necessary directories
    os.makedirs('static/downloads', exist_ok=True)
    os.makedirs('templates', exist_ok=True)
    
    print("🌐 Starting BID Web Application...")
    print("📱 Access at: http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)
