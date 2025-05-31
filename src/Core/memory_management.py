from pymongo import MongoClient
from collections import Counter
import datetime
import time
import re
from Services.llm_service import openrouter_llama4_maverick
import logging

logger = logging.getLogger(__name__)

class History:
    def __init__(self):
        uri = "mongodb+srv://MIKATA:mikata4228@mikata.0vlqy1o.mongodb.net/?retryWrites=true&w=majority&appName=MIKATA"
        client = MongoClient(uri)
        db = client["MIKATA"]
        self.collection = db["conversation_history"]

    def load_history(self):
        return list(self.collection.find({}, {"_id": 0}).sort("timestamp", -1).limit(20))

    def save_history(self):
        pass

    def update_history(self, role, content):
        if role not in ["user", "assistant"]:
            logger.warning(f"Invalid role '{role}'. Must be 'user' or 'assistant'.")
            return
        document = {
            "role": role,
            "content": content,
            "timestamp": datetime.datetime.now()
        }
        self.collection.insert_one(document)
        logger.debug(f"History updated: {role} message at {document['timestamp']}")

class Memory:
    def __init__(self):
        uri = "mongodb+srv://MIKATA:mikata4228@mikata.0vlqy1o.mongodb.net/?retryWrites=true&w=majority&appName=MIKATA"
        client = MongoClient(uri)
        self.db = client["MIKATA"]
        self.collection = self.db["memory_summaries"]
        self.scheduled_events_collection = self.db["scheduled_events"]

        now_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M %p')
        self.sys_msg = (
            f"Summarize the conversation in 1–3 concise sentences for long-term memory retention "
            f"by an AI assistant. Focus only on essential information such as user requests, preferences, "
            f"tasks, or key decisions to support accurate and personalized future responses. Exclude small talk "
            f"or irrelevant content. Replace relative time expressions (e.g., “today,” “tomorrow”) with the exact "
            f"date and time using {now_str}. "
            f"Return only the summary text."
        )

    def load_summaries(self):
        return list(self.collection.find({}, {"_id": 0}))

    def store_summary(self, summary):
        document = {
            "summary": summary,
            "timestamp": datetime.datetime.now()
        }
        self.collection.insert_one(document)
        logger.info("Memory summary stored successfully.")

    def get_relevant_context(self, user_input, top_n=3):
        summaries = self.load_summaries()
        if not summaries:
            return []

        similarity_scores = []
        for summary_doc in summaries:
            summary_text = summary_doc.get("summary")
            if summary_text:
                score = self.calculate_similarity(user_input, summary_text)
                similarity_scores.append((summary_text, score))

        similarity_scores.sort(key=lambda x: x[1], reverse=True)
        return [text for text, _ in similarity_scores[:top_n]]

    def calculate_similarity(self, user_input, summary):
        tokens_input = self.tokenize_text(user_input)
        tokens_summary = self.tokenize_text(summary)
        common_tokens = set(tokens_input).intersection(set(tokens_summary))
        if not tokens_input and not tokens_summary:
            return 0.0
        return len(common_tokens) / (len(tokens_input) + len(tokens_summary) - len(common_tokens)) if (len(tokens_input) + len(tokens_summary) - len(common_tokens)) > 0 else 0.0

    def tokenize_text(self, text):
        text = text.lower()
        return re.findall(r'\b\w+\b', text)

    def summariser(self, conversations):
        if not conversations:
            return ""
        convo = "\n".join([f"{msg['role']}: {msg['content']}" for msg in conversations])
        try:
            summary = openrouter_llama4_maverick(self.sys_msg, convo)
            return summary
        except Exception as e:
            logger.error(f"Error during summarization: {e}")
            return ""

    def add_scheduled_event(self, event_id: str, action: str, trigger_time: datetime.datetime, specific_message: str = None):
        event_data = {
            "_id": event_id,
            "action": action,
            "trigger_time": trigger_time,
            "specific_message": specific_message,
            "created_at": datetime.datetime.now(),
            "is_active": True
        }
        try:
            self.scheduled_events_collection.insert_one(event_data)
            logger.info(f"Scheduled event added: {event_data}")
        except Exception as e:
            logger.error(f"Failed to add scheduled event: {e}")

    def get_active_scheduled_event(self):
        event = self.scheduled_events_collection.find_one(
            {"is_active": True, "trigger_time": {"$gt": datetime.datetime.now()}},
            sort=[("trigger_time", 1)]
        )
        return event

    def deactivate_scheduled_event(self, event_id: str):
        try:
            result = self.scheduled_events_collection.update_one(
                {"_id": event_id},
                {"$set": {"is_active": False, "deactivated_at": datetime.datetime.now()}}
            )
            if result.modified_count > 0:
                logger.info(f"Scheduled event {event_id} deactivated successfully.")
            else:
                logger.warning(f"No active scheduled event found with ID {event_id} to deactivate.")
        except Exception as e:
            logger.error(f"Failed to deactivate scheduled event {event_id}: {e}")
