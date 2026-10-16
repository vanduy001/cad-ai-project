import requests, os

key = os.environ.get("OPENROUTER_API_KEY", "")
if not key:
    print("CHUA SET OPENROUTER_API_KEY")
    exit()

r = requests.get(
    "https://openrouter.ai/api/v1/models",
    headers={"Authorization": f"Bearer {key}"}
)
free = [
    m for m in r.json()["data"]
    if m.get("pricing", {}).get("prompt") == "0"
    and m.get("pricing", {}).get("completion") == "0"
]
print(f"Tim thay {len(free)} model free:\n")
for m in free:
    print(m["id"])