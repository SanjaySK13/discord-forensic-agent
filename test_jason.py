import json

data = json.load(open(r'C:\Users\sanja\.gemini\antigravity\scratch\discord_scraper\discord_messages.json', encoding='utf-8'))
jason = data['authors']['1081956004020883518']
print(f"Jason total messages: {len(jason['messages'])}")
cap_count = 0
for m in jason['messages'][:20]:
    c = m.get('content', '')
    if c:
        print("  Jason:", c)
        if c[0].isupper():
            cap_count += 1
print(f"Jason capitalization rate: {cap_count}/20")

