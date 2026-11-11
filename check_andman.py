import json

data = json.load(open(r'C:\Users\sanja\.gemini\antigravity\scratch\discord_scraper\discord_messages.json', encoding='utf-8'))
andman = data['authors']['1550310146117206028']
print(f"andman total messages: {len(andman['messages'])}")
print("Sample of andman messages:")
for m in andman['messages'][:25]:
    c = m.get('content', '')
    if c:
        print("  ->", c)

