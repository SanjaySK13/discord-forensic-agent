import json

with open(r'C:\Users\sanja\.gemini\antigravity\scratch\discord_scraper\discord_messages.json', encoding='utf-8') as f:
    data = json.load(f)

for aid, a in data['authors'].items():
    msgs = [m.get('content', '') for m in a['messages'] if m.get('content')]
    if a['message_count'] <= 35:
        print(f"\n[{a['display_name']} / @{a['username']}] ({len(msgs)} msgs)")
        for m in msgs:
            print(f"   {m}")

