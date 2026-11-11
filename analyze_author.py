"""
Stylometric Author Attribution Tool for Discord Messages
---------------------------------------------------------
Analyzes message histories across 5 stylometric markers to identify the most likely
author of a target confession/anonymous text.
"""

import json
import os
import re
from typing import Any, Dict, List, Tuple

CONFESSION_TEXT = """Okay so I gotta say this yo
Im writing this on behalf of my frd too cos he too felt like that lol~~

RADIANT gotta be one of the biggest pick me 🫩
Bro js acts and simps around girls of the server and it is lowkey blatant icl 😭✌️

And also yeah Obviously drools around shavvv goes behind her to every vc and shi 😂

Being in a sv with guys like these js icks me as a girl and honestly it's js cringe atp🫩🙏

Ts guy should stop acting and simping around girls of the server for real get a life 🤡"""

# Specific target stylistic markers extracted from confession
SLANG_TARGETS = [
    r"\bjs\b",        # "js" for "just"
    r"\bfrd\b",       # "frd" for "friend"
    r"\bcos\b",       # "cos" for "because"
    r"\bshi\b",       # "shi" for "shit"
    r"\bicl\b",       # "icl" for "i can't lie"
    r"\batp\b",       # "atp" for "at this point"
    r"\bts\b",        # "ts" for "this / this shit"
    r"\bsv\b",        # "sv" for "server"
    r"\blowkey\b",    # "lowkey"
    r"\bpick me\b",   # "pick me"
    r"\bvc\b",        # "vc" for "voice channel"
    r"\bicks?\b",     # "ick / icks"
    r"\bsimps?\b",    # "simp / simps"
    r"\byo\b",        # "yo"
]

TARGET_EMOJIS = ["🫩", "😭", "✌️", "😂", "🙏", "🤡"]
TARGET_PUNCT = ["~~", "  "]  # tilde trailing, spacing quirks


def analyze_user(user_data: Dict[str, Any]) -> Dict[str, Any]:
    messages = [m.get("content", "") for m in user_data.get("messages", []) if m.get("content")]
    all_text = " \n ".join(messages)

    if not messages:
        return {"score": 0.0, "matches": {}, "quotes": []}

    matches = {
        "slang": {},
        "emojis": {},
        "punctuation": {},
        "capitalization": {},
        "phrases": {}
    }

    # 1. Slang & Shortcut Analysis
    slang_score = 0
    for pattern in SLANG_TARGETS:
        found = re.findall(pattern, all_text, flags=re.IGNORECASE)
        word = pattern.replace(r"\b", "")
        if found:
            matches["slang"][word] = len(found)
            slang_score += len(found) * 3

    # Check for uncontracted "Im" (without apostrophe)
    im_count = len(re.findall(r"\bIm\b", all_text))
    if im_count > 0:
        matches["slang"]["Im (no apostrophe)"] = im_count
        slang_score += im_count * 2

    # 2. Punctuation Cadence
    punct_score = 0
    for p in TARGET_PUNCT:
        cnt = all_text.count(p)
        if cnt > 0:
            matches["punctuation"][p] = cnt
            punct_score += cnt * 4

    # 3. Emoji Selection & Combos
    emoji_score = 0
    for emo in TARGET_EMOJIS:
        cnt = all_text.count(emo)
        if cnt > 0:
            matches["emojis"][emo] = cnt
            # 🫩 is rare/specific, weight higher
            weight = 8 if emo == "🫩" else 2
            emoji_score += cnt * weight

    # 4. Phrase/Grammar Matches
    phrase_score = 0
    phrases = ["pick me", "get a life", "as a girl", "drools around", "for real"]
    for ph in phrases:
        cnt = len(re.findall(r"\b" + re.escape(ph) + r"\b", all_text, flags=re.IGNORECASE))
        if cnt > 0:
            matches["phrases"][ph] = cnt
            phrase_score += cnt * 5

    total_score = slang_score + punct_score + emoji_score + phrase_score

    # Normalized score relative to total messages
    normalized_score = total_score / (len(messages) ** 0.5) if messages else 0.0

    # Extract relevant evidence quotes
    evidence_quotes = []
    interesting_terms = list(matches["slang"].keys()) + list(matches["emojis"].keys()) + ["~~", "pick me"]
    for msg in messages:
        if any(term in msg.lower() or term in msg for term in interesting_terms):
            evidence_quotes.append(msg)
            if len(evidence_quotes) >= 5:
                break

    return {
        "author_id": user_data.get("author_id"),
        "username": user_data.get("username"),
        "display_name": user_data.get("display_name"),
        "message_count": len(messages),
        "raw_score": total_score,
        "score": normalized_score,
        "matches": matches,
        "quotes": evidence_quotes
    }


def run_attribution(data_path: str):
    if not os.path.exists(data_path):
        print(f"[X] Error: File {data_path} not found.")
        return

    with open(data_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    authors = data.get("authors", {})
    if not authors:
        print("[X] No authors found in data.")
        return

    results = []
    for uid, user_data in authors.items():
        res = analyze_user(user_data)
        results.append(res)

    results.sort(key=lambda x: x["score"], reverse=True)

    print("=" * 80)
    print("STYLOMETRIC AUTHOR ATTRIBUTION RANKINGS")
    print("=" * 80)
    total_top_score = sum(r["score"] for r in results[:3]) or 1.0

    for idx, r in enumerate(results[:3], start=1):
        confidence = (r["score"] / total_top_score) * 100 if total_top_score > 0 else 0
        print(f"\n#{idx}: {r['display_name']} (@{r['username']}) - Confidence: {confidence:.1f}%")
        print(f"    Raw Match Score: {r['raw_score']} (Messages Analyzed: {r['message_count']})")
        print(f"    Slang matches: {r['matches'].get('slang')}")
        print(f"    Emoji matches: {r['matches'].get('emojis')}")
        print(f"    Punctuation matches: {r['matches'].get('punctuation')}")
        print(f"    Sample Quotes from Chat History:")
        if r["quotes"]:
            for q in r["quotes"]:
                print(f"      - \"{q.strip()}\"")
        else:
            print("      (No direct stylistic trigger quotes found)")


if __name__ == "__main__":
    import sys
    path = sys.argv[1] if len(sys.argv) > 1 else "discord_messages.json"
    run_attribution(path)

