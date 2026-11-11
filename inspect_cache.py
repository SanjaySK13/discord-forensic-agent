import json

data = json.load(open(r'C:\Users\sanja\.gemini\antigravity\scratch\discord_scraper\discord_messages.json', encoding='utf-8'))
print("Total authors:", len(data['authors']))
for aid, a in list(data['authors'].items())[:12]:
    print(f"{a.get('display_name')} (@{a.get('username')}): {len(a.get('messages', []))} msgs")
    for m in a.get('messages', [])[:2]:
        print("   ", m.get('timestamp'), "->", m.get('content'))

