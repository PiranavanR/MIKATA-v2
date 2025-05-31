import json
from pymongo import MongoClient
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv("DataHub/.env")
client = MongoClient("mongodb+srv://MIKATA:mikata4228@mikata.0vlqy1o.mongodb.net/?retryWrites=true&w=majority&appName=MIKATA")
collection = client["MIKATA"]["chatbot_personality"]

file_path = "src/Data/chatbot_personality.json"

if os.path.exists(file_path):
    with open(file_path, "r") as f:
        data = json.load(f)

    collection.replace_one(
        {"_id": "chatbot"},
        {"_id": "chatbot", "data": data, "migrated_at": datetime.utcnow()},
        upsert=True
    )
    print("✅ Chatbot personality migrated successfully.")
else:
    print(f"❌ File not found at {file_path}")
