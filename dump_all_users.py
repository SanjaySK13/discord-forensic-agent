import json

with open(r'C:\Users\sanja\.gemini\antigravity\scratch\discord_scraper\discord_messages.json', encoding='utf-8') as f:
    data = json.load(f)

authors = data['authors']

# Let's inspect users with > 5 messages and all female-identifying or suspicious users
for aid, a in authors.items():
    msgs = [m.get('content', '') for m in a['messages'] if m.get('content')]
    if len(msgs) > 0:
        print(f"\n==================================================")
        print(f"USER: {a['display_name']} (@{a['username']}) - ID: {aid} - Msg Count: {len(msgs)}")
        print(f"==================================================")
        for m in msgs[:25]: # print up to 25 messages
            print(f"  > {m}")

