import json
import re

with open(r'C:\Users\sanja\.gemini\antigravity\scratch\discord_scraper\discord_messages.json', encoding='utf-8') as f:
    data = json.load(f)

# Let's inspect users that match any slang or tone
for aid, a in data['authors'].items():
    msgs = [m.get('content', '') for m in a['messages'] if m.get('content')]
    text = " \n ".join(msgs)
    
    # Let's look for:
    # - slang like icl, atp, lwk, lowk, lowkey, shi, ts, fr, frd, bro, yo, lol, sv, vc, simp, pick me, icks, cringe
    # - emojis like 🫩, 😭, ✌️, 😂, 🙏, 🤡, 💀, etc.
    # - punctuation like ~~, !!, ?, etc.
    found_clues = []
    if re.search(r'\b(ts|shi|icl|atp|frd|lwk|lowk|lowkey|sv|vc|simp|pick me|ick|cringe|fr)\b', text, re.I):
        matches = re.findall(r'\b(ts|shi|icl|atp|frd|lwk|lowk|lowkey|sv|vc|simp|pick me|ick|cringe|fr)\b', text, re.I)
        found_clues.append(f"Slang: {set(matches)}")
    
    found_emojis = [c for c in ['🫩', '✌️', '😭', '😂', '🙏', '🤡', '💀', '🙄', '✨'] if c in text]
    if found_emojis:
        found_clues.append(f"Emojis: {found_emojis}")
        
    if '~' in text:
        found_clues.append("Tilde usage")
        
    if found_clues:
        print(f"\n[{a['display_name']} / @{a['username']}] (Total: {len(msgs)} msgs)")
        for c in found_clues:
            print(f"  {c}")
        print("  Sample messages:")
        for m in msgs[:10]:
            print(f"    - {m}")

