import os
import requests

def fetch_wallpapers():
    print("Fetching wallpapers from API...")
    # Simulating API call
    wallpapers = [
        {"name": "Mountain Lake", "url": "https://images.unsplash.com/photo-1464822759023-fed622ff2c3b"},
        {"name": "City Lights", "url": "https://images.unsplash.com/photo-1477959858617-67f85cf4f1df"},
    ]
    
    if not os.path.exists("downloads"):
        os.makedirs("downloads")
        
    for wp in wallpapers:
        print(f"Downloading {wp['name']}...")
        # In a real app, we would download the image here
        # response = requests.get(wp['url'])
        # with open(f"downloads/{wp['name']}.jpg", "wb") as f:
        #     f.write(response.content)
        print(f"Finished downloading {wp['name']}")

if __name__ == "__main__":
    fetch_wallpapers()
