"""
Web Crawler Application
A desktop application for crawling web information with user authentication.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import hashlib
import os
import threading
from datetime import datetime

class WebCrawlerApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Web Crawler Pro")
        self.root.geometry("800x600")
        self.root.resizable(True, True)
        
        # Initialize database
        self.init_database()
        
        # Current user
        self.current_user = None
        
        # Create login interface
        self.create_login_interface()
        
    def init_database(self):
        """Initialize SQLite database for users and crawled data"""
        self.conn = sqlite3.connect('webcrawler.db')
        self.cursor = self.conn.cursor()
        
        # Create users table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create crawl_jobs table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS crawl_jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                url TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Create crawled_data table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS crawled_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id INTEGER,
                url TEXT NOT NULL,
                title TEXT,
                content TEXT,
                crawled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (job_id) REFERENCES crawl_jobs (id)
            )
        ''')
        
        self.conn.commit()
    
    def hash_password(self, password):
        """Hash password using SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def create_login_interface(self):
        """Create the login/registration interface"""
        # Clear the window
        for widget in self.root.winfo_children():
            widget.destroy()
            
        # Main frame
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, text="Web Crawler Pro", font=("Arial", 24, "bold"))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 30))
        
        # Username
        ttk.Label(main_frame, text="Username:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.username_entry = ttk.Entry(main_frame, width=30)
        self.username_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5)
        
        # Password
        ttk.Label(main_frame, text="Password:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.password_entry = ttk.Entry(main_frame, width=30, show="*")
        self.password_entry.grid(row=2, column=1, sticky=(tk.W, tk.E), pady=5)
        
        # Buttons frame
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.grid(row=3, column=0, columnspan=2, pady=20)
        
        # Login button
        login_btn = ttk.Button(buttons_frame, text="Login", command=self.login)
        login_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Register button
        register_btn = ttk.Button(buttons_frame, text="Register", command=self.register)
        register_btn.pack(side=tk.LEFT)
        
        # Bind Enter key to login
        self.root.bind('<Return>', lambda event: self.login())
        
        # Focus on username entry
        self.username_entry.focus()
    
    def login(self):
        """Handle user login"""
        username = self.username_entry.get().strip()
        password = self.password_entry.get()
        
        if not username or not password:
            messagebox.showerror("Error", "Please enter both username and password")
            return
        
        password_hash = self.hash_password(password)
        
        self.cursor.execute(
            "SELECT id, username FROM users WHERE username = ? AND password_hash = ?",
            (username, password_hash)
        )
        user = self.cursor.fetchone()
        
        if user:
            self.current_user = {"id": user[0], "username": user[1]}
            messagebox.showinfo("Success", f"Welcome back, {username}!")
            self.create_main_interface()
        else:
            messagebox.showerror("Error", "Invalid username or password")
    
    def register(self):
        """Handle user registration"""
        username = self.username_entry.get().strip()
        password = self.password_entry.get()
        
        if not username or not password:
            messagebox.showerror("Error", "Please enter both username and password")
            return
        
        if len(password) < 6:
            messagebox.showerror("Error", "Password must be at least 6 characters long")
            return
        
        password_hash = self.hash_password(password)
        
        try:
            self.cursor.execute(
                "INSERT INTO users (username, password_hash) VALUES (?, ?)",
                (username, password_hash)
            )
            self.conn.commit()
            messagebox.showinfo("Success", "Account created successfully! You can now login.")
            self.password_entry.delete(0, tk.END)
        except sqlite3.IntegrityError:
            messagebox.showerror("Error", "Username already exists")
    
    def create_main_interface(self):
        """Create the main crawler interface"""
        # Import crawler here to avoid circular imports
        from crawler import WebCrawler, CrawlerThread

        # Initialize crawler
        self.crawler = WebCrawler(self.conn)

        # Clear the window
        for widget in self.root.winfo_children():
            widget.destroy()

        # Create notebook for tabs
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Create tabs
        self.create_crawler_tab(notebook)
        self.create_jobs_tab(notebook)
        self.create_data_tab(notebook)

        # Add logout button
        logout_frame = ttk.Frame(self.root)
        logout_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        user_label = ttk.Label(logout_frame, text=f"Logged in as: {self.current_user['username']}")
        user_label.pack(side=tk.LEFT)

        logout_btn = ttk.Button(logout_frame, text="Logout", command=self.logout)
        logout_btn.pack(side=tk.RIGHT)

    def create_crawler_tab(self, notebook):
        """Create the main crawler tab"""
        crawler_frame = ttk.Frame(notebook)
        notebook.add(crawler_frame, text="New Crawl")

        # Main container with padding
        main_container = ttk.Frame(crawler_frame, padding="20")
        main_container.pack(fill=tk.BOTH, expand=True)

        # Title
        title_label = ttk.Label(main_container, text="Start New Web Crawl", font=("Arial", 16, "bold"))
        title_label.pack(pady=(0, 20))

        # URL input
        url_frame = ttk.LabelFrame(main_container, text="Target URL", padding="10")
        url_frame.pack(fill=tk.X, pady=(0, 15))

        self.url_entry = ttk.Entry(url_frame, font=("Arial", 11))
        self.url_entry.pack(fill=tk.X)
        self.url_entry.insert(0, "https://app.e-brandid.com/login/login.aspx")

        # Login credentials (for websites that require login)
        login_frame = ttk.LabelFrame(main_container, text="Website Login Credentials (Optional)", padding="10")
        login_frame.pack(fill=tk.X, pady=(0, 15))

        # Username
        username_frame = ttk.Frame(login_frame)
        username_frame.pack(fill=tk.X, pady=(0, 5))
        ttk.Label(username_frame, text="Username:").pack(side=tk.LEFT)
        self.website_username_entry = ttk.Entry(username_frame, width=30)
        self.website_username_entry.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(10, 0))

        # Password
        password_frame = ttk.Frame(login_frame)
        password_frame.pack(fill=tk.X, pady=(0, 5))
        ttk.Label(password_frame, text="Password:").pack(side=tk.LEFT)
        self.website_password_entry = ttk.Entry(password_frame, width=30, show="*")
        self.website_password_entry.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(10, 0))

        # Info label
        info_label = ttk.Label(login_frame, text="Leave blank if the website doesn't require login", font=("Arial", 9))
        info_label.pack(anchor=tk.W, pady=(5, 0))

        # Options frame
        options_frame = ttk.LabelFrame(main_container, text="Crawl Options", padding="10")
        options_frame.pack(fill=tk.X, pady=(0, 15))

        # Max depth
        depth_frame = ttk.Frame(options_frame)
        depth_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(depth_frame, text="Max Depth:").pack(side=tk.LEFT)
        self.depth_var = tk.StringVar(value="2")
        depth_spinbox = ttk.Spinbox(depth_frame, from_=0, to=5, width=10, textvariable=self.depth_var)
        depth_spinbox.pack(side=tk.RIGHT)

        # Delay
        delay_frame = ttk.Frame(options_frame)
        delay_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(delay_frame, text="Delay (seconds):").pack(side=tk.LEFT)
        self.delay_var = tk.StringVar(value="1")
        delay_spinbox = ttk.Spinbox(delay_frame, from_=0, to=10, width=10, textvariable=self.delay_var)
        delay_spinbox.pack(side=tk.RIGHT)

        # Same domain only
        self.same_domain_var = tk.BooleanVar(value=True)
        same_domain_check = ttk.Checkbutton(options_frame, text="Same domain only", variable=self.same_domain_var)
        same_domain_check.pack(anchor=tk.W)

        # Advanced options
        advanced_frame = ttk.LabelFrame(main_container, text="Advanced Options", padding="10")
        advanced_frame.pack(fill=tk.X, pady=(0, 15))

        # JavaScript support
        self.javascript_var = tk.BooleanVar(value=False)
        js_check = ttk.Checkbutton(advanced_frame, text="Enable JavaScript support (slower but handles dynamic content)", variable=self.javascript_var)
        js_check.pack(anchor=tk.W, pady=(0, 5))

        # Click elements
        self.click_elements_var = tk.BooleanVar(value=False)
        click_check = ttk.Checkbutton(advanced_frame, text="Click on buttons and links (interactive crawling)", variable=self.click_elements_var)
        click_check.pack(anchor=tk.W, pady=(0, 5))

        # Export options
        export_frame = ttk.LabelFrame(main_container, text="Export Options", padding="10")
        export_frame.pack(fill=tk.X, pady=(0, 15))

        export_btn_frame = ttk.Frame(export_frame)
        export_btn_frame.pack(fill=tk.X)

        ttk.Button(export_btn_frame, text="Export to TXT", command=self.export_to_txt).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(export_btn_frame, text="Export to JSON", command=self.export_to_json).pack(side=tk.LEFT)

        # Start crawl button
        start_btn = ttk.Button(main_container, text="Start Crawling", command=self.start_crawl, style="Accent.TButton")
        start_btn.pack(pady=20)

        # Progress frame
        self.progress_frame = ttk.LabelFrame(main_container, text="Progress", padding="10")
        self.progress_frame.pack(fill=tk.X, pady=(0, 15))
        self.progress_frame.pack_forget()  # Hide initially

        self.progress_label = ttk.Label(self.progress_frame, text="Ready to crawl...")
        self.progress_label.pack()

        self.progress_bar = ttk.Progressbar(self.progress_frame, mode='indeterminate')
        self.progress_bar.pack(fill=tk.X, pady=(10, 0))

    def create_jobs_tab(self, notebook):
        """Create the jobs history tab"""
        jobs_frame = ttk.Frame(notebook)
        notebook.add(jobs_frame, text="Crawl Jobs")

        # Container with padding
        container = ttk.Frame(jobs_frame, padding="20")
        container.pack(fill=tk.BOTH, expand=True)

        # Title and refresh button
        header_frame = ttk.Frame(container)
        header_frame.pack(fill=tk.X, pady=(0, 15))

        ttk.Label(header_frame, text="Crawl Jobs History", font=("Arial", 16, "bold")).pack(side=tk.LEFT)
        ttk.Button(header_frame, text="Refresh", command=self.refresh_jobs).pack(side=tk.RIGHT)

        # Jobs treeview
        columns = ("ID", "URL", "Status", "Created", "Completed")
        self.jobs_tree = ttk.Treeview(container, columns=columns, show="headings", height=15)

        # Configure columns
        self.jobs_tree.heading("ID", text="ID")
        self.jobs_tree.heading("URL", text="URL")
        self.jobs_tree.heading("Status", text="Status")
        self.jobs_tree.heading("Created", text="Created")
        self.jobs_tree.heading("Completed", text="Completed")

        self.jobs_tree.column("ID", width=50)
        self.jobs_tree.column("URL", width=300)
        self.jobs_tree.column("Status", width=100)
        self.jobs_tree.column("Created", width=150)
        self.jobs_tree.column("Completed", width=150)

        # Scrollbar for jobs tree
        jobs_scrollbar = ttk.Scrollbar(container, orient=tk.VERTICAL, command=self.jobs_tree.yview)
        self.jobs_tree.configure(yscrollcommand=jobs_scrollbar.set)

        # Pack treeview and scrollbar
        self.jobs_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        jobs_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Bind double-click to view job data
        self.jobs_tree.bind("<Double-1>", self.view_job_data)

    def create_data_tab(self, notebook):
        """Create the crawled data tab"""
        data_frame = ttk.Frame(notebook)
        notebook.add(data_frame, text="Crawled Data")

        # Container with padding
        container = ttk.Frame(data_frame, padding="20")
        container.pack(fill=tk.BOTH, expand=True)

        # Title
        ttk.Label(container, text="Crawled Data Viewer", font=("Arial", 16, "bold")).pack(pady=(0, 15))

        # Data display area
        self.data_text = tk.Text(container, wrap=tk.WORD, font=("Consolas", 10))
        data_scrollbar = ttk.Scrollbar(container, orient=tk.VERTICAL, command=self.data_text.yview)
        self.data_text.configure(yscrollcommand=data_scrollbar.set)

        self.data_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        data_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Initially show instructions
        self.data_text.insert(tk.END, "Double-click on a job in the 'Crawl Jobs' tab to view its data here.")
        self.data_text.config(state=tk.DISABLED)

    def start_crawl(self):
        """Start a new crawl job"""
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showerror("Error", "Please enter a URL to crawl")
            return

        try:
            max_depth = int(self.depth_var.get())
            delay = float(self.delay_var.get())
        except ValueError:
            messagebox.showerror("Error", "Invalid depth or delay value")
            return

        same_domain_only = self.same_domain_var.get()
        use_javascript = self.javascript_var.get()
        click_elements = self.click_elements_var.get()

        # Get login credentials
        website_username = self.website_username_entry.get().strip()
        website_password = self.website_password_entry.get().strip()
        needs_login = bool(website_username and website_password)

        # Create new job in database
        job_id = self.crawler.save_crawl_job(self.current_user['id'], url)

        # Show progress
        self.progress_frame.pack(fill=tk.X, pady=(0, 15))

        if needs_login:
            self.progress_label.config(text=f"Starting login crawl of {url} (with credentials)...")
            # Import login crawler
            try:
                from login_crawler import LoginWebCrawler
                login_crawler = LoginWebCrawler(self.conn, headless=True)

                # Start login crawler thread
                crawler_thread = LoginCrawlerThread(
                    login_crawler, job_id, url, website_username, website_password,
                    max_depth, delay, callback=self.crawl_completed
                )
            except ImportError as e:
                messagebox.showerror("Error", f"Login crawler not available: {e}")
                return
        elif use_javascript:
            self.progress_label.config(text=f"Starting advanced crawl of {url} (with JavaScript)...")
            # Import advanced crawler
            try:
                from advanced_crawler import AdvancedWebCrawler
                advanced_crawler = AdvancedWebCrawler(self.conn, headless=True)

                # Start advanced crawler thread
                crawler_thread = AdvancedCrawlerThread(
                    advanced_crawler, job_id, url, max_depth, delay, same_domain_only,
                    click_elements, callback=self.crawl_completed
                )
            except ImportError as e:
                messagebox.showerror("Error", f"Advanced crawler not available: {e}")
                return
        else:
            self.progress_label.config(text=f"Starting basic crawl of {url}...")
            # Start basic crawler thread
            crawler_thread = CrawlerThread(
                self.crawler, job_id, url, max_depth, delay, same_domain_only,
                callback=self.crawl_completed
            )

        self.progress_bar.start()
        crawler_thread.start()

    def crawl_completed(self, job_id, status, result):
        """Callback when crawl is completed"""
        self.progress_bar.stop()

        if status == 'completed':
            self.progress_label.config(text=f"Crawl completed! Found {result} pages.")
            messagebox.showinfo("Success", f"Crawl completed successfully!\nCrawled {result} pages.")
        else:
            self.progress_label.config(text=f"Crawl failed: {result}")
            messagebox.showerror("Error", f"Crawl failed: {result}")

        # Refresh jobs list
        self.refresh_jobs()

        # Hide progress after a delay
        self.root.after(3000, lambda: self.progress_frame.pack_forget())

    def refresh_jobs(self):
        """Refresh the jobs list"""
        # Clear existing items
        for item in self.jobs_tree.get_children():
            self.jobs_tree.delete(item)

        # Get jobs from database
        jobs = self.crawler.get_user_jobs(self.current_user['id'])

        for job in jobs:
            job_id, url, status, created_at, completed_at = job

            # Format dates
            created_str = created_at[:19] if created_at else ""
            completed_str = completed_at[:19] if completed_at else ""

            # Truncate URL if too long
            display_url = url if len(url) <= 50 else url[:47] + "..."

            self.jobs_tree.insert("", tk.END, values=(
                job_id, display_url, status, created_str, completed_str
            ))

    def view_job_data(self, event):
        """View data for selected job"""
        selection = self.jobs_tree.selection()
        if not selection:
            return

        item = self.jobs_tree.item(selection[0])
        job_id = item['values'][0]

        # Get job data
        job_data = self.crawler.get_job_data(job_id)

        # Clear and populate data text widget
        self.data_text.config(state=tk.NORMAL)
        self.data_text.delete(1.0, tk.END)

        if not job_data:
            self.data_text.insert(tk.END, "No data found for this job.")
        else:
            for i, (url, title, content, crawled_at) in enumerate(job_data, 1):
                self.data_text.insert(tk.END, f"=== Page {i} ===\n")
                self.data_text.insert(tk.END, f"URL: {url}\n")
                self.data_text.insert(tk.END, f"Title: {title}\n")
                self.data_text.insert(tk.END, f"Crawled: {crawled_at}\n")
                self.data_text.insert(tk.END, f"Content:\n{content}\n\n")
                self.data_text.insert(tk.END, "-" * 80 + "\n\n")

        self.data_text.config(state=tk.DISABLED)

        # Switch to data tab
        notebook = self.data_text.master.master.master  # Navigate up to notebook
        notebook.select(2)  # Select data tab (index 2)

    def export_to_txt(self):
        """Export crawled data to text file"""
        try:
            from tkinter import filedialog

            # Get all user's jobs
            jobs = self.crawler.get_user_jobs(self.current_user['id'])

            if not jobs:
                messagebox.showinfo("Info", "No crawl data to export")
                return

            # Ask user to select save location
            filename = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
                title="Save crawled data as..."
            )

            if filename:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(f"Web Crawler Pro - Export Report\n")
                    f.write(f"User: {self.current_user['username']}\n")
                    f.write(f"Export Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write("=" * 80 + "\n\n")

                    for job in jobs:
                        job_id, url, status, created_at, completed_at = job
                        f.write(f"Job ID: {job_id}\n")
                        f.write(f"URL: {url}\n")
                        f.write(f"Status: {status}\n")
                        f.write(f"Created: {created_at}\n")
                        f.write(f"Completed: {completed_at}\n")
                        f.write("-" * 40 + "\n")

                        # Get job data
                        job_data = self.crawler.get_job_data(job_id)
                        for page_url, title, content, crawled_at in job_data:
                            f.write(f"Page URL: {page_url}\n")
                            f.write(f"Title: {title}\n")
                            f.write(f"Content:\n{content}\n")
                            f.write("-" * 20 + "\n")

                        f.write("\n" + "=" * 80 + "\n\n")

                messagebox.showinfo("Success", f"Data exported to {filename}")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to export data: {e}")

    def export_to_json(self):
        """Export crawled data to JSON file"""
        try:
            import json
            from tkinter import filedialog

            # Get all user's jobs
            jobs = self.crawler.get_user_jobs(self.current_user['id'])

            if not jobs:
                messagebox.showinfo("Info", "No crawl data to export")
                return

            # Ask user to select save location
            filename = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
                title="Save crawled data as..."
            )

            if filename:
                export_data = {
                    "user": self.current_user['username'],
                    "export_date": datetime.now().isoformat(),
                    "jobs": []
                }

                for job in jobs:
                    job_id, url, status, created_at, completed_at = job
                    job_data = self.crawler.get_job_data(job_id)

                    job_info = {
                        "job_id": job_id,
                        "url": url,
                        "status": status,
                        "created_at": created_at,
                        "completed_at": completed_at,
                        "pages": []
                    }

                    for page_url, title, content, crawled_at in job_data:
                        page_info = {
                            "url": page_url,
                            "title": title,
                            "content": content,
                            "crawled_at": crawled_at
                        }
                        job_info["pages"].append(page_info)

                    export_data["jobs"].append(job_info)

                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(export_data, f, indent=2, ensure_ascii=False)

                messagebox.showinfo("Success", f"Data exported to {filename}")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to export data: {e}")

    def logout(self):
        """Logout current user"""
        self.current_user = None
        self.create_login_interface()

    def run(self):
        """Start the application"""
        self.root.mainloop()
        self.conn.close()

class LoginCrawlerThread(threading.Thread):
    """Thread class for running login crawler in background"""

    def __init__(self, crawler, job_id, url, username, password, max_depth=2, delay=1, callback=None):
        threading.Thread.__init__(self)
        self.crawler = crawler
        self.job_id = job_id
        self.url = url
        self.username = username
        self.password = password
        self.max_depth = max_depth
        self.delay = delay
        self.callback = callback
        self.daemon = True

    def run(self):
        """Run the login crawler in background"""
        try:
            # Update job status to running
            self.crawler.update_job_status(self.job_id, 'running')

            # Perform the login crawl
            results = self.crawler.crawl_with_login(
                login_url=self.url,
                username=self.username,
                password=self.password,
                crawl_urls=None,
                max_depth=self.max_depth,
                delay=self.delay
            )

            # Check if results is an error
            if isinstance(results, dict) and 'error' in results:
                self.crawler.update_job_status(self.job_id, 'failed')
                if self.callback:
                    self.callback(self.job_id, 'failed', results['error'])
                return

            # Save results to database
            for page_data in results:
                self.crawler.save_crawled_data(self.job_id, page_data)

            # Update job status to completed
            self.crawler.update_job_status(self.job_id, 'completed')

            # Call callback if provided
            if self.callback:
                self.callback(self.job_id, 'completed', len(results))

        except Exception as e:
            # Update job status to failed
            self.crawler.update_job_status(self.job_id, 'failed')

            # Call callback if provided
            if self.callback:
                self.callback(self.job_id, 'failed', str(e))


class AdvancedCrawlerThread(threading.Thread):
    """Thread class for running advanced crawler in background"""

    def __init__(self, crawler, job_id, url, max_depth=2, delay=1, same_domain_only=True,
                 click_elements=False, callback=None):
        threading.Thread.__init__(self)
        self.crawler = crawler
        self.job_id = job_id
        self.url = url
        self.max_depth = max_depth
        self.delay = delay
        self.same_domain_only = same_domain_only
        self.click_elements = click_elements
        self.callback = callback
        self.daemon = True

    def run(self):
        """Run the advanced crawler in background"""
        try:
            # Update job status to running
            self.crawler.update_job_status(self.job_id, 'running')

            # Perform the advanced crawl
            results = self.crawler.crawl_page_advanced(
                self.url,
                max_depth=self.max_depth,
                delay=self.delay,
                same_domain_only=self.same_domain_only,
                click_elements=self.click_elements,
                wait_for_load=3
            )

            # Check if results is an error
            if isinstance(results, dict) and 'error' in results:
                self.crawler.update_job_status(self.job_id, 'failed')
                if self.callback:
                    self.callback(self.job_id, 'failed', results['error'])
                return

            # Save results to database
            for page_data in results:
                self.crawler.save_crawled_data(self.job_id, page_data)

            # Update job status to completed
            self.crawler.update_job_status(self.job_id, 'completed')

            # Call callback if provided
            if self.callback:
                self.callback(self.job_id, 'completed', len(results))

        except Exception as e:
            # Update job status to failed
            self.crawler.update_job_status(self.job_id, 'failed')

            # Call callback if provided
            if self.callback:
                self.callback(self.job_id, 'failed', str(e))


if __name__ == "__main__":
    app = WebCrawlerApp()
    app.run()
