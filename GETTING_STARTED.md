# Getting Started with Web Crawler Pro

## Quick Start Guide

### Option 1: Use the Executable (Recommended for End Users)
1. **Download**: Get `WebCrawlerPro.exe` from the `dist` folder
2. **Run**: Double-click the executable file
3. **Register**: Create a new account with username/password
4. **Start Crawling**: Enter a URL and click "Start Crawling"

### Option 2: Run from Source (For Developers)
1. **Setup Virtual Environment**:
   ```bash
   python -m venv venv
   .\venv\Scripts\activate
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run Application**:
   ```bash
   python main.py
   ```

## First Time Usage

### 1. Create Account
- Click "Register" on the login screen
- Enter a username and password (minimum 6 characters)
- Click "Register" to create your account

### 2. Login
- Enter your username and password
- Click "Login"

### 3. Start Your First Crawl
- Go to the "New Crawl" tab
- Enter a URL (e.g., `https://example.com`)
- Adjust settings:
  - **Max Depth**: Start with 1 or 2 for testing
  - **Delay**: Keep at 1 second to be polite to servers
  - **Same Domain Only**: Keep checked for focused crawling
- Click "Start Crawling"

### 4. View Results
- Switch to "Crawl Jobs" tab to see your crawl history
- Double-click any completed job to view the crawled data
- Data will appear in the "Crawled Data" tab

## Example URLs to Test

### Safe Testing URLs:
- `https://httpbin.org/html` - Simple HTML page
- `https://example.com` - Basic example site
- `https://quotes.toscrape.com` - Quotes website designed for scraping practice

### Settings for Different Use Cases:

**Quick Test (Single Page)**:
- Max Depth: 0
- Delay: 1 second
- Same Domain Only: ✓

**Small Website Crawl**:
- Max Depth: 2
- Delay: 1-2 seconds
- Same Domain Only: ✓

**Focused Deep Crawl**:
- Max Depth: 3-5
- Delay: 2-3 seconds
- Same Domain Only: ✓

## Tips for Effective Crawling

### 1. Be Respectful
- Always use delays between requests (1+ seconds)
- Don't crawl too deeply on large sites
- Check if the site has an API instead

### 2. Start Small
- Test with depth 0 or 1 first
- Gradually increase depth as needed
- Monitor the number of pages being crawled

### 3. Troubleshooting
- If crawling fails, check your internet connection
- Some sites block automated requests
- Try different URLs if one doesn't work

## Understanding the Interface

### New Crawl Tab
- **URL Field**: Enter the starting URL
- **Max Depth**: How many link levels to follow
- **Delay**: Seconds between requests
- **Same Domain Only**: Restrict crawling to the same website

### Crawl Jobs Tab
- Shows all your crawling jobs
- Status: pending, running, completed, failed
- Double-click to view data

### Crawled Data Tab
- Shows the actual content from crawled pages
- Displays URL, title, and text content
- Automatically opens when you select a job

## Building Your Own Executable

If you want to create your own executable:

```bash
python build_exe.py
```

The executable will be created in the `dist` folder.

## Need Help?

- Check the README.md for detailed documentation
- Look at the console output for error messages
- Make sure you have internet connectivity
- Try simpler URLs if complex sites don't work

Happy crawling! 🕷️
