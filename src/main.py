print("Importing libraries to main...")
from RealtimeSTT import AudioToTextRecorder
from Core.agent import Agent
print("Loading Brain...")
agent = Agent()
print("Brain loaded successfully")

def process_query (text):
    #recorder.stop()
    result = agent.execute_functions(text)
    print(result)
    if result == "exit":
        return 'exit'
    elif result:
        return True
    else:
        return False
"""
if __name__ == '__main__':
    print("Wait until it says 'speak now'")
    recorder = AudioToTextRecorder()
    print("Recorder Initialised")
    try:
        while True:
            print("Entered While loop")
            text = recorder.text()
            print("Got the audio Input")
            print(text)
            if text:
                print("Processing Query")
                if process_query(text):
                    break 
    except Exception as e:
        print(f"An error occurred: {e}")"""
while True:
    inp = input("->")
    if process_query(inp) == 'exit':
        print("Closing...")
        break