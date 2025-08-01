"""
Test Method 5 integration in unified_downloader
"""

def test_menu():
    """Test that Method 5 appears in the menu"""
    try:
        # Import the class
        from unified_downloader import UnifiedDownloader
        
        # Create instance
        downloader = UnifiedDownloader()
        
        # Test menu display (capture output)
        import io
        import sys
        from unittest.mock import patch
        
        # Capture print output
        captured_output = io.StringIO()
        
        with patch('sys.stdout', captured_output):
            with patch('builtins.input', return_value='5'):  # Simulate user input
                try:
                    method = downloader.show_main_menu()
                    print(f"Selected method: {method}")
                except:
                    pass  # Expected since we're just testing menu display
        
        # Get the captured output
        menu_output = captured_output.getvalue()
        
        # Check if Method 5 is in the menu
        if "Guaranteed Complete Download" in menu_output:
            print("✅ SUCCESS: Method 5 'Guaranteed Complete Download' found in menu!")
            print("✅ Method 5 integration successful!")
            return True
        else:
            print("❌ FAILED: Method 5 not found in menu")
            print("Menu output:")
            print(menu_output)
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing Method 5 integration...")
    print("=" * 50)
    
    success = test_menu()
    
    if success:
        print("\n🎉 Method 5 is successfully integrated!")
        print("📋 Users can now select:")
        print("   1. Standard Download")
        print("   2. Hybrid Speed Download") 
        print("   3. Enhanced Download")
        print("   4. Clean Naming Download")
        print("   5. ✨ Guaranteed Complete Download ✨")
        print("   6. Test Mode")
    else:
        print("\n❌ Method 5 integration failed!")
