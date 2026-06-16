import pandas as pd
import mysql.connector
import os
import re  # <-- NEW: Python's text-scrubbing tool!

# 1. Connect to MySQL Database
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Root1234",  # <-- REMEMBER TO PUT YOUR PASSWORD HERE
    database="rank2college"
)
cursor = db.cursor()

# 2. Your Excel file and the specific sheets
excel_file = "Rank2College.xlsx"
sheet_names = ["IIT", "NIT", "IIIT", "GFTI"]

# The SQL instruction to insert data
insert_query = """
INSERT INTO college_cutoffs 
(institute_type, institute_name, branch_name, quota, category, gender, opening_rank, closing_rank)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
"""

# 3. Process the file
if os.path.exists(excel_file):
    print(f"Found {excel_file}! Let's count and load the data...\n")
    
    for sheet in sheet_names:
        df = pd.read_excel(excel_file, sheet_name=sheet)
        df = df.dropna(subset=['Opening Rank', 'Closing Rank'])
        
        total_rows = len(df)
        print(f"📊 Found {total_rows} entries in the {sheet} sheet! Cleaning and moving data...")
        
        for index, row in df.iterrows():
            
            # ---> THE FIX: Clean the ranks by keeping ONLY digits <---
            raw_opening = str(row['Opening Rank'])
            raw_closing = str(row['Closing Rank'])
            
            # re.sub(r'\D', '', text) means "Find anything that is NOT a digit, and delete it"
            clean_opening = re.sub(r'\D', '', raw_opening)
            clean_closing = re.sub(r'\D', '', raw_closing)
            
            # If a cell is completely empty after cleaning, skip it so it doesn't crash
            if clean_opening == '' or clean_closing == '':
                continue

            values = (
                sheet,  
                str(row['Institute']),
                str(row['Academic Program Name']),
                str(row['Quota']),
                str(row['Seat Type']),
                str(row['Gender']),
                int(clean_opening), # Now it is a pure number!
                int(clean_closing)  # Now it is a pure number!
            )
            cursor.execute(insert_query, values)
            
        # Save the data for this specific sheet
        db.commit()
        print(f"✅ Successfully saved all clean {sheet} data!\n")
        
else:
    print(f"❌ Could not find {excel_file}. Make sure it is inside your project folder.")

# Close the database connection
cursor.close()
db.close()
print("🎉 ALL DATA HAS BEEN SUCCESSFULLY LOADED!")