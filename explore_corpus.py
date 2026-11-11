import json
import re

with open(r'C:\Users\sanja\.gemini\antigravity\scratch\discord_scraper\discord_messages.json', encoding='utf-8') as f:
    data = json.load(f)

authors = data['authors']

print("Searching for mentions of 'shav' or 'shavvv':")
for aid, a in authors.items():
    for m in a['messages']:
        content = m.get('content', '')
        if re.search(r'shav', content, re.IGNORECASE):
            print(f"[{a['display_name']} / @{a['username']}]: {content}")

print("\nSearching for mentions of 'radiant':")
for aid, a in authors.items():
    for m in a['messages']:
        content = m.get('content', '')
        if re.search(r'radiant', content, re.IGNORECASE):
            print(f"[{a['display_name']} / @{a['username']}]: {content}")

print("\nSearching for 'js' or 'jst' or 'jus':")
for aid, a in authors.items():
    for m in a['messages']:
        content = m.get('content', '')
        if re.search(r'\b(js|jst|jus)\b', content, re.IGNORECASE):
            print(f"[{a['display_name']} / @{a['username']}]: {content}")

print("\nSearching for 'frd':")
for aid, a in authors.items():
    for m in a['messages']:
        content = m.get('content', '')
        if re.search(r'\bfrd\b', content, re.IGNORECASE):
            print(f"[{a['display_name']} / @{a['username']}]: {content}")

print("\nSearching for 'ick' or 'cringe':")
for aid, a in authors.items():
    for m in a['messages']:
        content = m.get('content', '')
        if re.search(r'\b(ick|icks|cringe)\b', content, re.IGNORECASE):
            print(f"[{a['display_name']} / @{a['username']}]: {content}")

print("\nSearching for 'simp' or 'simps' or 'simping':")
for aid, a in authors.items():
    for m in a['messages']:
        content = m.get('content', '')
        if re.search(r'\bsimp', content, re.IGNORECASE):
            print(f"[{a['display_name']} / @{a['username']}]: {content}")

print("\nSearching for '~~':")
for aid, a in authors.items():
    for m in a['messages']:
        content = m.get('content', '')
        if '~~' in content or '~' in content:
            print(f"[{a['display_name']} / @{a['username']}]: {content}")

