"""
Simple test script for E-BrandID downloader
Tests the basic functionality without GUI
"""

from ebrandid_downloader import EBrandIDDownloader
import os

def test_ebrandid_downloader():
    """Test the E-BrandID downloader with PO 1288060"""
    
    print("🚀 Testing E-BrandID File Downloader")
    print("=" * 50)
    
    # Test parameters
    po_number = "1288060"
    username = "sales10@fuchanghk.com"
    password = "fc31051856"
    
    print(f"PO Number: {po_number}")
    print(f"Username: {username}")
    print(f"Download Path: {os.getcwd()}")
    print()
    
    # Create downloader (visible browser for testing)
    downloader = EBrandIDDownloader(headless=False, download_path=os.getcwd())
    
    print("Starting 3-milestone process...")
    print()
    
    try:
        # Run complete process
        success, message = downloader.run_complete_process(po_number, username, password)
        
        print()
        print("=" * 50)
        if success:
            print(f"🎉 SUCCESS: {message}")
            print(f"📁 Check folder: {os.path.join(os.getcwd(), po_number)}")
        else:
            print(f"❌ FAILED: {message}")
        print("=" * 50)
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
    
    print("\nTest completed!")

if __name__ == "__main__":
    test_ebrandid_downloader()
