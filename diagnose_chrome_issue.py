#!/usr/bin/env python3
"""
Diagnostic script to identify ChromeDriver issues on different computers
Run this on the computer where the executable fails
"""

import os
import sys
import subprocess
import platform

def diagnose_chrome_setup():
    """Diagnose Chrome and ChromeDriver setup issues"""
    print("🔍 BID Smart App - Chrome Diagnostic Tool")
    print("=" * 50)
    
    # System Information
    print(f"💻 Operating System: {platform.system()} {platform.release()}")
    print(f"🏗️ Architecture: {platform.architecture()[0]}")
    print(f"🐍 Python Version: {sys.version}")
    print()
    
    # Check Chrome Installation
    print("🌐 Checking Chrome Installation...")
    chrome_paths = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        r"C:\Users\{}\AppData\Local\Google\Chrome\Application\chrome.exe".format(os.getenv('USERNAME', '')),
    ]
    
    chrome_found = False
    chrome_version = "Unknown"
    
    for path in chrome_paths:
        if os.path.exists(path):
            chrome_found = True
            print(f"✅ Chrome found: {path}")
            
            # Try to get Chrome version
            try:
                result = subprocess.run([path, "--version"], capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    chrome_version = result.stdout.strip()
                    print(f"📋 Chrome Version: {chrome_version}")
            except Exception as e:
                print(f"⚠️ Could not get Chrome version: {e}")
            break
    
    if not chrome_found:
        print("❌ Chrome not found in standard locations")
        print("💡 Please install Google Chrome from: https://www.google.com/chrome/")
        return False
    
    print()
    
    # Check ChromeDriver
    print("🔧 Checking ChromeDriver...")
    chromedriver_paths = [
        "chromedriver.exe",
        os.path.join(os.getcwd(), "chromedriver.exe"),
        os.path.join(sys.executable, "..", "chromedriver.exe") if not getattr(sys, 'frozen', False) else None
    ]
    
    chromedriver_found = False
    chromedriver_version = "Unknown"
    
    for path in chromedriver_paths:
        if path and os.path.exists(path):
            chromedriver_found = True
            print(f"✅ ChromeDriver found: {path}")
            
            # Try to get ChromeDriver version
            try:
                result = subprocess.run([path, "--version"], capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    chromedriver_version = result.stdout.strip()
                    print(f"📋 ChromeDriver Version: {chromedriver_version}")
            except Exception as e:
                print(f"⚠️ Could not get ChromeDriver version: {e}")
            break
    
    if not chromedriver_found:
        print("❌ ChromeDriver not found")
        print("💡 This might be the issue!")
    
    print()
    
    # Check Network Connectivity
    print("🌐 Checking Network Connectivity...")
    test_urls = [
        "https://www.google.com",
        "https://e-brandid.com",
    ]
    
    for url in test_urls:
        try:
            import urllib.request
            urllib.request.urlopen(url, timeout=10)
            print(f"✅ Can reach: {url}")
        except Exception as e:
            print(f"❌ Cannot reach {url}: {e}")
    
    print()
    
    # Check Python Dependencies
    print("📦 Checking Python Dependencies...")
    required_packages = [
        'selenium',
        'webdriver_manager',
        'requests',
        'flask',
        'beautifulsoup4'
    ]
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"✅ {package} installed")
        except ImportError:
            print(f"❌ {package} missing")
    
    print()
    
    # Test Basic Selenium
    print("🧪 Testing Basic Selenium Setup...")
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.chrome.service import Service
        
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        
        # Try with ChromeDriverManager first
        try:
            from webdriver_manager.chrome import ChromeDriverManager
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
            driver.get("https://www.google.com")
            print("✅ ChromeDriverManager works - this should fix the issue!")
            driver.quit()
            return True
        except Exception as e:
            print(f"❌ ChromeDriverManager failed: {e}")
        
        # Try with local ChromeDriver
        if chromedriver_found:
            try:
                service = Service(chromedriver_paths[1])  # Use found path
                driver = webdriver.Chrome(service=service, options=chrome_options)
                driver.get("https://www.google.com")
                print("✅ Local ChromeDriver works")
                driver.quit()
                return True
            except Exception as e:
                print(f"❌ Local ChromeDriver failed: {e}")
        
    except Exception as e:
        print(f"❌ Selenium test failed: {e}")
    
    print()
    print("🔧 RECOMMENDATIONS:")
    print("1. Install/Update Google Chrome to latest version")
    print("2. Use ChromeDriverManager for automatic version matching")
    print("3. Check Windows Defender/Antivirus settings")
    print("4. Run as Administrator if needed")
    print("5. Check corporate firewall settings")
    
    return False

if __name__ == '__main__':
    success = diagnose_chrome_setup()
    if success:
        print("\n🎉 Chrome setup looks good!")
    else:
        print("\n❌ Chrome setup has issues - see recommendations above")
    
    input("\nPress Enter to close...")
