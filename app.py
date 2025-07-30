"""
E-BrandID Downloader Web App
Modern web interface for all download methods
"""

from flask import Flask, render_template, request, jsonify, send_from_directory
import os
import json
import threading
import time
from datetime import datetime
import glob

# Import our downloader logic
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

app = Flask(__name__)

# Global variables for tracking downloads
download_status = {
    'active': False,
    'progress': 0,
    'current_item': '',
    'total_items': 0,
    'processed': 0,
    'failed': 0,
    'files_downloaded': 0,
    'log': [],
    'error': None
}

@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')

@app.route('/api/start_download', methods=['POST'])
def start_download():
    """Start download process"""
    global download_status
    
    if download_status['active']:
        return jsonify({'error': 'Download already in progress'}), 400
    
    data = request.json
    po_number = data.get('po_number')
    method = data.get('method')
    item_selection = data.get('item_selection', 'all')
    item_count = data.get('item_count', 0)
    
    if not po_number or not method:
        return jsonify({'error': 'Missing required parameters'}), 400
    
    # Reset status
    download_status = {
        'active': True,
        'progress': 0,
        'current_item': '',
        'total_items': 0,
        'processed': 0,
        'failed': 0,
        'files_downloaded': 0,
        'log': [],
        'error': None,
        'po_number': po_number,
        'method': method
    }
    
    # Start download in background thread
    thread = threading.Thread(
        target=run_download,
        args=(po_number, method, item_selection, item_count)
    )
    thread.daemon = True
    thread.start()
    
    return jsonify({'success': True, 'message': 'Download started'})

@app.route('/api/status')
def get_status():
    """Get current download status"""
    return jsonify(download_status)

@app.route('/api/stop_download', methods=['POST'])
def stop_download():
    """Stop current download"""
    global download_status
    download_status['active'] = False
    download_status['error'] = 'Stopped by user'
    return jsonify({'success': True})

@app.route('/api/get_po_info', methods=['POST'])
def get_po_info():
    """Get PO information (item count, etc.)"""
    data = request.json
    po_number = data.get('po_number')
    
    if not po_number:
        return jsonify({'error': 'PO number required'}), 400
    
    try:
        # This would normally connect to get PO info
        # For now, return mock data
        return jsonify({
            'success': True,
            'po_number': po_number,
            'total_items': 25,  # Mock data
            'po_status': 'Active',
            'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def run_download(po_number, method, item_selection, item_count):
    """Run download process in background"""
    global download_status
    
    try:
        download_status['log'].append(f"Starting {get_method_name(method)} for PO {po_number}")
        
        # Simple mock downloader for now
        download_status['log'].append("Mock downloader - simulating process...")

        # Simulate processing
        for i in range(10):
            if not download_status['active']:
                break
            download_status['progress'] = (i + 1) * 10
            download_status['current_item'] = f"Item {i+1}"
            download_status['processed'] = i + 1
            download_status['log'].append(f"Processing item {i+1}")
            time.sleep(2)

        download_status['files_downloaded'] = download_status['processed']
        download_status['active'] = False
        
    except Exception as e:
        download_status['error'] = str(e)
        download_status['active'] = False
        download_status['log'].append(f"Error: {str(e)}")

def get_method_name(method):
    """Get method name from number"""
    methods = {
        '1': 'Standard Download',
        '2': 'Hybrid Speed Download',
        '3': 'Enhanced Download',
        '4': 'Clean Naming Download',
        '5': 'Test Mode'
    }
    return methods.get(method, 'Unknown Method')

if __name__ == '__main__':
    print("🚀 Starting E-BrandID Downloader Web App...")
    print("📱 Open your browser and go to: http://localhost:5000")
    print("🛑 Press Ctrl+C to stop the server")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
