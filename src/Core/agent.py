from Services.geolocation_service import GeoLocationService
from Services.weather_service import WeatherService
from Core.brain import Brain
from Services.time_service import get_current_datetime
from Services.search_service import SearchTools
import re
import time

def measure_time(func):
    """Decorator to measure the runtime of a function."""
    def wrapper(*args, **kwargs):
        start_time = time.time()  # Start timer
        result = func(*args, **kwargs)  # Run the function
        end_time = time.time()  # End timer
        print(f"Execution time of {func.__name__}: {end_time - start_time:.6f} seconds\n")
        return result
    return wrapper

class Agent:
    def __init__(self):
        """Initialize Intelligent Agent with LLM, geolocation, and weather services."""
        self.llm = Brain()
        self.geo_service = GeoLocationService()
        self.weather_service = WeatherService()
        self.search_tools = SearchTools()

    @measure_time
    def execute_functions(self, user_query):
        """Determines required functions using LLM and executes them in order."""
        results = {}
        function_list = self.llm.subdivide_query(user_query).split("\n")
        print(function_list)

        if function_list[0] == "exit":
            return "exit"

        def extract_function_details(call_str):
            """Extracts function name and parameters safely using regex."""
            match = re.match(r"(\w+)\((.*)\)", call_str)

            if match:
                function_name = match.group(1)
                param_str = match.group(2).strip()

                params = {}
                if param_str:
                    param_pairs = param_str.split(",")  
                    for pair in param_pairs:
                        key, value = pair.split("=")
                        key = key.strip()
                        value = value.strip().strip("'").strip('"')  # Remove extra spaces and quotes
                        
                        # Convert numbers properly
                        if value.isdigit():
                            value = int(value)

                        params[key] = value
                return function_name, params
            
            else:
                # Handle cases where there are no parameters (e.g., "general_chat")
                return call_str.strip(), {}

        for index, function_call in enumerate(function_list):
            is_last = (index == len(function_list) - 1)  # Check if it's the last function

            try:
                function_name, params = extract_function_details(function_call)
            except Exception as e:
                print(f"Error parsing function call: {e}")
                continue  # Skip execution if parsing fails

            if function_name == "general_chat":
                pass# Simply return general chat mode

            elif function_name == "get_location":
                results["location"] = self.geo_service.get_location()
                print(results)

            elif function_name == "get_weather":
                if "location" in results:
                    latitude, longitude = results["location"]["latitude"], results["location"]["longitude"]
                else:
                    location = self.geo_service.get_location()
                    latitude, longitude = location["latitude"], location["longitude"]
                    results["location"] = location

                results["weather"] = self.weather_service.get_weather(latitude, longitude)

            elif function_name == "get_current_datetime":
                results["time"] = get_current_datetime()

            elif function_name == "search_duckduckgo":
                results['search'] = self.search_tools.search_duckduckgo(**params)  # Pass extracted params

            elif function_name == "search_wikipedia":
                results['wikipedia'] = self.search_tools.search_wikipedia(**params)  # Pass extracted params

        final_response = self.llm.generate_response(user_query, results)
        return final_response
