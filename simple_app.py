"""
Simple E-BrandID Downloader Web App
"""

from flask import Flask, render_template_string
import webbrowser
import threading
import time

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>E-BrandID Downloader</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f5f5f5;
            min-height: 100vh;
            padding: 20px;
            color: #333;
        }

        .container {
            max-width: 900px;
            margin: 0 auto;
            background: white;
            border: 1px solid #e0e0e0;
            overflow: hidden;
        }

        .header {
            background: #333;
            color: white;
            padding: 30px;
            text-align: center;
            border-bottom: 1px solid #e0e0e0;
        }

        .header h1 {
            font-size: 2em;
            margin-bottom: 8px;
            font-weight: 300;
        }

        .header p {
            font-size: 1em;
            opacity: 0.8;
            font-weight: 300;
        }
        
        .content {
            padding: 30px;
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
        
        .method-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 15px;
            margin-bottom: 30px;
        }

        .method-card {
            border: 1px solid #e0e0e0;
            padding: 20px;
            cursor: pointer;
            transition: all 0.2s;
            text-align: left;
            background: white;
        }

        .method-card:hover {
            border-color: #333;
            background: #fafafa;
        }

        .method-card.selected {
            border-color: #333;
            background: #f9f9f9;
        }

        .method-card .icon {
            font-size: 1.5em;
            margin-bottom: 10px;
            color: #333;
        }

        .method-card h3 {
            color: #333;
            margin-bottom: 8px;
            font-size: 1.1em;
            font-weight: 500;
        }

        .method-card p {
            color: #666;
            line-height: 1.4;
            font-size: 0.9em;
        }
        
        .form-section {
            background: #fafafa;
            padding: 25px;
            border: 1px solid #e0e0e0;
            margin-bottom: 25px;
        }

        .form-group {
            margin-bottom: 20px;
        }

        .form-group label {
            display: block;
            margin-bottom: 8px;
            font-weight: 500;
            color: #333;
            font-size: 0.9em;
        }

        .form-group input, .form-group select {
            width: 100%;
            padding: 12px;
            border: 1px solid #ccc;
            font-size: 1em;
            transition: border-color 0.2s;
            background: white;
        }

        .form-group input:focus, .form-group select:focus {
            outline: none;
            border-color: #333;
        }
        
        .radio-group {
            display: flex;
            gap: 25px;
            margin-top: 12px;
        }

        .radio-item {
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 0.9em;
        }

        .radio-item input[type="radio"] {
            width: auto;
        }

        .btn {
            background: #333;
            color: white;
            border: 1px solid #333;
            padding: 12px 24px;
            font-size: 0.9em;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.2s;
            display: inline-block;
            text-decoration: none;
        }

        .btn:hover {
            background: #555;
            border-color: #555;
        }

        .btn-large {
            padding: 15px 30px;
            font-size: 1em;
        }
        
        .coming-soon {
            text-align: center;
            padding: 40px;
            color: #666;
        }

        .coming-soon h3 {
            font-size: 1.3em;
            margin-bottom: 15px;
            color: #333;
            font-weight: 500;
        }

        .coming-soon ul {
            text-align: left;
            max-width: 400px;
            margin: 20px auto;
            font-size: 0.9em;
            line-height: 1.6;
        }

        .launch-section {
            text-align: center;
            padding: 30px;
            background: #f9f9f9;
            border: 1px solid #e0e0e0;
            margin-top: 25px;
        }

        .launch-section h3 {
            color: #333;
            margin-bottom: 15px;
            font-size: 1.2em;
            font-weight: 500;
        }

        .launch-section p {
            font-size: 0.9em;
            color: #666;
            margin-bottom: 20px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>E-BrandID Downloader</h1>
            <p>Download artwork files</p>
        </div>
        
        <div class="content">
            <div class="tabs">
                <button class="tab active" onclick="showTab('artwork')">Download Artwork</button>
                <button class="tab" onclick="showTab('po')">PO Management</button>
                <button class="tab" onclick="showTab('settings')">Settings</button>
            </div>
            
            <!-- Download Artwork Tab -->
            <div id="artwork" class="tab-content active">
                <h2 style="margin-bottom: 25px; color: #333; font-size: 1.3em; font-weight: 500;">Choose Download Method</h2>

                <div class="method-grid">
                    <div class="method-card" onclick="selectMethod('hybrid')">
                        <div class="icon">⚡</div>
                        <h3>Hybrid Speed</h3>
                        <p><strong>Recommended</strong><br>Ultra-fast processing with smart monitoring. 20x faster than standard method.</p>
                    </div>

                    <div class="method-card" onclick="selectMethod('clean')">
                        <div class="icon">📝</div>
                        <h3>Clean Naming</h3>
                        <p><strong>Best Organization</strong><br>Perfect file organization with clean naming pattern (original_name_1, original_name_2).</p>
                    </div>

                    <div class="method-card" onclick="selectMethod('standard')">
                        <div class="icon">🎯</div>
                        <h3>Standard Download</h3>
                        <p><strong>Most Reliable</strong><br>Original reliable method. Slower but very stable. Good for small POs.</p>
                    </div>

                    <div class="method-card" onclick="selectMethod('enhanced')">
                        <div class="icon">🔄</div>
                        <h3>Enhanced Download</h3>
                        <p><strong>Handles Duplicates</strong><br>Creates copies of duplicate PDFs with item names.</p>
                    </div>
                </div>
                
                <div class="form-section">
                    <div class="form-group">
                        <label for="po_number">PO Number:</label>
                        <input type="text" id="po_number" placeholder="Enter PO number (e.g., 1288060, 1284678)" />
                    </div>

                    <div class="form-group">
                        <label>Items to Download:</label>
                        <div class="radio-group">
                            <div class="radio-item">
                                <input type="radio" id="all_items" name="item_selection" value="all" checked />
                                <label for="all_items">All items</label>
                            </div>
                            <div class="radio-item">
                                <input type="radio" id="first_x" name="item_selection" value="first_x" />
                                <label for="first_x">First X items</label>
                            </div>
                            <div class="radio-item">
                                <input type="radio" id="test_mode" name="item_selection" value="test" />
                                <label for="test_mode">Test (5 items)</label>
                            </div>
                        </div>

                        <div style="margin-top: 12px; display: none;" id="item_count_section">
                            <input type="number" id="item_count" placeholder="Number of items" min="1" style="width: 150px;" />
                        </div>
                    </div>
                </div>

                <div class="launch-section">
                    <h3>Ready to Launch</h3>
                    <p>Click the button below to start the downloader with your selected options.</p>
                    <button class="btn btn-large" onclick="launchDownloader()">Launch Downloader</button>
                </div>
            </div>
            
            <!-- PO Management Tab -->
            <div id="po" class="tab-content">
                <div class="coming-soon">
                    <h3>PO Management</h3>
                    <p>Future feature for comprehensive PO management</p>
                    <ul>
                        <li>View PO details and status</li>
                        <li>Set and track delivery dates</li>
                        <li>Batch download multiple POs</li>
                        <li>Download history and analytics</li>
                        <li>Automatic PO synchronization</li>
                    </ul>
                </div>
            </div>

            <!-- Settings Tab -->
            <div id="settings" class="tab-content">
                <div class="coming-soon">
                    <h3>Settings & Configuration</h3>
                    <p>Future feature for system customization</p>
                    <ul>
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
        let selectedMethod = 'hybrid';
        
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
            
            // Add active class to clicked tab
            event.target.classList.add('active');
        }
        
        function selectMethod(method) {
            selectedMethod = method;
            
            // Remove selected class from all cards
            document.querySelectorAll('.method-card').forEach(card => {
                card.classList.remove('selected');
            });
            
            // Add selected class to clicked card
            event.target.classList.add('selected');
        }
        
        // Handle item selection radio buttons
        document.querySelectorAll('input[name="item_selection"]').forEach(radio => {
            radio.addEventListener('change', function() {
                const countSection = document.getElementById('item_count_section');
                if (this.value === 'first_x') {
                    countSection.style.display = 'block';
                } else {
                    countSection.style.display = 'none';
                }
            });
        });
        
        function launchDownloader() {
            const poNumber = document.getElementById('po_number').value.trim();
            const itemSelection = document.querySelector('input[name="item_selection"]:checked').value;
            const itemCount = document.getElementById('item_count').value;
            
            if (!poNumber) {
                alert('Please enter a PO number');
                return;
            }
            
            if (itemSelection === 'first_x' && (!itemCount || itemCount < 1)) {
                alert('Please enter a valid number of items');
                return;
            }
            
            // Create command to run
            let methodNumber;
            switch(selectedMethod) {
                case 'standard': methodNumber = '1'; break;
                case 'hybrid': methodNumber = '2'; break;
                case 'enhanced': methodNumber = '3'; break;
                case 'clean': methodNumber = '4'; break;
                default: methodNumber = '2';
            }
            
            // Show instructions
            const instructions = `
🚀 LAUNCH INSTRUCTIONS:

1. Open Command Prompt or PowerShell
2. Navigate to your project folder: cd C:\\crawl_web
3. Run this command:

C:\\crawl_web\\venv\\Scripts\\python.exe unified_downloader.py

4. When prompted:
   - Choose method: ${methodNumber} (${getMethodName(selectedMethod)})
   - Enter PO: ${poNumber}
   - Select items: ${getItemSelectionText(itemSelection, itemCount)}

5. Confirm and start download!

📁 Files will be saved to: YYYY_MM_DD_HH_MM_${poNumber}
   (e.g., 2025_07_31_14_30_${poNumber})

The downloader will open automatically with your browser and start processing.
            `;
            
            alert(instructions);
            
            // Also copy command to clipboard if possible
            if (navigator.clipboard) {
                navigator.clipboard.writeText('C:\\\\crawl_web\\\\venv\\\\Scripts\\\\python.exe unified_downloader.py');
            }
        }
        
        function getMethodName(method) {
            const names = {
                'standard': 'Standard Download',
                'hybrid': 'Hybrid Speed Download',
                'enhanced': 'Enhanced Download',
                'clean': 'Clean Naming Download'
            };
            return names[method] || 'Hybrid Speed Download';
        }
        
        function getItemSelectionText(selection, count) {
            switch(selection) {
                case 'all': return 'All items';
                case 'first_x': return `First ${count} items`;
                case 'test': return 'Test mode (5 items)';
                default: return 'All items';
            }
        }
        
        // Initialize
        document.addEventListener('DOMContentLoaded', function() {
            // Select default method
            document.querySelector('.method-card').classList.add('selected');
        });
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

def open_browser():
    """Open browser after a short delay"""
    time.sleep(1.5)
    webbrowser.open('http://localhost:5000')

if __name__ == '__main__':
    print("🚀 Starting E-BrandID Downloader Web Interface...")
    print("📱 Opening browser automatically...")
    print("🌐 URL: http://localhost:5000")
    print("🛑 Press Ctrl+C to stop the server")
    print()
    
    # Open browser in background
    threading.Thread(target=open_browser, daemon=True).start()
    
    # Start Flask app
    app.run(debug=False, host='127.0.0.1', port=5000, use_reloader=False)
