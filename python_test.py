import requests
import json

# ---------------- Config ----------------
API_KEY = "wrong-key"  # intentionally wrong for testing
SESSION_ID = "test-session-123"
URL = "http://127.0.0.1:8000/chat/stream"

conversation = [
    {"role": "user", "content": "Hello!"},
]

headers = {
    "Content-Type": "application/json",
    "x-session-id": SESSION_ID,
    "X-API-KEY": API_KEY,
}

payload = {"conversation": conversation}

assistant_text = ""  # define it outside

with requests.post(URL, headers=headers, json=payload, stream=True) as response:
    if response.status_code != 200:
        print(f"Error: {response.status_code} - {response.text}")
    else:
        for line in response.iter_lines():
            if not line:
                continue
            decoded = line.decode("utf-8")
            if decoded.startswith("data: "):
                data = decoded[len("data: "):].strip()
                if data == "[DONE]":
                    break
                try:
                    chunk = json.loads(data)
                    delta = chunk.get("content", "")
                    if delta:
                        assistant_text += delta
                        print("Chunk:", delta)
                except json.JSONDecodeError:
                    continue

print("\nFull Assistant Response:\n", assistant_text)
