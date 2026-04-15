"""
Example: Work with Java tables — read data, click cells.
"""
from java_bridge import JavaApp

app = JavaApp("http://localhost:9996")
app.activate(".*Inventory.*")

# Get table info
tbl = app.table("Products")
info = tbl.info()
print(f"Table has {info['rows']} rows and {info['cols']} columns")

# Read cell data
for row in range(min(info["rows"], 5)):  # first 5 rows
    cell = tbl.cell(row, 0)
    print(f"  Row {row}: {cell}")

# Click a specific cell
tbl.click_cell(2, 1)

# Select from a combo box
app.select("Category", 3)

# Navigate menus
app.menu("File;Export;CSV")
