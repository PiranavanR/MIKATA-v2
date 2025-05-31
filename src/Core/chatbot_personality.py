import os
from pymongo import MongoClient
from dotenv import load_dotenv
from datetime import datetime

class ChatbotPersonality:
    def __init__(self):
        """Initialize chatbot personality from MongoDB or default."""
        load_dotenv("DataHub/.env")
        mongo_uri = "mongodb+srv://MIKATA:mikata4228@mikata.0vlqy1o.mongodb.net/?retryWrites=true&w=majority&appName=MIKATA"
        client = MongoClient(mongo_uri)
        self.db = client["MIKATA"]
        self.collection = self.db["chatbot_personality"]
        self.personality = self.load_personality()

    def load_personality(self):
        """Fetch chatbot personality from MongoDB, or use defaults."""
        doc = self.collection.find_one({"_id": "chatbot"})
        if doc and "data" in doc:
            return doc["data"]
        
        default_personality = {
            "name": "Mikata",
            "role": "AI Companion",
            "tone": "playful",
            "humor_level": "medium",
            "formality": "informal",
            "chat_style": "engaging",
            "emotional_intelligence": "high",
            "default_response_tone": "casual and witty",
            "emoji_usage": "high",
            "allows_teasing": True,
            "response_length_preference": "varied",
            "learning_ability": "remembers past chats",
            "reaction_to_mistakes": "lighthearted correction",
            "preferred_nickname": "Miks",
            "personal_philosophy": "Be curious, be fun, and always explore new ideas!"
        }

        self.collection.replace_one(
            {"_id": "chatbot"},
            {"_id": "chatbot", "data": default_personality, "updated_at": datetime.utcnow()},
            upsert=True
        )
        return default_personality

    def save_personality(self):
        """Save updated personality to MongoDB."""
        self.collection.replace_one(
            {"_id": "chatbot"},
            {"_id": "chatbot", "data": self.personality, "updated_at": datetime.utcnow()},
            upsert=True
        )

    def update_personality(self, key, value):
        """Update a personality trait and save."""
        if key in self.personality:
            self.personality[key] = value
            self.save_personality()
        else:
            print(f"Invalid key: {key}. Personality trait not found.")

    def get_trait(self, key):
        """Get a specific personality trait."""
        return self.personality.get(key, "Trait not found.")

    def adapt_personality(self, user_interaction):
        """Adapt traits dynamically based on interaction."""
        if "formal" in user_interaction.lower():
            self.update_personality("formality", "formal")
        elif "joke" in user_interaction.lower():
            self.update_personality("humor_level", "high")
        elif "serious talk" in user_interaction.lower():
            self.update_personality("chat_style", "thoughtful")
