import json
import os

class ChatbotPersonality:
    def __init__(self, personality_file="src\\Data\\chatbot_personality.json"):
        """Initialize chatbot personality from a JSON file or set default values."""
        self.personality_file = personality_file
        self.personality = self.load_personality()

    def load_personality(self):
        """Load chatbot personality from a JSON file. If not found, use default values."""
        if os.path.exists(self.personality_file):
            try:
                with open(self.personality_file, "r") as file:
                    return json.load(file)
            except json.JSONDecodeError:
                print("Error loading chatbot personality. Using default values.")
        
        # Default chatbot personality
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
        return default_personality

    def update_personality(self, key, value):
        """Update a specific trait in the chatbot's personality and save it."""
        if key in self.personality:
            self.personality[key] = value
            self.save_personality()
        else:
            print(f"Invalid key: {key}. Personality trait not found.")

    def save_personality(self):
        """Save the updated chatbot personality to the JSON file."""
        try:
            with open(self.personality_file, "w") as file:
                json.dump(self.personality, file, indent=4)
        except IOError as e:
            print(f"Error saving chatbot personality: {e}")

    def get_trait(self, key):
        """Retrieve a specific trait from the chatbot's personality."""
        return self.personality.get(key, "Trait not found.")

    def adapt_personality(self, user_interaction):
        """Dynamically adapt chatbot personality based on interactions."""
        if "formal" in user_interaction.lower():
            self.update_personality("formality", "formal")
        elif "joke" in user_interaction.lower():
            self.update_personality("humor_level", "high")
        elif "serious talk" in user_interaction.lower():
            self.update_personality("chat_style", "thoughtful")
