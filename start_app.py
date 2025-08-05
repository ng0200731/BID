#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Start App Launcher
Launches the Flask web application and opens Chrome browser automatically
"""

import subprocess
import time
import sys
import os
import threading
import webbrowser
from pathlib import Path

def start_flask_app():
    """Start the Flask application"""
    print("🚀 Starting Flask application...")
    try:
        # Run the smart_app.py file
        subprocess.run([sys.executable, "smart_app.py"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Error starting Flask app: {e}")
    except KeyboardInterrupt:
        print("\n🛑 Flask app stopped by user")

def wait_for_server(timeout=30):
    """Wait for the Flask server to be ready"""
    import requests
    start_time = time.time()

    # Try both localhost and 127.0.0.1 on port 5002
    urls_to_try = [
        "http://localhost:5002",
        "http://127.0.0.1:5002"
    ]

    while time.time() - start_time < timeout:
        for url in urls_to_try:
            try:
                response = requests.get(url, timeout=2)
                if response.status_code == 200:
                    print(f"✅ Server is ready at {url}")
                    return url
            except requests.exceptions.RequestException:
                pass

        print("⏳ Waiting for server to start...")
        time.sleep(2)

    print(f"❌ Server did not start within {timeout} seconds")
    return None

def open_chrome_browser(url):
    """Open Chrome browser with the application"""
    print(f"🌐 Opening Chrome browser at {url}")
    
    # Try different Chrome executable paths for Windows
    chrome_paths = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        r"C:\Users\%USERNAME%\AppData\Local\Google\Chrome\Application\chrome.exe"
    ]
    
    chrome_found = False
    for chrome_path in chrome_paths:
        expanded_path = os.path.expandvars(chrome_path)
        if os.path.exists(expanded_path):
            try:
                # Launch Chrome with specific flags for better app experience
                subprocess.Popen([
                    expanded_path,
                    "--new-window",
                    "--disable-web-security",
                    "--disable-features=VizDisplayCompositor",
                    url
                ])
                print(f"✅ Chrome launched successfully from: {expanded_path}")
                chrome_found = True
                break
            except Exception as e:
                print(f"❌ Failed to launch Chrome from {expanded_path}: {e}")
                continue
    
    if not chrome_found:
        print("⚠️ Chrome not found in standard locations, trying default browser...")
        try:
            webbrowser.open(url)
            print("✅ Opened in default browser")
        except Exception as e:
            print(f"❌ Failed to open browser: {e}")
            print(f"📝 Please manually open: {url}")

def main():
    """Main function to start both Flask app and browser"""
    print("=" * 60)
    print("🎯 BID Smart App Launcher")
    print("=" * 60)
    
    # Check if smart_app.py exists
    if not os.path.exists("smart_app.py"):
        print("❌ smart_app.py not found in current directory!")
        print(f"📁 Current directory: {os.getcwd()}")
        print("📝 Please make sure you're in the correct directory")
        return
    
    print("✅ Found smart_app.py")
    
    # Start Flask app in a separate thread
    flask_thread = threading.Thread(target=start_flask_app, daemon=True)
    flask_thread.start()
    
    # Wait for the server to be ready
    server_url = wait_for_server()
    if server_url:
        # Open Chrome browser
        time.sleep(1)  # Small delay to ensure server is fully ready
        open_chrome_browser(server_url)
        
        print("\n" + "=" * 60)
        print("🎉 Application started successfully!")
        print("📱 Web App: http://localhost:5002")
        print("🌐 Chrome browser should open automatically")
        print("🛑 Press Ctrl+C to stop the application")
        print("=" * 60)
        
        try:
            # Keep the main thread alive
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 Shutting down application...")
            print("👋 Goodbye!")
    else:
        print("❌ Failed to start the application")

if __name__ == "__main__":
    main()
