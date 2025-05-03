import openai
import time
from google import genai
import requests
import os
from dotenv import load_dotenv

load_dotenv()
NOVITA_API_KEY = os.getenv("NOVITA_API_KEY")
DEEPINFRA_API_KEY = os.getenv("DEEPINFRA_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

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

    openai.api_key = NOVITA_API_KEY
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
            return response['choices'][0]['message']['content']
    else:
        print(response['choices'][0]['message']['content'])
        return response['choices'][0]['message']['content']

@measure_time
def google_gemini(system_prompt: str, user_prompt: str, model: str = "gemini-2.0-flash"):
    """Send system and user prompt to Google Gemini API and print the response."""

    genai_client = genai.Client(api_key=GEMINI_API_KEY)
    contents = [
        {"role": "user", "parts": [{"text": system_prompt}]},
        {"role": "user", "parts": [{"text": user_prompt}]}
    ]

    response = genai_client.models.generate_content(
        model=model,
        contents=contents
    )

    print(response.text)
    return response.text

@measure_time
def deepinfra(system_prompt: str, user_prompt: str, model: str = "meta-llama/Llama-2-13b-chat-hf", stream: bool = False):
    """Send system and user prompt to DeepInfra API and print the response."""

    openai.api_key = DEEPINFRA_API_KEY
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
            return chunk['choices'][0]['delta'].get('content', '')
    else:
        print(response['choices'][0]['message']['content'])
        return response['choices'][0]['message']['content']
        #print(response['usage']['prompt_tokens'], response['usage']['completion_tokens'])

@measure_time
def openrouter_llama4_maverick(system_prompt: str, user_prompt: str, image_url: str = None):
    """Send system and user prompt (optionally with image) to Meta LLaMA 4 Maverick via OpenRouter."""

    api_key = OPENROUTER_API_KEY
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
        return result['choices'][0]['message']['content']
    else:
        print(f"Error {response.status_code}: {response.text}")
