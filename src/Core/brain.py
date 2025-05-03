from Core.memory_management import History, Memory
from Core.personality_manager import PersonalityManager
from Core.chatbot_personality import ChatbotPersonality  
from Core.user_info_manager import UserInfoManager
from Services.llm_service import deepinfra, google_gemini
import os

class Brain:
    def __init__(self):
        """Initialize the LLM client with Together AI API."""
        self.messages = []
        self.LLM_Model = os.getenv("self.LLM_Model")
        self.memory_management = Memory()
        self.history_management = History()
        self.personality_management = PersonalityManager()
        self.chatbot_personality = ChatbotPersonality()
        self.user_info_manager = UserInfoManager()

    def subdivide_query(self, user_message):
        """Determine required functions using LLM."""
        if "sleep" in user_message:
            self.history_management.save_history()
            print("History Saved Successfully!")
            summary = self.memory_management.summariser(self.messages)
            self.memory_management.store_summary(summary)
            print("Memory Updated Successfully!")
            return "exit"

        system_messages = f"""
                    You are an intelligent AI assistant with access to various functions:

                    get_location() → Fetch the user's latitude, longitude, and address. No parameters required.
                    get_weather(location: str = None) → Retrieve the weather for a given location. If location is not provided, use the user's current location from get_location().
                    get_current_datetime() → Get the current date, day, and time. No parameters required.
                    search_wikipedia(query: str, char_limit: int = 500) → Get factual summaries from Wikipedia. Limit the response to char_limit characters while ensuring complete sentences.
                    search_duckduckgo(query: str, max_results: int = 3) → Fetch general web search results. Return up to max_results links.
                    Important Guidelines:
                    Use previous conversation history ({self.messages}) to avoid redundant API calls.
                    Parameter should be seperated by comma(,) and functions should be seperated by new line.
                    If the required information was recently provided, recall it instead of calling a function again.
                    Only execute functions if necessary; otherwise, default to 'general_chat'.
                    Function Selection Examples:
                    If the user asks for the weather again shortly after receiving it, recall it instead of calling get_weather().
                    If the user asks factual questions (e.g., "What is a black hole?"), use search_wikipedia().
                    If the user asks for general web information (e.g., "Latest news on SpaceX"), use search_duckduckgo().
                    Output Restriction:
                    Respond with the required function names and parameters only, separated by new lines.
                    If no function is needed, return 'general_chat'.  
                    """        
        
        self.messages.append({"role": "user", "content": user_message})
        result = deepinfra(system_messages, user_message)
        return result

    def generate_response(self, user_query, results):
        """Generate a natural response using LLM based on the fetched results."""
        self.history_management.update_history("user", user_query)

        relevant_contexts = self.memory_management.get_relevant_context(user_query)

        user_info = self.user_info_manager.get_user_info()

        prompt = f"""
            User Query: {user_query}
            Fetched Data: {results}
            Conversation History: {self.messages}
            Relevant past convo summaries: {relevant_contexts}

            User Profile:
            {user_info}  # Directly insert user profile data
            
            Chatbot Personality:
            - Name: {self.chatbot_personality.get_trait("name")}
            - Tone: {self.chatbot_personality.get_trait("tone")}
            - Humor Level: {self.chatbot_personality.get_trait("humor_level")}
            - Speech Formality: {self.chatbot_personality.get_trait("formality")}
            - Topics Liked: {", ".join(self.chatbot_personality.get_trait("topics_liked"))}
            - Topics Disliked: {", ".join(self.chatbot_personality.get_trait("topics_disliked"))}

            Generate a response that aligns with both personalities, making the conversation feel natural, engaging, and emotionally intelligent.
        """

        if results == "alt_prompt":
            prompt = user_query
        
        response = google_gemini(prompt, "")

        # Save history and update personality & user info
        self.history_management.update_history("assistant", response)
        self.messages.append({"role": "assistant", "content": response})
        self.personality_management.analyze_and_update(self.messages)  # Update chatbot personality
        self.user_info_manager.analyze_and_update(self.messages)  # Update user profile and activities
        self.chatbot_personality.adapt_personality(user_query)
        return response

    def track_user_activities(self, user_message):
        """Extract and update user activities if detected in conversation."""
        if "internship" in user_message.lower():
            self.user_info_manager.add_activity("internships", user_message)
        elif "project" in user_message.lower():
            self.user_info_manager.add_activity("projects", user_message)
        elif "presentation" in user_message.lower():
            self.user_info_manager.add_activity("presentations", user_message)