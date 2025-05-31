import openai
import time
from google import genai
import requests
# Setup once

def measure_time(func):
    """Decorator to measure the runtime of a function."""
    def wrapper(*args, **kwargs):
        start_time = time.time()  # Start timer
        result = func(*args, **kwargs)  # Run the function
        end_time = time.time()  # End timer
        print(f"Execution time of {func.__name__}: {end_time - start_time:.6f} seconds\n")
        return result
    return wrapper

@measure_time
def novita(system_prompt: str, user_prompt: str, model: str = "qwen/qwen2.5-7b-instruct", stream: bool = True):
    """Send system and user prompt to Novita API and print the response."""

    openai.api_key = "sk_LtRlPTOGFu6zLo0BaSZP1_bF4LEm5_q1wLf4RC8P7-M"
    openai.api_base = "https://api.novita.ai/v3/openai"
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    response = openai.ChatCompletion.create(
        model=model,
        messages=messages,
        stream=stream,
    )

    if stream:
        for chunk in response:
            print(chunk['choices'][0]['delta'].get('content', ''), end="")
    else:
        print(response['choices'][0]['message']['content'])

@measure_time
def google_gemini(system_prompt: str, user_prompt: str, model: str = "gemini-2.0-flash"):
    """Send system and user prompt to Google Gemini API and print the response."""

    genai_client = genai.Client(api_key="AIzaSyCb8v1NXNOacUlDE4_zUmL43dj1rFDrmQQ")
    contents = [
        {"role": "user", "parts": [{"text": system_prompt}]},
        {"role": "user", "parts": [{"text": user_prompt}]}
    ]

    response = genai_client.models.generate_content(
        model=model,
        contents=contents
    )

    print(response.text)

@measure_time
def deepinfra(system_prompt: str, user_prompt: str, model: str = "meta-llama/Llama-2-13b-chat-hf", stream: bool = False):
    """Send system and user prompt to DeepInfra API and print the response."""

    openai.api_key = "BCRigsREaNtRyHsPru2BOjSHEHZMDj00"
    openai.api_base = "https://api.deepinfra.com/v1/openai"

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    response = openai.ChatCompletion.create(
        model=model,
        messages=messages,
        stream=stream,
    )

    if stream:
        for chunk in response:
            print(chunk['choices'][0]['delta'].get('content', ''), end="")
    else:
        print(response['choices'][0]['message']['content'])
        #print(response['usage']['prompt_tokens'], response['usage']['completion_tokens'])

@measure_time
def openrouter_llama4_maverick(system_prompt: str, user_prompt: str, image_url: str = None):
    """Send system and user prompt (optionally with image) to Meta LLaMA 4 Maverick via OpenRouter."""

    api_key = "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"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",  
        "X-Title": "MIKATA Assistant"               
    }

    content = [{"type": "text", "text": user_prompt}]
    if image_url:
        content.append({
            "type": "image_url",
            "image_url": {"url": image_url}
        })

    payload = {
        "model": "meta-llama/llama-4-maverick:free",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": content}
        ]
    }

    response = requests.post("https://openrouter.ai/api/v1/chat/completions",
                             headers=headers, json=payload)

    if response.status_code == 200:
        result = response.json()
        print(result['choices'][0]['message']['content'])
    else:
        print(f"Error {response.status_code}: {response.text}")

messages = []

from huggingface_hub import InferenceClient
from Core.memory_management import History, Memory
from Core.personality_manager import PersonalityManager
from Core.chatbot_personality import ChatbotPersonality  
from Core.user_info_manager import UserInfoManager
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
        TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY")
        self.client = InferenceClient(
            provider="together",
            api_key= TOGETHER_API_KEY
        )

    def subdivide_query(self, user_message):
        """Determine required functions using LLM."""
        if "sleep" in user_message:
            self.history_management.save_history()
            print("History Saved Successfully!")
            summary = self.memory_management.summariser(self.messages)
            self.memory_management.store_summary(summary)
            print("Memory Updated Successfully!")
            return "exit"

        system_messages = [
            {
                "role": "system",
                "content": f"""
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
            }
        ]
        
        messages = system_messages + [{"role": "user", "content": user_message}]
        self.messages.append({"role": "user", "content": user_message})
        completion = self.client.chat.completions.create(
            model=self.LLM_Model,
            messages=messages,
            max_tokens=100
        )
        return completion.choices[0].message.content.strip()

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

        print(google_gemini("", user_query))
        print(deepinfra("", user_query))
        print(novita("", user_query))
        print(openrouter_llama4_maverick("", user_query))

    def track_user_activities(self, user_message):
        """Extract and update user activities if detected in conversation."""
        if "internship" in user_message.lower():
            self.user_info_manager.add_activity("internships", user_message)
        elif "project" in user_message.lower():
            self.user_info_manager.add_activity("projects", user_message)
        elif "presentation" in user_message.lower():
            self.user_info_manager.add_activity("presentations", user_message)

Brain().generate_response("Hello there!What's your name?")