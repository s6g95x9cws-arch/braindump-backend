import requests
import json

API_URL = "http://localhost:8000/api/v1/audio/process-text"

def test_brain_dump():
    sample_text = "Yarın saat 3'te Mehmet ile kahve içeceğim, bu arada eve gelirken kedi maması almalıyım."
    
    print(f"Sending text: {sample_text}")
    print("-" * 50)
    
    try:
        response = requests.post(API_URL, json={"text": sample_text})
        if response.status_code == 200:
            data = response.json()
            print("SUCCESS! AI Response:")
            print(json.dumps(data, indent=2, ensure_ascii=False))
        else:
            print(f"FAILED: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"Error: {e}")
        print("Make sure the backend is running! (python app/main.py)")

if __name__ == "__main__":
    test_brain_dump()
