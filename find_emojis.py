import json

with open(r'C:\Users\sanja\.gemini\antigravity\scratch\discord_scraper\discord_messages.json', encoding='utf-8') as f:
    data = json.load(f)

print("--- EMOJI OCCURRENCES ---")
for aid, a in data['authors'].items():
    for m in a['messages']:
        c = m.get('content', '')
        for char in ['✌️', '✌', '🫩', '😂', '🙏', '🤡', '😭']:
            if char in c:
                print(f"[{char}] {a['display_name']} (@{a['username']}): {c}")

