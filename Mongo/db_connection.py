from pymongo import MongoClient

# Replace with your MongoDB Atlas connection string
MONGO_URI = "mongodb+srv://Jason:jason1234@cluster0.e3lxn.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

client = MongoClient(MONGO_URI)
db = client["news_db"]
collection = db["news"]

# Test connection
print("Connected to MongoDB Atlas successfully!")
