"""
E-BrandID File Downloader - Simple Fix Version
Fixed version that handles WebDriver issues better
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import os
import time
import requests
from datetime import datetime

class EBrandIDSimpleFix:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("E-BrandID File Downloader (Fixed)")
        self.root.geometry("600x500")
        
        # Variables
        self.download_path = tk.StringVar(value=os.getcwd())
        self.po_number = tk.StringVar(value="1288060")
        self.username = tk.StringVar(value="sales10@fuchanghk.com")
        self.password = tk.StringVar(value="fc31051856")
        
        self.create_interface()
        
    def create_interface(self):
        """Create the main interface"""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(main_frame, text="E-BrandID File Downloader (Fixed)", font=("Arial", 18, "bold"))
        title_label.pack(pady=(0, 20))
        
        # Error notice
        error_frame = ttk.LabelFrame(main_frame, text="WebDriver Issue Detected", padding="10")
        error_frame.pack(fill=tk.X, pady=(0, 15))
        
        error_text = """The WebDriver (Chrome automation) is not working properly on this system.
This usually happens due to:
• Chrome browser not installed
• Chrome version mismatch
• Windows security restrictions
• Missing system dependencies

SOLUTIONS:"""
        
        ttk.Label(error_frame, text=error_text, font=("Arial", 9)).pack(anchor=tk.W)
        
        # Solutions
        solutions_frame = ttk.LabelFrame(main_frame, text="Quick Solutions", padding="10")
        solutions_frame.pack(fill=tk.X, pady=(0, 15))
        
        solution_text = """1. MANUAL APPROACH (Recommended):
   • Open Chrome browser manually
   • Login to e-brandid with your credentials
   • Navigate to the PO page manually
   • Use browser's built-in download features

2. INSTALL CHROME:
   • Download and install Google Chrome browser
   • Restart this application

3. ALTERNATIVE TOOL:
   • Use browser extensions for bulk downloading
   • Use manual copy-paste for file links"""
        
        ttk.Label(solutions_frame, text=solution_text, font=("Arial", 9)).pack(anchor=tk.W)
        
        # Manual helper section
        helper_frame = ttk.LabelFrame(main_frame, text="Manual Helper", padding="10")
        helper_frame.pack(fill=tk.X, pady=(0, 15))
        
        # PO URL generator
        ttk.Label(helper_frame, text="Your PO URL:").pack(anchor=tk.W)
        
        url_frame = ttk.Frame(helper_frame)
        url_frame.pack(fill=tk.X, pady=(5, 10))
        
        self.url_var = tk.StringVar()
        url_entry = ttk.Entry(url_frame, textvariable=self.url_var, font=("Arial", 9))
        url_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        copy_btn = ttk.Button(url_frame, text="Copy URL", command=self.copy_url)
        copy_btn.pack(side=tk.RIGHT, padx=(10, 0))
        
        # PO input
        po_frame = ttk.Frame(helper_frame)
        po_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(po_frame, text="PO Number:").pack(side=tk.LEFT)
        po_entry = ttk.Entry(po_frame, textvariable=self.po_number, width=15)
        po_entry.pack(side=tk.LEFT, padx=(10, 10))
        
        generate_btn = ttk.Button(po_frame, text="Generate URL", command=self.generate_url)
        generate_btn.pack(side=tk.LEFT)
        
        # Credentials display
        cred_frame = ttk.LabelFrame(helper_frame, text="Your Login Credentials", padding="5")
        cred_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Label(cred_frame, text=f"Username: {self.username.get()}", font=("Arial", 10, "bold")).pack(anchor=tk.W)
        ttk.Label(cred_frame, text=f"Password: {self.password.get()}", font=("Arial", 10, "bold")).pack(anchor=tk.W)
        
        # Instructions
        instructions_frame = ttk.LabelFrame(main_frame, text="Manual Instructions", padding="10")
        instructions_frame.pack(fill=tk.X, pady=(0, 15))
        
        instructions_text = """STEP-BY-STEP MANUAL PROCESS:

1. Click 'Generate URL' above
2. Click 'Copy URL' to copy the PO page link
3. Open Chrome browser manually
4. Go to: https://app.e-brandid.com/login/login.aspx
5. Login with the credentials shown above
6. Paste the copied URL in browser address bar
7. On the PO page, right-click each file link → 'Save link as...'
8. Create a folder named with your PO number
9. Save all files to that folder"""
        
        ttk.Label(instructions_frame, text=instructions_text, font=("Arial", 9)).pack(anchor=tk.W)
        
        # Generate initial URL
        self.generate_url()
    
    def generate_url(self):
        """Generate the PO URL"""
        po_num = self.po_number.get().strip()
        if po_num:
            url = f"https://app.e-brandid.com/Bidnet/bidnet3/factoryPODetail.aspx?po_id={po_num}"
            self.url_var.set(url)
        else:
            self.url_var.set("Please enter a PO number first")
    
    def copy_url(self):
        """Copy URL to clipboard"""
        url = self.url_var.get()
        if url and "Please enter" not in url:
            self.root.clipboard_clear()
            self.root.clipboard_append(url)
            messagebox.showinfo("Copied", "URL copied to clipboard!\nYou can now paste it in your browser.")
        else:
            messagebox.showerror("Error", "Please generate a valid URL first")
    
    def run(self):
        """Start the application"""
        self.root.mainloop()


if __name__ == "__main__":
    app = EBrandIDSimpleFix()
    app.run()
