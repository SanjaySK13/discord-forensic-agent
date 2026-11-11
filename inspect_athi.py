import json

with open(r'C:\Users\sanja\.gemini\antigravity\scratch\discord_scraper\discord_messages.json', encoding='utf-8') as f:
    data = json.load(f)

for aid, a in data['authors'].items():
    if a['username'] == 'athimethavi_angurasu':
        print(f"Author: {a['display_name']} (@{a['username']})")
        for i, m in enumerate(a['messages']):
            content = m.get('content', '')
            if '✌' in content or '😭' in content or 'lowkey' in content or 'drool' in content or 'shi' in content:
                print(f"[{i}] ({m.get('timestamp')}): {content}")

