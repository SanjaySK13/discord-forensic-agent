import json
import os
import sys

# Add directory to sys.path
sys.path.insert(0, r"C:\Users\sanja\.gemini\antigravity\scratch\discord_scraper")

from server import app

client = app.test_client()

# 1. Test GET /
res_home = client.get("/")
print("GET / status:", res_home.status_code)
assert res_home.status_code == 200

# 2. Test GET /api/status
res_status = client.get("/api/status")
print("GET /api/status:", res_status.json)
assert res_status.status_code == 200

# 3. Test POST /api/predict
confession = """Okay so I gotta say this yo
Im writing this on behalf of my frd too cos he too felt like that lol~~

RADIANT gotta be one of the biggest pick me 🫩
Bro js acts and simps around girls of the server and it is lowkey blatant icl 😭✌️

And also yeah Obviously drools around shavvv goes behind her to every vc and shi 😂

Being in a sv with guys like these js icks me as a girl and honestly it's js cringe atp🫩🙏

Ts guy should stop acting and simping around girls of the server for real get a life 🤡"""

res_predict = client.post("/api/predict", json={
    "channel_id": "1516697578107043850",
    "limit": 1000,
    "confession": confession
})
print("POST /api/predict status:", res_predict.status_code)
assert res_predict.status_code == 200
data = res_predict.json.get("data", {})
print("Used cache:", data.get("used_cache"))
print("Total analyzed msgs:", data.get("total_messages_analyzed"))
print("Top 3 Rankings:")
for r in data.get("top_rankings", [])[:3]:
    print(f"  {r['display_name']} (@{r['username']}) - Confidence: {r['confidence_pct']}% - Score: {r['overall_score']}")
    print(f"    Slang: {r['breakdown']['slang_matches']}")
    print(f"    Emojis: {r['breakdown']['emoji_matches']}")

print("\nAll unit tests passed successfully!")

