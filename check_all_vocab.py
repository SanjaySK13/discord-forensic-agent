import json
import re

with open(r'C:\Users\sanja\.gemini\antigravity\scratch\discord_scraper\discord_messages.json', encoding='utf-8') as f:
    data = json.load(f)

print("--- SEARCHING VOCABULARY ACROSS ALL USERS ---")

vocab = [
    'yo', 'frd', 'cos', 'lol', 'pick me', 'bro', 'js', 'simp', 'lowkey', 'lwk', 'lowk', 'blatant', 
    'icl', 'drool', 'drools', 'shavvv', 'shav', 'vc', 'shi', 'sv', 'ick', 'icks', 'cringe', 'atp', 
    'ts', 'for real', 'fr', 'get a life', 'obviously', 'obvi', 'as a girl', 'girl', 'girls'
]

user_vocab_counts = {}

for aid, a in data['authors'].items():
    u = a['username']
    msgs = [m.get('content', '') for m in a['messages'] if m.get('content')]
    text = " \n ".join(msgs)
    
    counts = {}
    for w in vocab:
        c = len(re.findall(r'\b' + re.escape(w) + r'\b', text, re.I))
        if c > 0:
            counts[w] = c
            
    # Also check emojis:
    emojis_found = {}
    for emo in ['🫩', '😭', '✌️', '😂', '🙏', '🤡', '🥰', '😍', '🔥', '💀']:
        c = text.count(emo)
        if c > 0:
            emojis_found[emo] = c
            
    if counts or emojis_found:
        user_vocab_counts[u] = {
            'display': a['display_name'],
            'total_msgs': len(msgs),
            'counts': counts,
            'emojis': emojis_found
        }

for u, d in sorted(user_vocab_counts.items(), key=lambda x: len(x[1]['counts']), reverse=True):
    if len(d['counts']) > 0 or len(d['emojis']) > 0:
        print(f"\nUser: {d['display']} (@{u}) - Total Msgs: {d['total_msgs']}")
        print(f"  Vocab Matches: {d['counts']}")
        print(f"  Emoji Matches: {d['emojis']}")

