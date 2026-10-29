import os
import json
import urllib.request
import urllib.error

from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY")

if not api_key:
    print("ERROR: GOOGLE_API_KEY was not found in .env")
    raise SystemExit(1)

url = (
    "https://generativelanguage.googleapis.com/"
    "v1beta/models?key=" + api_key
)

print("Testing Google Gemini API connectivity...")

request = urllib.request.Request(
    url,
    headers={"Accept": "application/json"},
)

try:
    with urllib.request.urlopen(request, timeout=15) as response:
        print(f"HTTP status: {response.status}")

        data = json.loads(response.read().decode("utf-8"))
        models = data.get("models", [])

        print(f"Models returned: {len(models)}")

        for model in models[:10]:
            print("-", model.get("name", "Unknown model"))

        print("\nAPI connectivity and authentication succeeded.")

except urllib.error.HTTPError as error:
    print(f"HTTP status: {error.code}")
    print(error.read().decode("utf-8", errors="replace")[:1000])
    print("\nCheck the API key, permissions, and API configuration.")

except Exception as error:
    print(f"{type(error).__name__}: {error}")
    print("\nCheck your network connection and try again.")