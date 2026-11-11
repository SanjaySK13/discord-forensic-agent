import json

data = json.load(open(r'C:\Users\sanja\.gemini\antigravity\scratch\discord_scraper\discord_messages.json', encoding='utf-8'))

for aid, a in data['authors'].items():
    msgs = [m.get('content', '') for m in a.get('messages', []) if m.get('content')]
    text = ' \n '.join(msgs).lower()
    matches = []
    if 'scared' in text or 'scsred' in text:
        matches.append('SCARED/SCSRED')
    if 'holy' in text:
        matches.append('HOLY')
    if 'asfuck' in text or 'asf' in text.split():
        matches.append('ASF')
    if 'bro' in text.split():
        matches.append('BRO')
    if 'ts' in text.split():
        matches.append('TS')
    if matches:
        print(f"{a.get('display_name')} (@{a.get('username')}): msgs={len(msgs)} -> {matches}")

