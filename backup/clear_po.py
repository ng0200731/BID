import sqlite3

conn = sqlite3.connect('po_database.db')
cursor = conn.cursor()

print("=== CLEARING PO 1284789 FROM DATABASE ===")

# Delete existing records
cursor.execute('DELETE FROM po_items WHERE po_number = ?', ('1284789',))
cursor.execute('DELETE FROM po_headers WHERE po_number = ?', ('1284789',))

conn.commit()
print("✅ PO 1284789 cleared from database")

conn.close()
print("Now please re-save PO 1284789 to get the correct item numbers")
