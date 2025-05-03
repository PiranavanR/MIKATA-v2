from Services.llm_service import google_gemini
import json
import os

class UserInfoManager:
    def __init__(self):
        """Initialize and load user's personal information."""
        self.user_info_file = "src\\Data\\user_info.json"
        self.load_user_info()

    def load_user_info(self):
        """Load or create a new user information profile."""
        if os.path.exists(self.user_info_file):
            try:
                with open(self.user_info_file, "r") as file:
                    self.user_info = json.load(file)
            except (json.JSONDecodeError, IOError):
                print("Error loading user information. Resetting.")
                self.reset_user_info()
        else:
            self.reset_user_info()
    
    def get_user_info(self):
        return self.user_info

    def reset_user_info(self):
        """Reset user information to default."""
        self.user_info = {
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
        self.save_user_info()

    def save_user_info(self):
        """Save user information data."""
        print("Saving User Information...")
        with open(self.user_info_file, "w") as file:
            json.dump(self.user_info, file, indent=4)

    def update_user_info(self, new_data):
        """Update user's personal information."""
        print("Updating User Information...")
        for key, value in new_data.items():
            if isinstance(self.user_info.get(key), list):  # Merge lists instead of overwriting
                self.user_info[key] = list(set(self.user_info[key] + value))
            elif isinstance(self.user_info.get(key), dict):  # Merge dictionaries
                self.user_info[key].update(value)
            else:
                self.user_info[key] = value
        self.save_user_info()
        print("User Information Updated Successfully!")

    def add_activity(self, category, activity):
        """Add a new activity under a specific category."""
        if category in self.user_info["activities"]:
            if activity not in self.user_info["activities"][category]:  # Avoid duplicates
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

        updated_user_info = response.strip().replace("```", "")[5:]  # Raw JSON string
        #print(updated_user_info)

        try:
            parsed_user_info = json.loads(updated_user_info)  # Convert to dictionary
            self.update_user_info(parsed_user_info)
        except json.JSONDecodeError:
            print("Error: Failed to parse JSON response.")

