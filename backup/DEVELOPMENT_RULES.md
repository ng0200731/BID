# Development Rules - Smart BrandID Downloader

## 🚨 CRITICAL RULES - NEVER BREAK THESE

### Version Tracking (MANDATORY)
- **EVERY code edit MUST get a version number**
- **UPDATE version info** before or after each change
- **USE the helper function**: `update_version("1.0.1", "Description")`
- **DOCUMENT changes** in VERSION_TRACKING.md
- **VERSION MUST be visible** in UI footer

### Data Protection
- **NEVER delete user data** without explicit permission
- **ALWAYS backup** important files before making changes
- **PRESERVE all existing downloads** in any folder reorganization
- **PROTECT user credentials** - never log or expose passwords

### System Compatibility
- **TEST on Chinese Windows** - encoding issues are common
- **VERIFY batch files work** on target system before finalizing
- **MAINTAIN UTF-8 compatibility** for special characters
- **ENSURE Chrome auto-opening** works properly

### Folder Structure
- **NEVER change** the central download folder: `download_artwork/`
- **PRESERVE** existing folder hierarchy: `YYYY_MM_DD/PO#_HH_MM_SS/`
- **MAINTAIN** backward compatibility with legacy folder names
- **RESPECT** user's existing file organization

## 📋 CODE STANDARDS

### Python Code
```python
# ✅ GOOD - Clear, descriptive names
def download_artwork_files(po_number, download_method):
    """Download artwork files for a specific PO using selected method"""
    try:
        # Clear logic with error handling
        result = process_download(po_number)
        return result
    except Exception as e:
        logger.error(f"Download failed for PO {po_number}: {e}")
        return None

# ❌ BAD - Unclear, no error handling
def dl(p, m):
    return proc(p)
```

### File Operations
```python
# ✅ ALWAYS check file existence
if os.path.exists(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

# ✅ ALWAYS use UTF-8 encoding
with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
```

### Error Handling
```python
# ✅ COMPREHENSIVE error handling
try:
    result = risky_operation()
    log_success(result)
    return result
except SpecificException as e:
    log_error(f"Specific error: {e}")
    return fallback_value
except Exception as e:
    log_error(f"Unexpected error: {e}")
    raise
```

## 🎯 PROJECT-SPECIFIC RULES

### Web Interface
- **KEEP UI clean** - avoid version numbers and clutter
- **USE consistent styling** - maintain existing color scheme
- **ENSURE responsive design** - works on different screen sizes
- **PROVIDE clear feedback** - progress bars, status messages

### Batch Files
- **KEEP SIMPLE** - avoid complex temporary file creation
- **TEST THOROUGHLY** - verify on target Windows system
- **HANDLE ERRORS** gracefully with clear messages
- **AUTO-OPEN BROWSER** - Chrome first, fallback to default

### Download Methods
- **PRESERVE all 5 methods** - users may prefer different approaches
- **MAINTAIN method selection** - don't force a single method
- **ENSURE progress tracking** - real-time feedback for users
- **HANDLE failures gracefully** - clear error messages

## 🔧 TESTING CHECKLIST

### Before Any Release
- [ ] Batch file starts application correctly
- [ ] Chrome opens automatically to localhost:5001
- [ ] All 5 download methods are available
- [ ] Download folder creation works properly
- [ ] Existing downloads are preserved
- [ ] Progress tracking displays correctly
- [ ] Error messages are clear and helpful
- [ ] Chinese Windows compatibility verified

### Code Quality
- [ ] All functions have docstrings
- [ ] Error handling is comprehensive
- [ ] Variable names are descriptive
- [ ] No hardcoded paths or values
- [ ] UTF-8 encoding used consistently
- [ ] Comments explain complex logic

## 🚫 FORBIDDEN ACTIONS

### Never Do These
- Delete user download folders
- Change core folder structure without permission
- Install packages without asking user
- Remove existing functionality
- Break backward compatibility
- Ignore encoding issues
- Skip error handling
- Use unclear variable names
- Hardcode file paths
- Remove user data validation

## 💡 BEST PRACTICES

### When Adding Features
1. **ASK FIRST** - confirm user wants the feature
2. **PLAN CAREFULLY** - consider impact on existing functionality
3. **TEST THOROUGHLY** - verify on target system
4. **DOCUMENT CHANGES** - update README and comments
5. **PRESERVE COMPATIBILITY** - don't break existing workflows

### When Fixing Bugs
1. **UNDERSTAND ROOT CAUSE** - don't just patch symptoms
2. **TEST THE FIX** - verify it actually solves the problem
3. **CHECK SIDE EFFECTS** - ensure fix doesn't break other features
4. **ADD PREVENTION** - improve error handling to prevent recurrence

---
*These rules ensure the Smart BrandID Downloader remains stable, user-friendly, and maintainable.*
