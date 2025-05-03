from datetime import datetime

def get_current_datetime():
    """Fetch the current date and time in a readable format."""
    now = datetime.now()
    return {
        "date": now.strftime("%Y-%m-%d"),
        "time": now.strftime("%H:%M:%S"),
        "day": now.strftime("%A")
    }

# Example usage:
print(get_current_datetime())
