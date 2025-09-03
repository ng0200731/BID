# 📁 BID Smart App - Folder Selection Guide

## 🎯 **Problem Solved**

The executable now allows users to select their own folders for:
1. **Download Folder** - Where artwork files are saved
2. **Reports Folder** - Where QC reports, stickers, and packing lists are saved

---

## 🚀 **First Time Setup**

### **When you first run BID_Smart_App.exe:**

1. **Console window appears** with startup messages
2. **Folder selection dialogs** will appear:

#### **Step 1: Select Download Folder**
```
Dialog: "Select Download Folder for Artwork Files"
Purpose: Where all downloaded artwork files will be saved
Example: C:\Users\YourName\Documents\BID_Downloads\
```

#### **Step 2: Select Reports Folder**
```
Dialog: "Select Reports Folder"  
Purpose: Where QC reports, stickers, and packing lists will be saved
Example: C:\Users\YourName\Documents\BID_Reports\
```

3. **Settings are saved** - you won't be asked again unless you delete settings
4. **Browser opens** automatically to http://localhost:5002

---

## 📂 **Folder Structure Created**

### **Download Folder Structure:**
```
Your_Selected_Download_Folder/
├── 2025_08_15/           # Daily folders
│   ├── PO_1234567/       # PO-specific folders
│   │   ├── artwork1.jpg
│   │   ├── artwork2.png
│   │   └── ...
│   └── PO_1234568/
└── 2025_08_16/
```

### **Reports Folder Structure:**
```
Your_Selected_Reports_Folder/
├── qc_report/
│   ├── 2025-08-15-1234567-qc.xlsx
│   ├── 2025-08-15-1234568-qc.xlsx
│   └── ...
├── stickers/
│   ├── 2025-08-15-1234567-sticker.xlsx
│   └── ...
└── packing_lists/
    ├── PL-20250815-001.pdf
    └── ...
```

---

## ⚙️ **Settings Management**

### **Settings File Location:**
```
Windows: C:\Users\[YourName]\BID_Smart_App\user_settings.json
```

### **Settings File Content:**
```json
{
  "download_directory": "C:\\Users\\YourName\\Documents\\BID_Downloads",
  "reports_directory": "C:\\Users\\YourName\\Documents\\BID_Reports"
}
```

### **To Change Folders:**
1. **Close the application**
2. **Delete** `user_settings.json` file
3. **Restart** BID_Smart_App.exe
4. **Select new folders** when prompted

---

## 🔧 **Advanced Configuration**

### **Manual Settings Edit:**
You can manually edit `user_settings.json`:

```json
{
  "download_directory": "D:\\MyCompany\\Artwork_Downloads",
  "reports_directory": "D:\\MyCompany\\Reports",
  "auto_create_subfolders": true,
  "backup_reports": true
}
```

### **Network Folder Support:**
```json
{
  "download_directory": "\\\\server\\shared\\BID_Downloads",
  "reports_directory": "\\\\server\\shared\\BID_Reports"
}
```

---

## 🎯 **User Experience Flow**

### **First Run:**
1. Double-click `BID_Smart_App.exe`
2. See console: "First time setup - Please select directories..."
3. Dialog 1: Select download folder
4. Dialog 2: Select reports folder  
5. Console: "Download folder: [your choice]"
6. Console: "Reports folder: [your choice]"
7. Browser opens automatically

### **Subsequent Runs:**
1. Double-click `BID_Smart_App.exe`
2. Uses saved folder settings
3. Browser opens automatically
4. Ready to use!

---

## 💼 **Business Benefits**

### **User-Friendly:**
- ✅ **Flexible folder selection** - users choose their preferred locations
- ✅ **Network drive support** - works with company shared folders
- ✅ **One-time setup** - settings remembered
- ✅ **Easy reconfiguration** - delete settings to change

### **Enterprise-Ready:**
- ✅ **Centralized storage** - all files in user-selected locations
- ✅ **Backup-friendly** - users can select backup drives
- ✅ **Compliance-ready** - files stored where company policies require
- ✅ **Multi-user support** - each user has their own settings

---

## 🛠️ **Troubleshooting**

### **Problem: Folder dialog doesn't appear**
**Solution:** 
- Check if `user_settings.json` already exists
- Delete it to trigger folder selection again

### **Problem: Can't access selected folder**
**Solution:**
- Ensure folder permissions are correct
- Try selecting a different folder
- Check network connectivity for network drives

### **Problem: Files not saving to selected folder**
**Solution:**
- Check folder write permissions
- Ensure folder still exists
- Restart application

### **Problem: Want to change folders**
**Solution:**
1. Close BID Smart App
2. Navigate to: `C:\Users\[YourName]\BID_Smart_App\`
3. Delete `user_settings.json`
4. Restart application
5. Select new folders when prompted

---

## 📋 **Default Fallback Behavior**

If folder selection fails or is cancelled:

### **Download Folder Fallback:**
```
C:\Users\[YourName]\BID_Smart_App\download_artwork\
```

### **Reports Folder Fallback:**
```
C:\Users\[YourName]\BID_Smart_App\reports\
```

---

## 🎉 **Summary**

**The executable now provides:**
- ✅ **User folder selection** on first run
- ✅ **Persistent settings** - remembers your choices
- ✅ **Flexible storage** - use any accessible folder
- ✅ **Network drive support** - works with company shares
- ✅ **Easy reconfiguration** - delete settings to change
- ✅ **Professional appearance** - proper folder dialogs

**Users can now:**
1. **Choose where files are saved**
2. **Use company network drives**
3. **Organize files their way**
4. **Comply with company policies**
5. **Easily backup their data**

**The folder selection error is completely resolved!**
