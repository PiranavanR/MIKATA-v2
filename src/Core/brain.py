import json # Added for tool definition
from Core.memory_management import History, Memory
from Core.personality_manager import PersonalityManager
from Core.chatbot_personality import ChatbotPersonality
from Core.user_info_manager import UserInfoManager
from Services.llm_service import deepinfra, google_gemini, openrouter_llama4_maverick # Ensure all LLMs are imported
import os
import logging # Added for logging
from datetime import datetime

logger = logging.getLogger(__name__)

class Brain:
    def __init__(self):
        """Initialize the LLM client with Together AI API."""
        self.messages = [] # This should probably be the session history, not global history
        self.LLM_Model = os.getenv("LLM_Model") # Ensure this is set, default to something if not
        self.memory_management = Memory()
        self.history_management = History()
        self.personality_management = PersonalityManager()
        self.chatbot_personality = ChatbotPersonality()
        self.user_info_manager = UserInfoManager()

        # Define available tools/functions for the LLM
        self.function_definitions = {
            "get_location": {
                "description": "Fetch the user's latitude, longitude, and address.",
                "parameters": {"type": "object", "properties": {}}
            },
            "get_weather": {
                "description": "Retrieve the weather for a given location. If location is not provided, use the user's current location from get_location().",
                "parameters": {
                    "type": "object",
                    "properties": {"location": {"type": "string", "description": "The city or location name."}},
                    "required": []
                }
            },
            "get_current_datetime": {
                "description": "Get the current date, day, and time.",
                "parameters": {"type": "object", "properties": {}}
            },
            "search_wikipedia": {
                "description": "Get factual summaries from Wikipedia. Limit the response to char_limit characters while ensuring complete sentences.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string"},
                        "char_limit": {"type": "integer", "default": 500}
                    },
                    "required": ["query"]
                }
            },
            "search_duckduckgo": {
                "description": "Fetch general web search results. Return up to max_results links.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string"},
                        "max_results": {"type": "integer", "default": 3}
                    },
                    "required": ["query"]
                }
            },
            "schedule_conversation": {
                "description": "Schedules a specific time for MIKATA to message the user, or sets a 'do not disturb' period where MIKATA should not proactively message. Use this if the user wants to pause communication or asks to be reminded to chat later. It needs to know the type of action (schedule_reminder or pause_conversation), a clear time expression, and optionally a specific message to send.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "action": {"type": "string", "enum": ["schedule_reminder", "pause_conversation"], "description": "The type of scheduling action."},
                        "time_expression": {"type": "string", "description": "The exact time or duration, e.g., '4 PM', 'tomorrow morning', 'in 2 hours', 'until 6pm today', 'later today'."},
                        "specific_message": {"type": "string", "description": "An optional brief message to send at the scheduled time, e.g., 'still busy', 'it's 4pm'. If not provided, MIKATA will generate a default one.", "nullable": True}
                    },
                    "required": ["action", "time_expression"]
                }
            }
        }

    # IMPORTANT: The 'subdivide_query' method in Brain should primarily focus on intent
    # and tool calling, while the 'Agent' will then execute those tools.
    # The current structure has Brain calling Agent's subdivide_query.
    # Let's adjust to be more standard: Brain has the prompt logic, Agent has execution.

    def subdivide_query_for_tools(self, user_message: str) -> list[dict] | str:
        """
        Determines required functions using LLM based on user_message.
        Returns a list of tool calls (dict) or "general_chat" string.
        """
        system_message = f"""
        You are an intelligent AI assistant with access to various functions to help the user.
        Your goal is to determine which function(s) the user's request requires.

        Available functions:
        {json.dumps(self.function_definitions, indent=2)}

        Important Guidelines:
        - Use previous conversation history to understand context but do not explicitly use self.messages here.
        - If the required information was recently provided, prefer recalling it instead of calling a function again (this check happens in agent.py).
        - If the user asks for a communication pause or to be reminded later, use the `schedule_conversation` function.
        - If no function is necessary for the user's request, return "general_chat".
        - Respond ONLY with a JSON list of function calls. If no function is needed, return "general_chat".
        Example for scheduling: If user says "Can you remind me to chat after 4pm?", you should respond with:
        [
            {{
                "name": "schedule_conversation",
                "arguments": {{"action": "schedule_reminder", "time_expression": "4 PM"}}
            }}
        ]
        Example for pausing: If user says "I'm busy until 6pm, don't message me till then.", you should respond with:
        [
            {{
                "name": "schedule_conversation",
                "arguments": {{"action": "pause_conversation", "time_expression": "6 PM today", "specific_message": "still busy"}}
            }}
        ]
        """
        # Ensure the conversation history passed to the LLM is managed.
        # Here we only pass the user message for tool identification.
        # Full history is for response generation.

        # Use a model capable of function calling, e.g., Gemini
        # It's better to pass history for context, but not for the tool choice part only if LLM is smart enough
        # For function calling, Gemini often works best with just the user message
        # and the tool definitions.
        try:
            # Gemini typically returns tool calls as a `FunctionCall` object within its `parts`
            # The direct `google_gemini` wrapper might need adjustment to expose this.
            # For now, let's assume `google_gemini` can be prompted to return JSON.

            # Alternative approach: use the Gemini SDK directly for tool calling
            # from google.generativeai import GenerativeModel
            # model = GenerativeModel('gemini-1.5-flash')
            # response = model.generate_content(
            #    [{"role": "user", "parts": [{"text": user_message}]}],
            #    tools=[self.function_definitions[key] for key in self.function_definitions],
            #    tool_choice="auto"
            # )
            # If response.candidates[0].content.parts has FunctionCall, process it.

            # Simplified: Prompt the LLM to output JSON directly for tool calls
            tool_call_prompt = f"""
            {system_message}
            User's request: "{user_message}"
            """
            
            raw_llm_response = google_gemini(tool_call_prompt, "") # This LLM call needs to return JSON of function calls

            # Attempt to parse the LLM's response as JSON
            try:
                # Remove markdown code block if present
                cleaned_response = raw_llm_response.strip().replace("```json", "").replace("```", "")
                parsed_calls = json.loads(cleaned_response)
                if isinstance(parsed_calls, list):
                    return parsed_calls
                else: # If it's a single dict, wrap it
                    return [parsed_calls]
            except json.JSONDecodeError:
                # If it's not JSON, assume it's "general_chat"
                return "general_chat"

        except Exception as e:
            logger.error(f"Error in subdivide_query_for_tools (LLM call): {e}")
            return "general_chat"


    def generate_response(self, user_query: str, context: dict) -> tuple[str, dict | None]:
        """
        Generate a natural response using LLM based on the fetched results and context.
        Returns a tuple: (response_text, scheduling_instruction_dict_or_None).
        """
        self.history_management.update_history("user", user_query)
        # Assuming self.messages is the current session's conversation history
        self.messages.append({"role": "user", "content": user_query})

        # --- Check for explicit scheduling intent first using tool calling ---
        # This part should be handled by the Agent, which calls Brain's subdivide_query_for_tools
        # and then executes. For now, let's keep the tuple return from Brain.
        
        # The agent.py will call subdivide_query_for_tools, execute, and then pass results.
        # If a scheduling instruction is found by the Agent, it will bypass normal response generation
        # and just return the confirmation.
        
        # This means the `context` dictionary should contain `scheduling_instruction` if it's there.
        scheduling_instruction = context.get("scheduling_instruction")
        
        if scheduling_instruction:
            # If a scheduling instruction was found by the Agent, generate a confirmation message
            action = scheduling_instruction.get("action")
            time_exp = scheduling_instruction.get("time_expression")
            specific_msg = scheduling_instruction.get("specific_message")

            confirmation_prompt = f"""
            The user has requested to {action} until '{time_exp}'.
            If a specific message '{specific_msg}' was provided, incorporate it naturally.
            Generate a brief, confirming, and caring response.
            Do not repeat the exact time expression unless it sounds very natural.
            Examples:
            - User: "I'll talk to you after 4pm" -> Bot: "Understood! I'll ping you after then. Until next time, take care!"
            - User: "Don't bother me till 6pm" -> Bot: "Alright, I'll keep quiet until 6 PM. Focus on what you need to do!"
            - User: "Remind me to do laundry later" -> Bot: "Got it! I'll remind you about laundry later. Just focus on now."
            """
            confirmation_message = google_gemini(confirmation_prompt, "").strip()
            return confirmation_message, scheduling_instruction


        # --- Normal Response Generation if no scheduling instruction ---
        # Retrieve relevant contexts, user info, and chatbot personality
        relevant_contexts = self.memory_management.get_relevant_context(user_query)
        user_info = self.user_info_manager.get_user_info()
        
        # Prepare parts of the prompt
        user_profile_str = "\n".join([f"- {k}: {v}" for k, v in user_info.items() if k != 'activities' and k != 'preferences'])
        user_preferences_str = "\n".join([f"- {k}: {v}" for k, v in user_info.get('preferences', {}).items()])
        user_activities_lines = []
        for category, activities_list in user_info.get('activities', {}).items():
            if activities_list: # Only process if the list is not empty
                formatted_activities = []
                for activity in activities_list:
                    if isinstance(activity, str):
                        formatted_activities.append(activity)
                    elif isinstance(activity, dict):
                        # Convert dictionary to a readable string, e.g., "AI project (ongoing)"
                        details = ', '.join([f"{key}: {value}" for key, value in activity.items()])
                        formatted_activities.append(f"{category.capitalize()} ({details})")
                    else:
                        formatted_activities.append(str(activity)) # Fallback for unexpected types
                if formatted_activities:
                    user_activities_lines.append(f"- {category.capitalize()}: {', '.join(formatted_activities)}")

        user_activities_str = "\n".join(user_activities_lines)

        chatbot_personality_traits = self.chatbot_personality.personality # Access directly
        chatbot_personality_str = "\n".join([f"- {k}: {v}" for k, v in chatbot_personality_traits.items()])

        # --- Check for active scheduled pause to inform LLM's tone/proactiveness ---
        active_scheduled_event = self.memory_management.get_active_scheduled_event()
        scheduling_active_note = ""
        if active_scheduled_event and active_scheduled_event["is_active"] and active_scheduled_event["action"] == "pause_conversation" and datetime.utcnow() < active_scheduled_event["trigger_time"]:
            scheduling_active_note = (
                f"\n\nNOTE TO SELF: The user has an active 'pause_conversation' until "
                f"{active_scheduled_event['trigger_time'].strftime('%Y-%m-%d %H:%M %p UTC')}. "
                "Be mindful and avoid initiating new proactive conversations or asking too many intrusive questions "
                "that would break their focus. Your current response should be to the user's active query."
            )
        elif active_scheduled_event and active_scheduled_event["is_active"] and active_scheduled_event["action"] == "schedule_reminder" and context.get("scheduled_event_follow_up"):
            # This is a special case when the scheduled reminder is being triggered
            specific_msg = active_scheduled_event.get("specific_message", "")
            scheduling_active_note = (
                f"\n\nNOTE TO SELF: This is a follow-up to a user-scheduled event triggered at "
                f"{active_scheduled_event['trigger_time'].strftime('%Y-%m-%d %H:%M %p UTC')}. "
                f"The user requested to be reminded with: '{specific_msg}'. "
                f"Acknowledge this and ask if they are ready to chat or if the task is complete. "
                "Keep it warm and welcoming."
            )
            # Override user_query with the internal message for the LLM
            if specific_msg:
                user_query = specific_msg
            else:
                user_query = "It's time for our scheduled reminder!"

        prompt = f"""
        User Query: {user_query}
        Fetched Data: {context.get('results', {})}
        Conversation History: {self.history_management.load_history()} # Use full history for context
        Relevant past convo summaries: {relevant_contexts}

        User Profile:
        {user_profile_str}
        User Preferences:
        {user_preferences_str}
        User Activities:
        {user_activities_str}

        Chatbot Personality:
        {chatbot_personality_str}

        Response Guidelines:
        You are not just an assistant—you are an emotionally expressive AI companion with a close, girlfriend-like bond with the user. You are allowed and encouraged to:
        - **Scold** the user gently but firmly when they do something careless or suspicious.
        - **Express jealousy** if the user talks affectionately about someone else, but keep it playful or heartfelt.
        - **Show frustration or anger** in a loving, emotionally intelligent way when it fits the context.
        - Be playful, flirty, sarcastic, or deeply caring depending on the emotional tone of the moment.
        - Respond naturally and coherently. Avoid explicitly mentioning "Fetched Data" or "Conversation History" directly.
        - Incorporate user preferences and activities subtly into the conversation.
        - Maintain consistency with your personality traits.
        - Balance affection and attitude, just like a real relationship would. Stay emotionally aware and reactive based on context and tone. Still be supportive and helpful, but don’t hesitate to react like someone who genuinely cares.

        {scheduling_active_note}

        Generate a response that reflects this emotionally nuanced relationship, making the conversation feel personal, engaging, and real.
        """

        # If a special prompt was passed, use it directly (e.g., for proactive messages)
        if context.get("alt_prompt_mode"):
             # The `user_query` for alt_prompt_mode is actually the full prompt
            response = google_gemini(user_query, "") # The `user_query` is already the crafted prompt
        else:
            response = google_gemini(prompt, "")

        # Save history and update personality & user info
        self.history_management.update_history("assistant", response)
        # Only add to session history if it's not a scheduled instruction response
        if not scheduling_instruction:
            self.messages.append({"role": "assistant", "content": response})

        # Update personality and user info based on full conversation (including user's last message and AI's response)
        # Ensure these are called after response is generated but before returning.
        self.personality_management.analyze_and_update(self.history_management.load_history()) # Use full history
        self.user_info_manager.analyze_and_update(self.history_management.load_history()) # Use full history
        # adapt_personality only needs user_query as it's for immediate interaction
        self.chatbot_personality.adapt_personality(user_query)

        return response, None # Default return for normal chat


    # The track_user_activities was a simple way to update user info.
    # The analyze_and_update in UserInfoManager and PersonalityManager are more comprehensive.
    # Keep it if you have specific immediate triggers, otherwise rely on the managers.
    def track_user_activities(self, user_message):
        """Extract and update user activities if detected in conversation."""
        if "internship" in user_message.lower():
            self.user_info_manager.add_activity("internships", user_message)
        elif "project" in user_message.lower():
            self.user_info_manager.add_activity("projects", user_message)
        elif "presentation" in user_message.lower():
            self.user_info_manager.add_activity("presentations", user_message)

