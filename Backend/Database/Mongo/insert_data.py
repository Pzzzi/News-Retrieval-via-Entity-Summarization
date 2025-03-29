from db_connection import collection  # Import collection from db_connection.py

news_data = {
    "title": "Elon Musk’s Neuralink Receives FDA Approval",
    "content": "Neuralink, Elon Musk’s brain-computer startup, has received FDA approval for human trials.",
    "date": "2024-06-10",
    "url": "https://news.com/elon-musk-neuralink"
}

# Insert the data
collection.insert_one(news_data)
print("News article inserted successfully!")

