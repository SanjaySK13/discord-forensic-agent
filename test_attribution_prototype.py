import json, re, math
from collections import Counter
import numpy as np

data = json.load(open(r'C:\Users\sanja\.gemini\antigravity\scratch\discord_scraper\discord_messages.json', encoding='utf-8'))
authors_data = data['authors']

# Expanded English stopwords that shouldn't count as idiolect surprisal
COMMON_VOCAB = {
    "the", "and", "to", "of", "a", "in", "that", "is", "it", "i", "you", "for", "on", "with",
    "he", "she", "as", "at", "this", "but", "his", "by", "from", "they", "we", "say", "her",
    "or", "an", "will", "my", "one", "all", "would", "there", "their", "what", "so", "up",
    "out", "if", "about", "who", "get", "which", "go", "me", "when", "make", "can", "like",
    "time", "no", "just", "him", "know", "take", "people", "into", "year", "your", "good",
    "some", "could", "them", "see", "other", "than", "then", "now", "look", "only", "come",
    "its", "over", "think", "also", "back", "after", "use", "two", "how", "our", "work",
    "first", "well", "way", "even", "new", "want", "because", "any", "these", "give", "day",
    "most", "us", "are", "was", "were", "been", "has", "have", "had", "do", "does", "did",
    "why", "someone", "reason", "hates", "hate", "entire", "situation", "funny", "jealous",
    "holy", "unlike", "supporters", "admitted", "much", "very", "should", "told", "really",
    "something", "anything", "nothing", "everything", "anyone", "everyone", "being", "been",
    "said", "then", "more", "where", "here", "each", "both", "such", "own", "same", "tell",
    "be", "cant", "can't", "don't", "dont", "im", "i'm", "t", "s", "d", "m", "ll", "ve", "re"
}

KNOWN_SLANG = {
    "ts", "js", "bro", "asfuck", "asf", "af", "frd", "icl", "lwk", "lowkey", "shi", "sv", "vc",
    "atp", "rn", "ngl", "wth", "wtf", "lmao", "omg", "smh", "fr", "nah", "bruh", "yo", "lol",
    "cringe", "pick me", "simp", "simping", "icks", "drools", "scsred", "ouuu", "huh", "tsundere"
}

EMOJI_PATTERN = re.compile(
    "["
    "\U0001F1E0-\U0001FAFF"
    "\u2000-\u3300"
    "]+",
    flags=re.UNICODE
)

def levenshtein(s1, s2):
    if len(s1) < len(s2):
        return levenshtein(s2, s1)
    if len(s2) == 0:
        return len(s1)
    prev = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        curr = [i + 1]
        for j, c2 in enumerate(s2):
            ins = prev[j + 1] + 1
            dels = curr[j] + 1
            subs = prev[j] + (c1 != c2)
            curr.append(min(ins, dels, subs))
        prev = curr
    return prev[-1]

def evaluate(confession_text):
    print("=" * 60)
    print("ANALYZING:", confession_text[:80] + "...")
    print("=" * 60)

    conf_words = [w for w in re.findall(r"\b[a-zA-Z]+\b", confession_text.lower()) if len(w) > 1 and w not in COMMON_VOCAB or w in KNOWN_SLANG]
    conf_emojis = EMOJI_PATTERN.findall(confession_text)

    sentences = [s.strip() for s in re.split(r"[.!?\n]+", confession_text) if s.strip()]
    conf_cap_rate = sum(1 for s in sentences if s[0].isupper()) / max(len(sentences), 1)

    # Global corpus stats for confession words
    all_authors_text = {}
    for aid, a in authors_data.items():
        all_authors_text[aid] = " \n ".join(m.get("content", "") for m in a.get("messages", []) if m.get("content")).lower()

    scores = {}

    for aid, a in authors_data.items():
        msgs = [m.get("content", "") for m in a.get("messages", []) if m.get("content")]
        full_text = all_authors_text[aid]
        author_tokens = re.findall(r"\b\w+\b|[^\w\s]", full_text)
        author_words = [w for w in re.findall(r"\b[a-zA-Z]+\b", full_text)]
        author_words_set = set(author_words)
        total_tokens = len(author_tokens)

        matched_markers = {}
        for w in conf_words:
            # Check exact match
            if w in author_words_set:
                # Count how many authors in the entire server have this word
                author_freq = sum(1 for text in all_authors_text.values() if w in text.split())
                surprisal = 25.0 / (author_freq + 0.5)  # Higher weight for exclusive/rare words
                matched_markers[w] = round(surprisal, 1)
            else:
                # Check typo / fuzzy Levenshtein distance <= 1 for words of len >= 5
                if len(w) >= 5:
                    for aw in author_words_set:
                        if len(aw) >= 5 and abs(len(aw) - len(w)) <= 1:
                            if levenshtein(w, aw) == 1:
                                author_freq = sum(1 for text in all_authors_text.values() if aw in text.split())
                                surprisal = 30.0 / (author_freq + 0.5)  # Exclusive typo is massive fingerprint!
                                matched_markers[f"{aw} (typo for {w})"] = round(surprisal, 1)
                                break

        # Check emojis & emoji compounds
        for em in conf_emojis:
            if em in full_text:
                matched_markers[em] = 22.0
            else:
                for char in em:
                    if char in full_text and char in ["✌", "✌️", "🫩", "🤡", "🙏", "😭"]:
                        matched_markers[f"partial:{char}"] = 8.0

        # Check shout compounds (e.g. ASFUCK, WTF)
        has_shout_curse_conf = bool(re.search(r"\b[A-Z]{3,}\b", confession_text))
        has_shout_curse_author = bool(re.search(r"\b[A-Z]{3,}\b", " \n ".join(msgs)))
        if has_shout_curse_conf and has_shout_curse_author:
            matched_markers["ALL_CAPS_EXP"] = 8.0

        surprisal_sum = sum(matched_markers.values())
        # Information density:
        surprisal_density = surprisal_sum / math.log(total_tokens + 15) if total_tokens > 0 else 0.0

        # Capitalization match
        author_sentences = [s.strip() for s in re.split(r"[.!?\n]+", " \n ".join(msgs)) if s.strip()]
        a_cap_rate = sum(1 for s in author_sentences if s[0].isupper()) / max(len(author_sentences), 1)
        sim_case = 1.0 - abs(a_cap_rate - conf_cap_rate)

        # Multi-marker synergy
        k_hits = len(matched_markers)
        synergy = 1.0 + 0.35 * max(0, k_hits - 1) if k_hits > 0 else 0.40

        penalty = 1.0
        if len(msgs) > 40:
            if conf_cap_rate > 0.8 and a_cap_rate < 0.2:
                penalty *= 0.50

        composite = (surprisal_density * 2.5 + sim_case * 0.8) * synergy * penalty

        scores[aid] = {
            "display_name": a.get("display_name"),
            "username": a.get("username"),
            "message_count": len(msgs),
            "surprisal_density": round(surprisal_density, 3),
            "matched_markers": matched_markers,
            "sim_case": round(sim_case, 2),
            "penalty": penalty,
            "composite": round(composite, 4)
        }

    raw_comp = [v["composite"] for v in scores.values()]
    mean_c = np.mean(raw_comp)
    std_c = np.std(raw_comp) if np.std(raw_comp) > 1e-6 else 1.0
    z = [(c - mean_c) / std_c for c in raw_comp]
    exp_z = [math.exp(x / 0.9) for x in z]
    total_exp = sum(exp_z)
    probs = [round(x / total_exp * 100.0, 1) for x in exp_z]

    ranked = list(scores.values())
    for i, p in enumerate(probs):
        ranked[i]["prob"] = p

    ranked.sort(key=lambda x: x["composite"], reverse=True)

    print("TOP 5 RANKED:")
    for r in ranked[:5]:
        print(f"#{ranked.index(r)+1}: {r['display_name']} (@{r['username']}) - {r['prob']}% (Score: {r['composite']}, msgs: {r['message_count']})")
        print(f"    Matches: {r['matched_markers']}")
        print(f"    SimCase: {r['sim_case']}, Penalty: {r['penalty']}")

    for idx, r in enumerate(ranked):
        if 'radiant' in r['display_name'].lower() or '6564' in r['username']:
            print(f"-> RADIANT Rank: #{idx+1} ({r['prob']}%)")

confession_radiant = """You just admitted you are scared of me😅✌️. There is a reason why no one hates me and I have supporters unlike you 🤪✌️. Ts entire situation is funny ASFUCK. Someone can't be this jealous bro holy fuck."""
evaluate(confession_radiant)

confession_1 = """Okay so I gotta say this yo
Im writing this on behalf of my frd too cos he too felt like that lol~~

RADIANT gotta be one of the biggest pick me 🫩
Bro js acts and simps around girls of the server and it is lowkey blatant icl 😭✌️

And also yeah Obviously drools around shavvv goes behind her to every vc and shi 😂

Being in a sv with guys like these js icks me as a girl and honestly it's js cringe atp🫩🙏

Ts guy should stop acting and simping around girls of the server for real get a life 🤡"""
evaluate(confession_1)
