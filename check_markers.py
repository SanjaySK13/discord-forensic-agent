import json

data = json.load(open(r'C:\Users\sanja\.gemini\antigravity\scratch\discord_scraper\discord_messages.json', encoding='utf-8'))

print("=== CHECKING FOR PEACE SIGN ✌ IN ALL 984 MESSAGES ===")
found_peace = 0
for aid, a in data['authors'].items():
    text = ' '.join(m.get('content', '') for m in a.get('messages', []))
    if '✌' in text:
        found_peace += 1
        print(f"FOUND in {a.get('display_name')} (@{a.get('username')}) [total msgs: {len(a.get('messages', []))}]:")
        for m in a.get('messages', []):
            if '✌' in m.get('content', ''):
                print("   ->", m.get('content'))
if found_peace == 0:
    print("NO AUTHOR in the 984 cached messages has used ✌!")

print("\n=== CHECKING FOR 'scared' or 'scsred' ===")
for aid, a in data['authors'].items():
    for m in a.get('messages', []):
        c = m.get('content', '').lower()
        if 'scared' in c or 'scsred' in c:
            print(f"FOUND in {a.get('display_name')} (@{a.get('username')}): {m.get('content')}")

print("\n=== CHECKING FOR 'ASFUCK' or 'asfuck' or 'fuck' ===")
for aid, a in data['authors'].items():
    for m in a.get('messages', []):
        c = m.get('content', '').lower()
        if 'asfuck' in c or 'asf' in c.split():
            print(f"FOUND ASF/ASFUCK in {a.get('display_name')} (@{a.get('username')}): {m.get('content')}")

print("\n=== CHECKING FOR 'Ts' or 'ts' ===")
for aid, a in data['authors'].items():
    for m in a.get('messages', []):
        c = m.get('content', '')
        words = c.split()
        if any(w.lower() == 'ts' for w in words):
            print(f"FOUND TS in {a.get('display_name')} (@{a.get('username')}): {m.get('content')}")

