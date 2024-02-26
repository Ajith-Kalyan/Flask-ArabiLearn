import sqlite3

# Connect to the SQLite database (or create it if it doesn't exist)
conn = sqlite3.connect('Translations.db')

# Create a cursor object to execute SQL commands
cursor = conn.cursor()

# Define your SQL command to create a table
create_table_query = '''
CREATE TABLE IF NOT EXISTS arabic_lessons (
    id INTEGER PRIMARY KEY,
    lessonNo INTEGER,
    englishSentences TEXT,
    arabicSentences TEXT,
    audioPath TEXT,
    isCorrect BOOLEAN
);
'''

# Execute the SQL command to create the table
cursor.execute(create_table_query)

# Commit the transaction to save changes
conn.commit()

# Close the connection
conn.close()
