import json
import re

with open(r'C:\Users\sanja\.gemini\antigravity\scratch\discord_scraper\discord_messages.json', encoding='utf-8') as f:
    data = json.load(f)

authors = data['authors']
print(f'Total authors: {len(authors)}')

keywords = ['js', 'frd', 'cos', 'shi', 'icl', 'atp', 'ts', 'sv', 'lowkey', 'lowk', 'lwk', 'pick me', 'vc', 'ick', 'simp', 'yo', 'shav', 'radiant', 'drool', 'cringe', 'blatant', 'fr']
emojis = ['🫩', '✌️', '😭', '😂', '🙏', '🤡']

scores = []

for aid, a in authors.items():
    text = ' \n '.join(m.get('content', '') for m in a['messages'])
    found_kw = {}
    for kw in keywords:
        matches = len(re.findall(r'\b' + re.escape(kw) + r'\b', text, re.IGNORECASE))
        if matches:
            found_kw[kw] = matches
    found_emo = {}
    for emo in emojis:
        c = text.count(emo)
        if c:
            found_emo[emo] = c
    tilde = text.count('~~')
    if tilde:
        found_kw['~~'] = tilde
    
    # Check specific quotes or distinctive phrases
    score = 0
    # Weights for specific markers:
    # 🫩 is extremely specific
    if '🫩' in text:
        score += found_emo.get('🫩', 0) * 50
    if 'frd' in found_kw:
        score += found_kw['frd'] * 40
    if 'icl' in found_kw:
        score += found_kw['icl'] * 25
    if 'atp' in found_kw:
        score += found_kw['atp'] * 25
    if 'js' in found_kw:
        score += found_kw['js'] * 15
    if 'shi' in found_kw:
        score += found_kw['shi'] * 15
    if 'ts' in found_kw:
        score += found_kw['ts'] * 15
    if '~~' in found_kw:
        score += found_kw['~~'] * 30
    if 'sv' in found_kw:
        score += found_kw['sv'] * 20
    if 'cos' in found_kw:
        score += found_kw['cos'] * 20
    if 'cringe' in found_kw:
        score += found_kw['cringe'] * 10
    if 'pick me' in found_kw:
        score += found_kw['pick me'] * 25

    for emo, cnt in found_emo.items():
        if emo != '🫩':
            score += cnt * 2

    scores.append({
        'aid': aid,
        'username': a['username'],
        'display_name': a['display_name'],
        'message_count': a['message_count'],
        'score': score,
        'kw': found_kw,
        'emo': found_emo,
        'messages': [m.get('content', '') for m in a['messages'] if m.get('content')]
    })

scores.sort(key=lambda x: x['score'], reverse=True)

print("\n--- TOP 10 CANDIDATES BY SCORE ---")
for s in scores[:10]:
    print(f"\nUser: {s['display_name']} (@{s['username']}) [ID: {s['aid']}] - Score: {s['score']} (Msg Count: {s['message_count']})")
    print(f"  Keywords: {s['kw']}")
    print(f"  Emojis: {s['emo']}")
