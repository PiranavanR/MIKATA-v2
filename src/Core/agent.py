from Services.geolocation_service import GeoLocationService
from Services.weather_service import WeatherService
from Core.brain import Brain # Import Brain
from Services.time_service import get_current_datetime
from Services.search_service import SearchTools
import re
import time
import json # Added for parsing LLM output
import logging # Added for logging

logger = logging.getLogger(__name__)

def measure_time(func):
    """Decorator to measure the runtime of a function."""
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        logger.info(f"Execution time of {func.__name__}: {end_time - start_time:.6f} seconds")
        return result
    return wrapper

class Agent:
    def __init__(self, brain_instance: Brain): # Agent now takes a Brain instance
        """Initialize Intelligent Agent with LLM, geolocation, and weather services."""
        self.brain = brain_instance # Use the passed Brain instance
        self.geo_service = GeoLocationService()
        self.weather_service = WeatherService()
        self.search_tools = SearchTools()

    @measure_time
    # This method is what the telegram_bot.py will call.
    # It returns a tuple: (text_response, scheduling_instruction_dict_or_None)
    async def process_user_input(self, user_query: str) -> tuple[str, dict | None]:
        """
        Processes user query: determines required functions, executes them,
        and generates a final response or a scheduling instruction.
        """
        # Step 1: Determine if the user wants to call a function or just chat
        function_calls_or_chat = self.brain.subdivide_query_for_tools(user_query)
        
        results = {}
        scheduling_instruction = None

        if function_calls_or_chat == "general_chat":
            # No specific tool needed, proceed to general chat response
            pass
        elif isinstance(function_calls_or_chat, list) and function_calls_or_chat:
            # Found function calls, process them
            for func_call in function_calls_or_chat:
                func_name = func_call.get("name")
                func_args = func_call.get("arguments", {}) # Assuming LLM returns "arguments"

                if func_name == "schedule_conversation":
                    # This is a special instruction, don't execute it here.
                    # Just capture it and pass it up.
                    scheduling_instruction = {
                        "action": func_args.get("action"),
                        "time_expression": func_args.get("time_expression"),
                        "specific_message": func_args.get("specific_message")
                    }
                    # If scheduling, we short-circuit the execution of other functions
                    # and the general response generation.
                    # The brain will then generate a confirmation message.
                    logger.info(f"Agent detected scheduling instruction: {scheduling_instruction}")
                    # Break after finding scheduling instruction, as it's usually a standalone intent
                    break
                elif func_name == "general_chat": # Handle if general_chat is returned in a list
                    pass
                else:
                    # Execute other general service functions
                    try:
                        if func_name == "get_location":
                            results["location"] = self.geo_service.get_location()
                        elif func_name == "get_weather":
                            location = func_args.get("location")
                            if location:
                                # Prioritize explicit location, else use current location if available
                                results["weather"] = self.weather_service.get_weather_by_city(location)
                            elif "location" in results: # If get_location was called first
                                lat, lon = results["location"]["latitude"], results["location"]["longitude"]
                                results["weather"] = self.weather_service.get_weather(lat, lon)
                            else: # Fallback to current location if not explicitly provided
                                location_data = self.geo_service.get_location()
                                results["location"] = location_data
                                results["weather"] = self.weather_service.get_weather(location_data["latitude"], location_data["longitude"])
                        elif func_name == "get_current_datetime":
                            results["time"] = get_current_datetime()
                        elif func_name == "search_duckduckgo":
                            results['search'] = self.search_tools.search_duckduckgo(query=func_args.get("query"), max_results=func_args.get("max_results", 3))
                        elif func_name == "search_wikipedia":
                            results['wikipedia'] = self.search_tools.search_wikipedia(query=func_args.get("query"), char_limit=func_args.get("char_limit", 500))
                        else:
                            logger.warning(f"Unknown function requested: {func_name}")
                    except Exception as e:
                        logger.error(f"Error executing function {func_name}: {e}")
                        results[f"{func_name}_error"] = f"Failed to execute {func_name}."

        # If a scheduling instruction was found, bypass normal response generation
        if scheduling_instruction:
            # The Brain will generate a confirmation message based on this instruction
            confirmation_message, _ = self.brain.generate_response(user_query, {"scheduling_instruction": scheduling_instruction})
            return confirmation_message, scheduling_instruction
        else:
            # No scheduling instruction, proceed with normal response generation
            final_response_text, _ = self.brain.generate_response(user_query, {"results": results})
            return final_response_text, None