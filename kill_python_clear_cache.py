#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Kill All Python Processes and Clear Cache
Completely cleans Python processes and cache files
"""

import os
import sys
import subprocess
import shutil
import glob
import time
from pathlib import Path

def kill_all_python_processes():
    """Kill all Python processes"""
    print("🔥 Killing all Python processes...")
    
    try:
        # Windows commands to kill Python processes
        commands = [
            'taskkill /F /IM python.exe',
            'taskkill /F /IM pythonw.exe',
            'taskkill /F /IM python3.exe',
            'taskkill /F /IM python3.11.exe'
        ]
        
        for cmd in commands:
            try:
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                if result.returncode == 0:
                    print(f"✅ {cmd} - Success")
                else:
                    print(f"⚠️ {cmd} - No processes found or already killed")
            except Exception as e:
                print(f"❌ Error with {cmd}: {e}")
                
    except Exception as e:
        print(f"❌ Error killing Python processes: {e}")

def clear_python_cache():
    """Clear Python cache files"""
    print("🧹 Clearing Python cache files...")
    
    # Current directory and subdirectories
    current_dir = Path.cwd()
    
    # Patterns to delete
    cache_patterns = [
        "**/__pycache__",
        "**/*.pyc",
        "**/*.pyo",
        "**/*.pyd",
        ".pytest_cache",
        "*.egg-info",
        "build",
        "dist"
    ]
    
    deleted_count = 0
    
    for pattern in cache_patterns:
        try:
            # Find all matching files/directories
            matches = list(current_dir.glob(pattern))
            
            for match in matches:
                try:
                    if match.is_file():
                        match.unlink()
                        deleted_count += 1
                        print(f"🗑️ Deleted file: {match}")
                    elif match.is_dir():
                        shutil.rmtree(match)
                        deleted_count += 1
                        print(f"🗑️ Deleted directory: {match}")
                except Exception as e:
                    print(f"⚠️ Could not delete {match}: {e}")
                    
        except Exception as e:
            print(f"❌ Error with pattern {pattern}: {e}")
    
    print(f"✅ Cleared {deleted_count} cache files/directories")

def clear_flask_cache():
    """Clear Flask-specific cache"""
    print("🌶️ Clearing Flask cache...")
    
    try:
        # Clear Flask session files if any
        temp_patterns = [
            "flask_session*",
            "*.tmp",
            "*.temp"
        ]
        
        current_dir = Path.cwd()
        deleted_count = 0
        
        for pattern in temp_patterns:
            matches = list(current_dir.glob(pattern))
            for match in matches:
                try:
                    if match.is_file():
                        match.unlink()
                        deleted_count += 1
                        print(f"🗑️ Deleted Flask temp: {match}")
                except Exception as e:
                    print(f"⚠️ Could not delete {match}: {e}")
        
        print(f"✅ Cleared {deleted_count} Flask cache files")
        
    except Exception as e:
        print(f"❌ Error clearing Flask cache: {e}")

def clear_browser_cache_instructions():
    """Show instructions to clear browser cache"""
    print("\n🌐 BROWSER CACHE CLEARING INSTRUCTIONS:")
    print("=" * 50)
    print("1. In Chrome: Press Ctrl+Shift+R (Hard Refresh)")
    print("2. Or: Press F12 → Right-click refresh button → 'Empty Cache and Hard Reload'")
    print("3. Or: Chrome Settings → Privacy → Clear browsing data → Cached images and files")
    print("4. Alternative: Open Incognito/Private window")
    print("=" * 50)

def restart_application():
    """Restart the application"""
    print("\n🚀 Restarting application...")
    
    try:
        # Wait a moment for processes to fully terminate
        time.sleep(2)
        
        # Start the application
        print("📱 Starting smart_app.py...")
        subprocess.Popen([sys.executable, "smart_app.py"], cwd=os.getcwd())
        
        print("✅ Application started!")
        print("🌐 Open browser to: http://127.0.0.1:5002")
        
    except Exception as e:
        print(f"❌ Error restarting application: {e}")
        print("💡 Please manually run: python smart_app.py")

def main():
    """Main function"""
    print("=" * 60)
    print("🔥 PYTHON PROCESS KILLER & CACHE CLEANER")
    print("=" * 60)
    print("This will:")
    print("1. Kill all Python processes")
    print("2. Clear Python cache files (__pycache__, *.pyc)")
    print("3. Clear Flask temporary files")
    print("4. Restart the application")
    print("=" * 60)
    
    # Confirm before proceeding
    response = input("Continue? (y/N): ").strip().lower()
    if response != 'y':
        print("❌ Cancelled by user")
        return
    
    # Step 1: Kill Python processes
    kill_all_python_processes()
    
    # Step 2: Clear Python cache
    clear_python_cache()
    
    # Step 3: Clear Flask cache
    clear_flask_cache()
    
    # Step 4: Browser cache instructions
    clear_browser_cache_instructions()
    
    # Step 5: Restart application
    restart_application()
    
    print("\n" + "=" * 60)
    print("🎉 CLEANUP COMPLETE!")
    print("✅ All Python processes killed")
    print("✅ All cache files cleared")
    print("✅ Application restarted")
    print("🌐 Check browser at: http://127.0.0.1:5002")
    print("💡 Use Ctrl+Shift+R for hard refresh in browser")
    print("=" * 60)

if __name__ == "__main__":
    main()
