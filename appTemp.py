import requests

def fetch_all_boxes():
    try:
        # Fetch all senseBoxes
        response = requests.get("https://api.opensensemap.org/boxes")
        response.raise_for_status()
        all_boxes = response.json()
        print(f"Number of senseBoxes fetched: {len(all_boxes)}")
        return all_boxes
    except requests.RequestException as e:
        print(f"API request failed: {e}")
        return None

if __name__ == "__main__":
    boxes = fetch_all_boxes()
    if boxes:
        print("First box data (sample):", boxes[0])  # Display details of the first box
