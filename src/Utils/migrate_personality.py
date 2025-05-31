import json
import os
from pymongo import MongoClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv("DataHub/.env")

# MongoDB connection
MONGO_URI = "mongodb+srv://MIKATA:mikata4228@mikata.0vlqy1o.mongodb.net/?retryWrites=true&w=majority&appName=MIKATA"  # Replace this with your actual MongoDB URI
client = MongoClient(MONGO_URI)
db = client["MIKATA"]
collection = db["personality_profile"]

# Path to local JSON file
personality_path = "src/Data/personality.json"

if not os.path.exists(personality_path):
    print("❌ No local personality.json found. Migration skipped.")
else:
    with open(personality_path, "r", encoding="utf-8") as file:
        try:
            personality_data = json.load(file)
            # Attach default _id for MongoDB
            personality_data["_id"] = "default"
            # Insert or update document
            collection.replace_one({"_id": "default"}, personality_data, upsert=True)
            print("✅ Personality data migrated to MongoDB successfully.")
        except json.JSONDecodeError:
            print("❌ Error reading JSON. Migration aborted.")
