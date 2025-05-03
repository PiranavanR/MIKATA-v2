from Services.llm_service import openrouter_llama4_maverick
import json
import os
from dotenv import load_dotenv
import datetime
import time
from collections import Counter
import re

class History:
    def __init__(self):
        self.file_path = "src\\Data\\Conversation History.json"
        self.history = self.load_history()

    def load_history(self):
        """Load the conversation history from the JSON file."""
        if not os.path.exists(self.file_path):
            return []
        try:
            with open(self.file_path, "r") as convo:
                return json.load(convo)
        except (json.JSONDecodeError, IOError):
            print("Error loading history. Starting with an empty log.")
            return []

    def save_history(self):
        """Save the current history to the JSON file."""
        try:
            with open(self.file_path, "w") as convo:
                json.dump(self.history, convo, indent=4)
        except IOError as e:
            print(f"Error saving history: {e}")

    def update_history(self, role, content):
        """Update the history with new content."""
        if role == 'assistant':
            content = [{"role":"assistant", "content": content}]
        elif role == "user":
            content = [{"role":"user", "content": content}]

        if isinstance(content, list):
            self.history.extend(content)
        else:
            print("Content must be a list to update the history.")

class Memory:
    def __init__(self):
        self.summary_model = self.LLM_Model
        self.memory_file_path = "src\\Data\\memory.json"
        self.session_summaries = self.load_summaries()
        #print(summary_api_key,self.summary_model)
        self.sys_msg = f"Summarize the conversation in 1–3 concise sentences for long-term memory retention by an AI assistant. Focus only on essential information such as user requests, preferences, tasks, or key decisions to support accurate and personalized future responses. Exclude small talk or irrelevant content. Replace relative time expressions (e.g., “today,” “tomorrow”) with the exact date and time using {time.strftime('%H:%M %p', time.localtime())} and {datetime.datetime.now().date()}. Return only the summary text"

    def load_summaries(self):
        """Load the conversation history from the JSON file."""
        if not os.path.exists(self.memory_file_path):
            return []
        try:
            with open(self.memory_file_path, "r") as convo:
                return json.load(convo)
        except (json.JSONDecodeError, IOError):
            print("Error loading history. Starting with an empty log.")
            return []

    def store_summary(self, summary):
        """Store a single summary for the session."""
        session_id  = len(self.session_summaries)
        self.session_summaries.append({"id":session_id, "summary":summary, "timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())})
        try:
            with open(self.memory_file_path, "w") as convo:
                json.dump(self.session_summaries, convo, indent=4)
        except IOError as e:
            print(f"Error saving history: {e}")


    def get_relevant_context(self, user_input, top_n=3):
        """Retrieve the top N most relevant summaries for the current user input."""

        if len(self.session_summaries) < 3:
            top_n = len(self.session_summaries)

        similarity_scores = []

        for summary in self.session_summaries:
            id = summary['id']
            content = summary['summary']
            score = self.calculate_similarity(user_input, content)
            similarity_scores.append((id, score))
            
        # Sort by similarity score in descending order
        similarity_scores.sort(key=lambda x: x[1], reverse=True)
        print(similarity_scores)
        
        # Select the top N most relevant summaries
        top_summaries = [self.session_summaries[int(session_id)]['summary'] for session_id, _ in similarity_scores[:top_n]]
        
        return top_summaries

    def calculate_similarity(self, user_input, summary):
        """Calculate similarity between user input and a session summary."""
        # Tokenize and clean the text
        tokens_input = self.tokenize_text(user_input)
        tokens_summary = self.tokenize_text(summary)
        
        # Count occurrences of each word
        counter_input = Counter(tokens_input)
        counter_summary = Counter(tokens_summary)
        
        # Calculate the intersection of keywords
        common_tokens = set(tokens_input).intersection(set(tokens_summary))
        
        return len(common_tokens)  # Simple similarity based on shared keywords

    def tokenize_text(self, text):
        """Tokenize text into words, removing non-alphabetic characters."""
        text = text.lower()
        words = re.findall(r'\b\w+\b', text)  # Extract words using regex
        return words

    def summariser(self,conversations):
        """Summarise the Conversation."""
        # print("Conversations:",conversations)
        convo = ""

        for conversation in conversations:
            convo += f"{conversation['role']}:{conversation['content']} "
        
        print(convo)

        formated_convo = [{"role":"user","content":convo}]

        #print("Formatted Conversation:",formated_convo) 

        self.summary = openrouter_llama4_maverick(self.sys_msg, convo)

        print(self.summary)
        return self.summary
