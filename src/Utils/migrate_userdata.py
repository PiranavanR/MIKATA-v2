import json
from pymongo import MongoClient
import os
from dotenv import load_dotenv
import datetime

# Load environment variables
load_dotenv("DataHub/.env")

# Connect to MongoDB
MONGO_URI = "mongodb+srv://MIKATA:mikata4228@mikata.0vlqy1o.mongodb.net/?retryWrites=true&w=majority&appName=MIKATA"
client = MongoClient(MONGO_URI)
db = client["MIKATA"]
collection = db["user_info"]

# Path to the local JSON file
file_path = "src/Data/user_info.json"

# Load and migrate data
if os.path.exists(file_path):
    try:
        with open(file_path, "r") as file:
            user_info = json.load(file)

        # Insert or replace the document in MongoDB
        collection.replace_one(
            {"_id": "profile"},
            {"_id": "profile", "data": user_info, "migrated_at": datetime.datetime.utcnow()},
            upsert=True
        )

        print("✅ user_info.json migrated to MongoDB successfully!")

    except json.JSONDecodeError:
        print("❌ Error: Invalid JSON format in user_info.json.")
else:
    print(f"❌ Error: File not found at {file_path}")
