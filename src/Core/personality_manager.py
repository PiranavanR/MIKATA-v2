from Services.llm_service import google_gemini
import json
import os
from dotenv import load_dotenv

class PersonalityManager:
    def __init__(self):
        """Initialize and load personality profile."""
        self.personality_file = "src\\Data\\personality.json"
        self.load_personality()
        load_dotenv("DataHub\\.env")

    def load_personality(self):
        """Load or create a new personality profile."""
        if os.path.exists(self.personality_file):
            try:
                with open(self.personality_file, "r") as file:
                    self.personality = json.load(file)
            except (json.JSONDecodeError, IOError):
                print("Error loading personality. Resetting.")
                self.reset_personality()
        else:
            self.reset_personality()

    def reset_personality(self):
        """Reset personality to default."""
        self.personality = {
            "name": "Unknown",
            "tone": "neutral",
            "interests": [],
            "humor_level": "medium",
            "formality": "balanced",
            "topics_liked": [],
            "topics_disliked": []
        }
        self.save_personality()

    def save_personality(self):
        """Save personality data."""
        print("Saving Personality...")
        with open(self.personality_file, "w") as file:
            json.dump(self.personality, file, indent=4)

    def analyze_and_update(self, conversation_history):
        """Update the personality profile based on recent conversations."""
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
        Reply in the following format(json):
            "name": "Unknown",
            "tone": "neutral",
            "interests": [],
            "humor_level": "medium",
            "formality": "balanced",
            "topics_liked": [],
            "topics_disliked": []
        Note:You can add extra details if you think it's necessary.
        And make the personality traits like tone (which are temporary) as per the recent conversation alone.
        """

        response = google_gemini(prompt, "")

        updated_personality = response.strip().replace("```","")
        
        # Parse and merge new traits
        try:
            new_traits = json.loads(updated_personality)  # Ensure response is JSON formatted
            for key, value in new_traits.items():
                if isinstance(self.personality[key], list):  # Merge lists instead of overwriting
                    self.personality[key] = list(set(self.personality[key] + value))
                else:
                    self.personality[key] = value
            self.save_personality()
            print("Personality Update Succesful!")
        except json.JSONDecodeError:
            print("Error parsing personality update")

    def get_personality(self):
        """Return the stored personality profile."""
        return self.personality
