import sqlite3

conn = sqlite3.connect('po_database.db')
cursor = conn.cursor()

print("=== CHECKING DATABASE FOR PO 1284789 ===")

# Check items
cursor.execute('SELECT item_number, description FROM po_items WHERE po_number = ?', ('1284789',))
items = cursor.fetchall()

print(f"\nFound {len(items)} items:")
for i, item in enumerate(items, 1):
    print(f"Item {i}:")
    print(f"  Item Number: '{item[0]}'")
    print(f"  Description: {item[1]}")
    print()

conn.close()
