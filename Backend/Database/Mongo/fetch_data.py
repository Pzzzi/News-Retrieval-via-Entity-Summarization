from db_connection import collection  # Import collection from db_connection.py

# Fetch all articles
articles = collection.find()
for article in articles:
    print(f"{article['title']} - {article['date']}")
