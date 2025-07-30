# Web Crawler Pro - Customization Guide

## Interface Customization

### 1. Changing Colors and Themes

**Location**: `main.py` - in the `__init__` method

```python
# Add after self.root.geometry("800x600")
self.root.configure(bg='#2b2b2b')  # Dark background

# Configure ttk styles
style = ttk.Style()
style.theme_use('clam')  # Options: 'clam', 'alt', 'default', 'classic'

# Custom colors
style.configure('TLabel', background='#2b2b2b', foreground='white')
style.configure('TFrame', background='#2b2b2b')
style.configure('TButton', background='#4a4a4a', foreground='white')
```

### 2. Changing Window Size and Title

**Location**: `main.py` - in the `__init__` method

```python
self.root.title("Your Custom Crawler Name")
self.root.geometry("1000x700")  # Width x Height
self.root.minsize(600, 400)     # Minimum size
```

### 3. Adding Your Logo/Icon

**Steps**:
1. Save your icon as `icon.ico` in the project folder
2. Add to `main.py` in `__init__`:

```python
try:
    self.root.iconbitmap('icon.ico')
except:
    pass  # Icon file not found, continue without it
```

### 4. Customizing Default Values

**Location**: `main.py` - in `create_crawler_tab` method

```python
# Change default URL
self.url_entry.insert(0, "https://your-default-site.com")

# Change default depth
self.depth_var = tk.StringVar(value="3")  # Default depth 3

# Change default delay
self.delay_var = tk.StringVar(value="2")  # Default 2 seconds

# Enable JavaScript by default
self.javascript_var = tk.BooleanVar(value=True)
```

## Crawler Settings Customization

### 1. Default Crawler Behavior

**Location**: `crawler.py` - in `crawl_page` method

```python
# Change default user agent
self.session.headers.update({
    'User-Agent': 'Your Custom Bot 1.0'
})

# Change timeout
response = self.session.get(current_url, timeout=30)  # 30 seconds

# Change content limit
if len(content) > 10000:  # Increase from 5000 to 10000
    content = content[:10000] + "..."
```

### 2. Advanced Crawler Settings

**Location**: `advanced_crawler.py` - in `setup_driver` method

```python
# Change browser window size
chrome_options.add_argument("--window-size=1920,1080")

# Add more Chrome options
chrome_options.add_argument("--disable-images")  # Faster loading
chrome_options.add_argument("--disable-javascript")  # If you don't need JS
chrome_options.add_argument("--incognito")  # Private browsing
```

### 3. Database Customization

**Location**: `main.py` - in `init_database` method

Add custom fields to store more data:

```python
# Add to crawled_data table
self.cursor.execute('''
    CREATE TABLE IF NOT EXISTS crawled_data (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        job_id INTEGER,
        url TEXT NOT NULL,
        title TEXT,
        content TEXT,
        meta_description TEXT,  -- NEW FIELD
        word_count INTEGER,     -- NEW FIELD
        image_count INTEGER,    -- NEW FIELD
        crawled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (job_id) REFERENCES crawl_jobs (id)
    )
''')
```

## Adding New Features

### 1. Adding a Search Function

**Location**: `main.py` - in `create_data_tab` method

Add search functionality:

```python
# Add search frame
search_frame = ttk.Frame(container)
search_frame.pack(fill=tk.X, pady=(0, 10))

ttk.Label(search_frame, text="Search:").pack(side=tk.LEFT)
self.search_entry = ttk.Entry(search_frame)
self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 5))
ttk.Button(search_frame, text="Search", command=self.search_data).pack(side=tk.RIGHT)
```

Then add the search method:

```python
def search_data(self):
    """Search through crawled data"""
    search_term = self.search_entry.get().strip().lower()
    if not search_term:
        return
    
    # Search in database
    self.cursor.execute("""
        SELECT url, title, content FROM crawled_data 
        WHERE LOWER(content) LIKE ? OR LOWER(title) LIKE ?
    """, (f'%{search_term}%', f'%{search_term}%'))
    
    results = self.cursor.fetchall()
    
    # Display results
    self.data_text.config(state=tk.NORMAL)
    self.data_text.delete(1.0, tk.END)
    
    if results:
        self.data_text.insert(tk.END, f"Search Results for '{search_term}':\n\n")
        for url, title, content in results:
            self.data_text.insert(tk.END, f"URL: {url}\n")
            self.data_text.insert(tk.END, f"Title: {title}\n")
            self.data_text.insert(tk.END, f"Content: {content[:200]}...\n")
            self.data_text.insert(tk.END, "-" * 50 + "\n\n")
    else:
        self.data_text.insert(tk.END, f"No results found for '{search_term}'")
    
    self.data_text.config(state=tk.DISABLED)
```

### 2. Adding Email Export

Add to the export functions:

```python
def export_to_email(self):
    """Send crawled data via email"""
    import smtplib
    from email.mime.text import MimeText
    from email.mime.multipart import MimeMultipart
    
    # Email configuration dialog
    email_dialog = tk.Toplevel(self.root)
    email_dialog.title("Email Export")
    email_dialog.geometry("400x300")
    
    # Add email form fields here
    # Implementation depends on your email service
```

### 3. Adding Scheduled Crawling

```python
def schedule_crawl(self):
    """Schedule a crawl to run at specific times"""
    import schedule
    import time
    
    # Add scheduling logic
    schedule.every().day.at("09:00").do(self.auto_crawl)
    
    # Run in background thread
    def run_scheduler():
        while True:
            schedule.run_pending()
            time.sleep(60)
    
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()
```

## Building Custom Executable

### 1. Custom Build Script

Create `custom_build.py`:

```python
import subprocess
import os

def build_custom():
    cmd = [
        'pyinstaller',
        '--onefile',
        '--windowed',
        '--name=YourCustomName',
        '--icon=your_icon.ico',
        '--add-data=custom_config.json;.',
        'main.py'
    ]
    
    subprocess.run(cmd)

if __name__ == "__main__":
    build_custom()
```

### 2. Including Custom Files

To include configuration files, images, or other resources:

```python
# In build script
'--add-data=config.json;.',
'--add-data=images;images',
'--add-data=templates;templates'
```

## Configuration File

Create `config.json` for easy customization:

```json
{
    "app_name": "Your Crawler Pro",
    "default_url": "https://example.com",
    "default_depth": 2,
    "default_delay": 1,
    "max_content_length": 10000,
    "enable_javascript": false,
    "theme": "dark",
    "window_size": "1000x700"
}
```

Then load it in `main.py`:

```python
import json

def load_config(self):
    try:
        with open('config.json', 'r') as f:
            self.config = json.load(f)
    except:
        self.config = {
            "app_name": "Web Crawler Pro",
            "default_url": "https://example.com",
            # ... default values
        }

# Use config values
self.root.title(self.config["app_name"])
self.root.geometry(self.config["window_size"])
```

## Tips for Customization

1. **Test thoroughly** after each change
2. **Keep backups** of working versions
3. **Use version control** (git) to track changes
4. **Document your changes** for future reference
5. **Test the executable** after building

## Common Customization Requests

- **Company branding**: Change colors, logo, app name
- **Default settings**: Modify default URLs, delays, depths
- **Additional export formats**: PDF, Excel, CSV
- **Custom data extraction**: Specific HTML elements
- **Integration**: APIs, databases, other tools
- **Scheduling**: Automated crawling at set times
- **Notifications**: Email alerts when crawls complete

For more advanced customizations, consider learning:
- **Tkinter theming** for advanced UI changes
- **Selenium WebDriver** for complex web interactions
- **Database design** for custom data storage
- **Python packaging** for distribution
