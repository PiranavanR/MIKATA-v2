from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import time

class GeoLocationService:
    """Get the location information"""
    def __init__(self):
        pass

    def get_location(self):
        """Fetch the current latitude and longitude using Selenium and Google Maps."""
        print("Fetching location...")
        driver = webdriver.Chrome()
        driver.get("https://www.google.com/maps")

        time.sleep(3)
        search_box = driver.find_element("name", "q")
        search_box.send_keys("My Location")
        search_box.send_keys(Keys.RETURN)

        time.sleep(5)
        current_url = driver.current_url
        driver.quit()

        if "@" in current_url:
            coords = current_url.split("@")[1].split(",")[:2]
            print(coords)
            return {"latitude": coords[0],"longitude": coords[1]}
        return None, None
    
