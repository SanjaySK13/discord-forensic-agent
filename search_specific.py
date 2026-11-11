import json
import re

with open(r'C:\Users\sanja\.gemini\antigravity\scratch\discord_scraper\discord_messages.json', encoding='utf-8') as f:
    data = json.load(f)

print("--- SPECIFIC TOKEN SEARCH ---")
for aid, a in data['authors'].items():
    u = a['username']
    dn = a['display_name']
    for m in a['messages']:
        content = m.get('content', '')
        if re.search(r'\bjs\b', content, re.I):
            print(f"[JS] {dn} (@{u}): {content}")
        if '🫩' in content:
            print(f"[EMOJI 🫩] {dn} (@{u}): {content}")
        if '🤡' in content:
            print(f"[CLOWN] {dn} (@{u}): {content}")
        if 'atp' in content.lower():
            print(f"[ATP] {dn} (@{u}): {content}")
        if 'frd' in content.lower():
            print(f"[FRD] {dn} (@{u}): {content}")
        if 'pick me' in content.lower():
            print(f"[PICK ME] {dn} (@{u}): {content}")
        if 'cringe' in content.lower():
            print(f"[CRINGE] {dn} (@{u}): {content}")
        if 'blatant' in content.lower():
            print(f"[BLATANT] {dn} (@{u}): {content}")
        if 'drool' in content.lower():
            print(f"[DROOL] {dn} (@{u}): {content}")

