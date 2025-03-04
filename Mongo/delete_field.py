from pymongo import MongoClient

# Connect to MongoDB
MONGO_URI = "mongodb+srv://Jason:jason1234@cluster0.e3lxn.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(MONGO_URI)
db = client["news_db"]
collection = db["articles"]

# Field to remove
field_to_remove = "entity_summary"  # Change this to the field you want to delete

# Update all documents to remove the field
result = collection.update_many({}, {"$unset": {field_to_remove: ""}})

print(f"✅ {result.modified_count} documents updated. '{field_to_remove}' field removed.")
