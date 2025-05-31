import json
import os
from pymongo import MongoClient
import datetime

# MongoDB Atlas URI (targeting "mikata" cluster)
MONGO_URI = "mongodb+srv://MIKATA:mikata4228@mikata.0vlqy1o.mongodb.net/?retryWrites=true&w=majority&appName=MIKATA"

# Connect to MongoDB
client = MongoClient(MONGO_URI)
db = client['MIKATA']  # Database name is 'mikata'

# Define separate collections
conversation_collection = db['conversation_history']
memory_collection = db['memory_summaries']

def migrate_json_to_mongodb(json_file_path, document_type):
    if not os.path.exists(json_file_path):
        print(f"❌ {json_file_path} does not exist. Skipping.")
        return

    with open(json_file_path, 'r', encoding='utf-8') as file:
        try:
            data = json.load(file)
        except json.JSONDecodeError:
            print(f"❌ Error decoding JSON from {json_file_path}")
            return

    if not isinstance(data, list):
        print(f"❌ Unexpected format in {json_file_path}. Expected a list.")
        return

    docs_to_insert = []

    if document_type == "conversation":
        for item in data:
            if isinstance(item, list):
                for subitem in item:
                    if isinstance(subitem, dict):
                        docs_to_insert.append({
                            "type": "conversation",
                            "role": subitem.get("role", ""),
                            "content": subitem.get("content", ""),
                            "migrated_at": datetime.datetime.utcnow()
                        })
            elif isinstance(item, dict):
                docs_to_insert.append({
                    "type": "conversation",
                    "role": item.get("role", ""),
                    "content": item.get("content", ""),
                    "migrated_at": datetime.datetime.utcnow()
                })

        if docs_to_insert:
            result = conversation_collection.insert_many(docs_to_insert)
            print(f"✅ Inserted {len(result.inserted_ids)} conversation documents.")

    elif document_type == "summary":
        for item in data:
            if isinstance(item, dict):
                docs_to_insert.append({
                    "type": "summary",
                    "id": item.get("id"),
                    "summary": item.get("summary"),
                    "timestamp": item.get("timestamp"),
                    "migrated_at": datetime.datetime.utcnow()
                })

        if docs_to_insert:
            result = memory_collection.insert_many(docs_to_insert)
            print(f"✅ Inserted {len(result.inserted_ids)} memory summaries.")

if __name__ == "__main__":
    convo_history_path = "src/Data/Conversation History.json"
    summary_path = "src/Data/memory.json"

    migrate_json_to_mongodb(convo_history_path, document_type="conversation")
    migrate_json_to_mongodb(summary_path, document_type="summary")
