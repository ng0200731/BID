#!/usr/bin/env python
# Simple script to run the Flask app
import subprocess
import sys
import os

# Change to the script directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Run the smart_app.py
try:
    subprocess.run([sys.executable, "smart_app.py"], check=True)
except KeyboardInterrupt:
    print("\nApp stopped by user")
except Exception as e:
    print(f"Error running app: {e}")
    input("Press Enter to exit...")
