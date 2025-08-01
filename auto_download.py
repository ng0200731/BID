"""
Auto downloader script to run unified_downloader with preset parameters
"""
import subprocess
import sys

def run_downloader():
    """Run the unified downloader with method 2 and PO 1284678"""
    try:
        # Prepare the inputs
        inputs = "2\n1284678\n"
        
        # Run the unified_downloader.py with inputs
        process = subprocess.Popen(
            [sys.executable, "unified_downloader.py"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Send inputs and get output
        stdout, stderr = process.communicate(input=inputs, timeout=300)
        
        print("=== DOWNLOADER OUTPUT ===")
        print(stdout)
        
        if stderr:
            print("=== ERRORS ===")
            print(stderr)
            
        return process.returncode == 0
        
    except subprocess.TimeoutExpired:
        print("❌ Download timed out after 5 minutes")
        process.kill()
        return False
    except Exception as e:
        print(f"❌ Error running downloader: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting automatic download...")
    print("📋 Method: 2 (Hybrid Speed Download)")
    print("📝 PO Number: 1284678")
    print("=" * 50)
    
    success = run_downloader()
    
    if success:
        print("✅ Download completed successfully!")
    else:
        print("❌ Download failed!")
