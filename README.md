# Web Crawler Pro

A desktop application for crawling web information with user authentication and data management.

## Features

- **User Authentication**: Secure login/registration system
- **Web Crawling**: Configurable web crawling with depth control
- **Data Management**: View, search, and manage crawled data
- **User-Friendly GUI**: Easy-to-use Tkinter interface
- **Standalone Executable**: No Python installation required for end users

## Installation & Setup

### For Development:

1. **Create Virtual Environment**:
   ```bash
   python -m venv venv
   .\venv\Scripts\activate  # Windows
   # or
   source venv/bin/activate  # Linux/Mac
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the Application**:
   ```bash
   python main.py
   ```

### For Distribution:

1. **Build Executable**:
   ```bash
   python build_exe.py
   ```

2. **Distribute**:
   - The executable will be created in `dist/WebCrawlerPro.exe`
   - Users can run this file without installing Python

## Usage

### First Time Setup:
1. Run the application
2. Click "Register" to create a new account
3. Enter username and password (minimum 6 characters)
4. Login with your credentials

### Crawling Websites:
1. Go to "New Crawl" tab
2. Enter the target URL
3. Configure options:
   - **Max Depth**: How many levels deep to crawl (0 = current page only)
   - **Delay**: Seconds to wait between requests (be polite!)
   - **Same Domain Only**: Only crawl pages from the same domain
4. Click "Start Crawling"

### Viewing Results:
1. Go to "Crawl Jobs" tab to see all your crawl jobs
2. Double-click on any job to view its crawled data
3. Data will appear in the "Crawled Data" tab

## Technical Details

### Architecture:
- **Frontend**: Tkinter (Python's built-in GUI library)
- **Backend**: SQLite database for data storage
- **Crawler**: requests + BeautifulSoup for web scraping
- **Threading**: Background crawling to keep UI responsive

### Database Schema:
- **users**: User accounts and authentication
- **crawl_jobs**: Crawling job history and status
- **crawled_data**: Actual crawled content and metadata

### Files:
- `main.py`: Main application with GUI
- `crawler.py`: Web crawling engine
- `webcrawler.db`: SQLite database (created automatically)
- `requirements.txt`: Python dependencies
- `build_exe.py`: Script to build executable

## Crawling Ethics

Please use this tool responsibly:
- Respect robots.txt files
- Use appropriate delays between requests
- Don't overload servers
- Only crawl sites you have permission to access
- Be mindful of copyright and terms of service

## Troubleshooting

### Common Issues:

1. **"Module not found" errors**: Make sure virtual environment is activated and dependencies are installed
2. **Crawling fails**: Check internet connection and URL validity
3. **Database errors**: Delete `webcrawler.db` to reset (will lose all data)
4. **Executable won't run**: Make sure all dependencies are included in the build

### Support:
- Check the console output for error messages
- Ensure you have proper internet connectivity
- Verify the target website is accessible

## License

This project is for educational and personal use. Please respect website terms of service and applicable laws when crawling.
