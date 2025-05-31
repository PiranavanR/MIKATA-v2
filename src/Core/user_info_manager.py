from Services.llm_service import google_gemini
from pymongo import MongoClient
from dotenv import load_dotenv
import json
import os
import datetime

class UserInfoManager:
    def __init__(self):
        """Initialize MongoDB connection and load user's personal information."""
        load_dotenv("DataHub/.env")

        MONGO_URI = "mongodb+srv://MIKATA:mikata4228@mikata.0vlqy1o.mongodb.net/?retryWrites=true&w=majority&appName=MIKATA"
        self.client = MongoClient(MONGO_URI)
        self.db = self.client["MIKATA"]
        self.collection = self.db["user_info"]

        self.user_info = self.load_user_info()

    def load_user_info(self):
        """Load user info from MongoDB or create default."""
        existing = self.collection.find_one({"_id": "profile"})
        if existing:
            return existing["data"]
        else:
            return self.reset_user_info(save=True)

    def get_user_info(self):
        return self.user_info

    def reset_user_info(self, save=False):
        """Reset user information to default."""
        default_info = {
            "name": "Unknown",
            "age": None,
            "gender": "Unspecified",
            "location": "Unknown",
            "language": "English",
            "hobbies": [],
            "profession": "Unspecified",
            "preferences": {
                "communication_style": "neutral",
                "favorite_topics": [],
                "disliked_topics": []
            },
            "activities": {
                "internships": [],
                "projects": [],
                "presentations": [],
                "certifications": [],
                "other_achievements": []
            }
        }
        self.user_info = default_info
        if save:
            self.save_user_info()
        return default_info

    def save_user_info(self):
        """Save user information to MongoDB."""
        print("Saving User Information...")
        self.collection.replace_one(
            {"_id": "profile"},
            {"_id": "profile", "data": self.user_info, "updated_at": datetime.datetime.utcnow()},
            upsert=True
        )

    def update_user_info(self, new_data):
        """Update user's personal information."""
        print("Updating User Information...")
        for key, value in new_data.items():
            if isinstance(self.user_info.get(key), list):
                self.user_info[key] = list(set(self.user_info[key] + value))
            elif isinstance(self.user_info.get(key), dict):
                for sub_key, sub_value in value.items():
                    if isinstance(self.user_info[key].get(sub_key), list):
                        self.user_info[key][sub_key] = list(set(self.user_info[key][sub_key] + sub_value))
                    else:
                        self.user_info[key][sub_key] = sub_value
            else:
                self.user_info[key] = value
        self.save_user_info()
        print("User Information Updated Successfully!")

    def add_activity(self, category, activity):
        """Add a new activity under a specific category."""
        if category in self.user_info["activities"]:
            if activity not in self.user_info["activities"][category]:
                self.user_info["activities"][category].append(activity)
                self.save_user_info()
                print(f"Added activity under {category}: {activity}")
            else:
                print(f"Activity already exists in {category}: {activity}")
        else:
            print(f"Invalid activity category: {category}")

    def analyze_and_update(self, conversation_history):
        """Analyze conversation history and update user information."""
        print("Analyzing User Information...")
        convo_text = "\n".join([f"{c['role']}: {c['content']}" for c in conversation_history])

        prompt = f"""
        Based on the following conversation history, extract and update the user's personal details:
        {convo_text}

        - If they mention their name, update "name".
        - If they mention age, gender, or location, update those fields.
        - Detect hobbies and update "hobbies".
        - Detect professional details (job title, interests) and update "profession".
        - Detect preferences (communication style, favorite/disliked topics).
        - Detect any new activities (internships, projects, presentations, certifications, or achievements).

        Reply in JSON format with:
        {{
            "name": "Unknown",
            "age": null,
            "gender": "Unspecified",
            "location": "Unknown",
            "language": "English",
            "hobbies": [],
            "profession": "Unspecified",
            "preferences": {{
                "communication_style": "neutral",
                "favorite_topics": [],
                "disliked_topics": []
            }},
            "activities": {{
                "internships": [],
                "projects": [],
                "presentations": [],
                "certifications": [],
                "other_achievements": []
            }}
        }}
        Note: Only include fields that need updates. Do not modify unchanged fields.
        """

        response = google_gemini(prompt, "")
        cleaned_response = response.strip().replace("```", "")
        if cleaned_response.lower().startswith("json"):
            cleaned_response = cleaned_response[4:].strip()

        try:
            parsed_user_info = json.loads(cleaned_response)
            self.update_user_info(parsed_user_info)
        except json.JSONDecodeError:
            print("Error: Failed to parse JSON response.")
