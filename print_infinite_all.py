import json

with open(r'C:\Users\sanja\.gemini\antigravity\scratch\discord_scraper\discord_messages.json', encoding='utf-8') as f:
    data = json.load(f)

for aid, a in data['authors'].items():
    if a['username'] == 'infinitebanger.':
        print(f"Author: {a['display_name']} (@{a['username']}) - Total: {len(a['messages'])}")
        for i, m in enumerate(a['messages']):
            print(f"[{i+1}] {m.get('content')}")

