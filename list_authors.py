import json

with open(r'C:\Users\sanja\.gemini\antigravity\scratch\discord_scraper\discord_messages.json', encoding='utf-8') as f:
    data = json.load(f)

authors = data['authors']
authors_sorted = sorted(authors.values(), key=lambda a: a['message_count'], reverse=True)

print(f"{'Username':<25} | {'Display Name':<25} | {'Count':<5}")
print("-" * 65)
for a in authors_sorted:
    print(f"{a['username']:<25} | {a['display_name']:<25} | {a['message_count']:<5}")

