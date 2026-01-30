import requests
import json

API_URL = "http://localhost:8000/api/v1"

def test_persistence():
    # 1. Create Data (via processed text)
    print("\n1. Creating Data (Simulating AI Process)...")
    text_payload = {"text": "Yarın saat 5'te Ahmet ile tenis maçı var."}
    resp = requests.post(f"{API_URL}/audio/process-text", json=text_payload)
    if resp.status_code == 200:
        print("Create Success:", resp.json()["summary"])
    else:
        print("Create Failed:", resp.text)
        return

    # 2. Fetch Data (Verify Persistence)
    print("\n2. Fetching Data from DB...")
    resp = requests.get(f"{API_URL}/actions/")
    if resp.status_code == 200:
        actions = resp.json()
        print(f"Fetch Success: Found {len(actions)} actions")
        print(json.dumps(actions, indent=2, ensure_ascii=False))
        
        # 3. Delete Data (Cleanup)
        if actions:
            last_id = actions[0]["id"]
            print(f"\n3. Deleting Action ID: {last_id}...")
            del_resp = requests.delete(f"{API_URL}/actions/{last_id}")
            if del_resp.status_code == 200:
                print("Delete Success")
            else:
                print("Delete Failed:", del_resp.text)
    else:
        print("Fetch Failed:", resp.text)

if __name__ == "__main__":
    test_persistence()
