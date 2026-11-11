import json

with open(r'C:\Users\sanja\.gemini\antigravity\scratch\discord_scraper\discord_messages.json', encoding='utf-8') as f:
    data = json.load(f)

targets = ['andman._', 'infinitebanger.', 'adarshjason', 'athimethavi_angurasu', 'leonerd_131110', 'aadiplays', 'pxnther006', 'mysticrock']

for t in targets:
    for aid, a in data['authors'].items():
        if a['username'] == t:
            msgs = [m.get('content', '') for m in a['messages'] if m.get('content')]
            print(f"\n========================================================")
            print(f"TARGET: {a['display_name']} (@{a['username']}) - Total: {len(msgs)}")
            print(f"========================================================")
            for i, m in enumerate(msgs):
                print(f"[{i+1}] {m}")

