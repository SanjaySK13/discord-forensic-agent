import json

with open(r'C:\Users\sanja\.gemini\antigravity\scratch\discord_scraper\discord_messages.json', encoding='utf-8') as f:
    data = json.load(f)

users_to_inspect = ['andman._', 'athimethavi_angurasu', 'skepticalstonner', 'kinderholic', 'urmommy333', 'infinitebanger.']

for u in users_to_inspect:
    for aid, a in data['authors'].items():
        if a['username'] == u:
            print(f"\n=======================================================")
            print(f"USER: {a['display_name']} (@{u}) - ID: {aid}")
            print(f"=======================================================")
            msgs = [m.get('content', '') for m in a['messages'] if m.get('content')]
            for i, m in enumerate(msgs):
                # Filter for interesting messages
                print(f"[{i+1}] {m}")

