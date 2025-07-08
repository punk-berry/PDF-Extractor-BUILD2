import fitz  # PyMuPDF

# Create a new PDF document
doc = fitz.open()

# Add a page
page = doc.new_page()

# Add some text to create a simple table
text = """
Product ID    Product Name    Price    Quantity
001           Widget A        $10.99   100
002           Widget B        $15.50   75
003           Widget C        $8.25    200
004           Widget D        $12.75   50
"""

# Insert text
page.insert_text((50, 50), text, fontsize=12)

# Save the document
doc.save("/app/test_table.pdf")
print("Test PDF created successfully!")