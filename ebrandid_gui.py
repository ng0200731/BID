"""
E-BrandID File Downloader - GUI Interface
Simple interface for downloading files from e-brandid PO pages.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import os
from datetime import datetime
from ebrandid_downloader import EBrandIDDownloader

class EBrandIDGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("E-BrandID File Downloader")
        self.root.geometry("600x500")
        self.root.resizable(True, True)
        
        # Variables
        self.download_path = tk.StringVar(value=os.getcwd())
        self.po_number = tk.StringVar(value="1288060")
        self.username = tk.StringVar(value="sales10@fuchanghk.com")
        self.password = tk.StringVar(value="fc31051856")
        self.show_browser = tk.BooleanVar(value=True)
        
        self.downloader = None
        self.download_thread = None
        
        self.create_interface()
        
    def create_interface(self):
        """Create the main interface"""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(main_frame, text="E-BrandID File Downloader", font=("Arial", 18, "bold"))
        title_label.pack(pady=(0, 20))
        
        # Description
        desc_label = ttk.Label(main_frame, text="Automatically download all files from an e-brandid PO page", font=("Arial", 10))
        desc_label.pack(pady=(0, 20))
        
        # PO Number input
        po_frame = ttk.LabelFrame(main_frame, text="PO Information", padding="10")
        po_frame.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Label(po_frame, text="PO Number:").pack(anchor=tk.W)
        po_entry = ttk.Entry(po_frame, textvariable=self.po_number, font=("Arial", 12))
        po_entry.pack(fill=tk.X, pady=(5, 0))
        
        # Login credentials
        login_frame = ttk.LabelFrame(main_frame, text="E-BrandID Login Credentials", padding="10")
        login_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Username
        ttk.Label(login_frame, text="Username:").pack(anchor=tk.W)
        username_entry = ttk.Entry(login_frame, textvariable=self.username, font=("Arial", 10))
        username_entry.pack(fill=tk.X, pady=(5, 10))
        
        # Password
        ttk.Label(login_frame, text="Password:").pack(anchor=tk.W)
        password_entry = ttk.Entry(login_frame, textvariable=self.password, show="*", font=("Arial", 10))
        password_entry.pack(fill=tk.X, pady=(5, 0))
        
        # Download settings
        settings_frame = ttk.LabelFrame(main_frame, text="Download Settings", padding="10")
        settings_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Download path
        path_frame = ttk.Frame(settings_frame)
        path_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(path_frame, text="Download Folder:").pack(anchor=tk.W)
        path_entry_frame = ttk.Frame(path_frame)
        path_entry_frame.pack(fill=tk.X, pady=(5, 0))
        
        path_entry = ttk.Entry(path_entry_frame, textvariable=self.download_path, font=("Arial", 9))
        path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        browse_btn = ttk.Button(path_entry_frame, text="Browse", command=self.browse_folder)
        browse_btn.pack(side=tk.RIGHT, padx=(10, 0))
        
        # Show browser option
        browser_check = ttk.Checkbutton(settings_frame, text="Show browser window (uncheck to run in background)", variable=self.show_browser)
        browser_check.pack(anchor=tk.W)
        
        # Control buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(20, 0))
        
        self.start_btn = ttk.Button(button_frame, text="Start Download", command=self.start_download, style="Accent.TButton")
        self.start_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.stop_btn = ttk.Button(button_frame, text="Stop", command=self.stop_download, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT)
        
        # Progress section
        self.progress_frame = ttk.LabelFrame(main_frame, text="Progress", padding="10")
        self.progress_frame.pack(fill=tk.X, pady=(20, 0))
        
        self.status_label = ttk.Label(self.progress_frame, text="Ready to start download...")
        self.status_label.pack(anchor=tk.W, pady=(0, 10))
        
        self.progress_bar = ttk.Progressbar(self.progress_frame, mode='indeterminate')
        self.progress_bar.pack(fill=tk.X, pady=(0, 10))
        
        # Log area
        log_frame = ttk.Frame(self.progress_frame)
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        self.log_text = tk.Text(log_frame, height=8, wrap=tk.WORD, font=("Consolas", 9))
        log_scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_scrollbar.set)
        
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Initial log message
        self.log_message("E-BrandID File Downloader ready.")
        self.log_message("Enter PO number and click 'Start Download' to begin.")
        
    def browse_folder(self):
        """Browse for download folder"""
        folder = filedialog.askdirectory(initialdir=self.download_path.get())
        if folder:
            self.download_path.set(folder)
    
    def log_message(self, message):
        """Add message to log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()
    
    def update_status(self, status):
        """Update status label"""
        self.status_label.config(text=status)
        self.root.update_idletasks()
    
    def start_download(self):
        """Start the download process"""
        # Validate inputs
        po_num = self.po_number.get().strip()
        username = self.username.get().strip()
        password = self.password.get().strip()
        
        if not po_num:
            messagebox.showerror("Error", "Please enter a PO number")
            return
        
        if not username or not password:
            messagebox.showerror("Error", "Please enter username and password")
            return
        
        # Update UI
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.progress_bar.start()
        
        # Clear log
        self.log_text.delete(1.0, tk.END)
        
        # Start download in separate thread
        self.download_thread = threading.Thread(target=self.download_worker, daemon=True)
        self.download_thread.start()
    
    def download_worker(self):
        """Worker thread for downloading"""
        try:
            po_num = self.po_number.get().strip()
            username = self.username.get().strip()
            password = self.password.get().strip()
            download_path = self.download_path.get()
            show_browser = not self.show_browser.get()  # Inverted for headless
            
            self.log_message(f"Starting download for PO: {po_num}")
            self.update_status("Initializing browser...")
            
            # Create downloader
            self.downloader = EBrandIDDownloader(headless=show_browser, download_path=download_path)
            
            # Run the complete process
            self.update_status("Milestone 1: Logging in...")
            self.log_message("Milestone 1: Attempting login to e-brandid...")
            
            success, message = self.downloader.run_complete_process(po_num, username, password)
            
            if success:
                self.log_message(f"✅ SUCCESS: {message}")
                self.update_status("Download completed successfully!")
                
                # Show completion message
                self.root.after(0, lambda: messagebox.showinfo("Success", 
                    f"Download completed!\n\nPO: {po_num}\nFiles saved to: {os.path.join(download_path, po_num)}"))
            else:
                self.log_message(f"❌ FAILED: {message}")
                self.update_status("Download failed!")
                
                # Show error message
                self.root.after(0, lambda: messagebox.showerror("Error", f"Download failed:\n{message}"))
            
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            self.log_message(f"❌ ERROR: {error_msg}")
            self.update_status("Error occurred!")
            
            # Show error message
            self.root.after(0, lambda: messagebox.showerror("Error", error_msg))
        
        finally:
            # Reset UI
            self.root.after(0, self.reset_ui)
    
    def stop_download(self):
        """Stop the download process"""
        if self.downloader:
            self.downloader.close_driver()
        
        self.log_message("Download stopped by user")
        self.update_status("Download stopped")
        self.reset_ui()
    
    def reset_ui(self):
        """Reset UI to initial state"""
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.progress_bar.stop()
    
    def run(self):
        """Start the application"""
        self.root.mainloop()


if __name__ == "__main__":
    app = EBrandIDGUI()
    app.run()
