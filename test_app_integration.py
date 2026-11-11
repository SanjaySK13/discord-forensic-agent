import sys
sys.path.insert(0, r"C:\Users\sanja\.gemini\antigravity\scratch\discord_scraper")
from server import app

client = app.test_client()
res = client.post("/api/predict", json={
    "channel_id": "1516697578107043850",
    "limit": 1000,
    "confession": """Okay so I gotta say this yo
Im writing this on behalf of my frd too cos he too felt like that lol~~

RADIANT gotta be one of the biggest pick me 🫩
Bro js acts and simps around girls of the server and it is lowkey blatant icl 😭✌️

And also yeah Obviously drools around shavvv goes behind her to every vc and shi 😂

Being in a sv with guys like these js icks me as a girl and honestly it's js cringe atp🫩🙏

Ts guy should stop acting and simping around girls of the server for real get a life 🤡"""
})

print("Server API Status:", res.status_code)
d = res.json.get("data", {})
print("Top 3 Rankings:")
for r in d.get("top_rankings", [])[:3]:
    print(f"  {r['display_name']} (@{r['username']}) -> Posterior: {r['posterior_probability_pct']}% | Composite: {r['composite_score']}")
    print(f"    Layers: {r['layer_breakdown']}")
    print(f"    Biometrics: {r['biometrics']}")
    print(f"    Negative Penalties: {r['negative_penalties']}")
    print(f"    Is Anomaly: {r['is_anomaly']}")

