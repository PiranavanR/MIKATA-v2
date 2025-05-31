import asyncio
import sounddevice as sd
import numpy as np
import websockets
import json
from deepgram import Deepgram
from huggingface_hub import InferenceClient
from pymavlink import mavutil
import time

# Deepgram setup
DEEPGRAM_API_KEY = "your_deepgram_api_key"
dg_client = Deepgram(DEEPGRAM_API_KEY)

# LLaMA Intent Classifier
class Intent:
    def _init_(self):
        self.client = InferenceClient(
            provider="together",
            api_key="your_together_api_key"
        )
        self.messages = [
            {
                "role": "system",
                "content": "you are a command classification bot, classify the text into these: takeoff,landing,forward,backward,hover,return to home,turn right,turn left,move right,move left,vtol mode,fixed wing mode,increase speed,decrease speed,up,down. Reply only with the command."
            }
        ]

    def classify(self, text):
        self.messages.append({"role": "user", "content": text})
        completion = self.client.chat.completions.create(
            model="meta-llama/Meta-Llama-3-8B-Instruct",
            messages=self.messages,
            max_tokens=20
        )
        cmd = completion.choices[0].message.content.strip().lower()
        print(f"🎤 Voice Command Detected: {cmd}")
        return cmd

# Pixhawk Setup
print("🔌 Connecting to Pixhawk...")
master = mavutil.mavlink_connection('COM3', baud=57600)
master.wait_heartbeat()
print("✅ Pixhawk connected!")

def set_mode_guided():
    mode_id = master.mode_mapping()['GUIDED']
    master.set_mode(mode_id)

def arm_and_takeoff(altitude=10):
    print("⚙️ Arming...")
    master.mav.command_long_send(
        master.target_system, master.target_component,
        mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM,
        0, 1, 0, 0, 0, 0, 0, 0)
    master.motors_armed_wait()
    print("✅ Armed. Taking off...")

    master.mav.command_long_send(
        master.target_system, master.target_component,
        mavutil.mavlink.MAV_CMD_NAV_TAKEOFF,
        0, 0, 0, 0, 0, 0, 0, altitude)

def land():
    print("🛬 Landing...")
    master.mav.command_long_send(
        master.target_system, master.target_component,
        mavutil.mavlink.MAV_CMD_NAV_LAND,
        0, 0, 0, 0, 0, 0, 0, 0)

def move_forward(speed=1.0):
    print("⏩ Moving Forward...")
    master.mav.set_position_target_local_ned_send(
        0, master.target_system, master.target_component,
        mavutil.mavlink.MAV_FRAME_LOCAL_NED,
        int(0b110111000111),
        0, 0, 0,
        speed, 0, 0,
        0, 0, 0,
        0, 0)

# Router
def command_router(command):
    set_mode_guided()
    match command:
        case "takeoff":
            arm_and_takeoff()
        case "landing":
            land()
        case "forward":
            move_forward()
        case _:
            print(f"⚠️ Unknown or unsupported command: {command}")

# Voice Stream
async def listen():
    url = 'wss://api.deepgram.com/v1/listen?model=general'
    headers = {'Authorization': f'Token {DEEPGRAM_API_KEY}'}
    intent = Intent()

    async with websockets.connect(url, extra_headers=headers) as ws:
        print("🎙️ Listening... Speak your command.")
        sample_rate = 16000

        def callback(indata, frames, time, status):
            audio_data = indata[:, 0].tobytes()
            asyncio.run_coroutine_threadsafe(ws.send(audio_data), loop)

        with sd.InputStream(callback=callback, channels=1, samplerate=sample_rate, dtype='int16'):
            async for msg in ws:
                res = json.loads(msg)
                if 'channel' in res and 'alternatives' in res['channel']:
                    transcript = res['channel']['alternatives'][0]['transcript']
                    if transcript:
                        print(f"📝 Transcript: {transcript}")
                        command = intent.classify(transcript)
                        command_router(command)

# Start loop
loop = asyncio.get_event_loop()
loop.run_until_complete(listen())