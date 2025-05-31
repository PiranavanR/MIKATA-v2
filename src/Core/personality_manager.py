from pymongo import MongoClient
from Services.llm_service import google_gemini
import json
import os
from dotenv import load_dotenv

class PersonalityManager:
    def __init__(self):
        """Initialize and connect to MongoDB."""
        load_dotenv("DataHub/.env")
        uri = "mongodb+srv://MIKATA:mikata4228@mikata.0vlqy1o.mongodb.net/?retryWrites=true&w=majority&appName=MIKATA"  # Replace with your actual MongoDB URI
        client = MongoClient(uri)
        db = client["MIKATA"]
        self.collection = db["personality_profile"]
        self.profile_id = "default"  # Static ID since there's only one profile for now
        self.personality = self.load_personality()

    def load_personality(self):
        """Load or initialize a personality profile from MongoDB."""
        profile = self.collection.find_one({"_id": self.profile_id})
        if profile:
            profile.pop("_id")
            return profile
        else:
            return self.reset_personality(save=True)

    def reset_personality(self, save=False):
        """Reset personality to default values."""
        default_profile = {
            "_id": self.profile_id,
            "name": "Unknown",
            "tone": "neutral",
            "interests": [],
            "humor_level": "medium",
            "formality": "balanced",
            "topics_liked": [],
            "topics_disliked": []
        }
        if save:
            self.collection.replace_one({"_id": self.profile_id}, default_profile, upsert=True)
        return {k: v for k, v in default_profile.items() if k != "_id"}

    def save_personality(self):
        """Save the current personality profile to MongoDB."""
        print("Saving Personality...")
        self.collection.replace_one({"_id": self.profile_id}, {"_id": self.profile_id, **self.personality}, upsert=True)

    def analyze_and_update(self, conversation_history):
        """Update the personality profile based on recent conversation history."""
        print("Analysing Personality...")
        convo_text = "\n".join([f"{c['role']}: {c['content']}" for c in conversation_history])

        prompt = f"""
        Based on the following conversation history, update the user's personality traits:
        {convo_text}

        - If they use formal or structured language, adjust "formality".
        - If they joke often, increase "humor_level".
        - Detect favorite topics and update "interests" and "topics_liked".
        - Detect disliked topics and update "topics_disliked".
        - If they mention their name, update "name".
        Reply in the following format (JSON):
            "name": "Unknown",
            "tone": "neutral",
            "interests": [],
            "humor_level": "medium",
            "formality": "balanced",
            "topics_liked": [],
            "topics_disliked": []
        Note: You can add extra details if you think it's necessary.
        And make the personality traits like tone (which are temporary) as per the recent conversation alone.
        """

        response = google_gemini(prompt, "")
        updated_personality = response.strip().replace("```", "")

        try:
            new_traits = json.loads(updated_personality)
            for key, value in new_traits.items():
                if isinstance(self.personality.get(key), list):
                    self.personality[key] = list(set(self.personality[key] + value))
                else:
                    self.personality[key] = value
            self.save_personality()
            print("Personality Update Successful!")
        except json.JSONDecodeError:
            print("Error parsing personality update")

    def get_personality(self):
        """Return the current personality profile."""
        return self.personality
