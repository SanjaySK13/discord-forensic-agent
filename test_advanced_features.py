import json
import math
import re
from collections import Counter
import numpy as np

with open(r"C:\Users\sanja\.gemini\antigravity\scratch\discord_scraper\discord_messages.json", encoding="utf-8") as f:
    corpus = json.load(f)

confession = """Okay so I gotta say this yo
Im writing this on behalf of my frd too cos he too felt like that lol~~

RADIANT gotta be one of the biggest pick me 🫩
Bro js acts and simps around girls of the server and it is lowkey blatant icl 😭✌️

And also yeah Obviously drools around shavvv goes behind her to every vc and shi 😂

Being in a sv with guys like these js icks me as a girl and honestly it's js cringe atp🫩🙏

Ts guy should stop acting and simping around girls of the server for real get a life 🤡"""

# Contraction drop pairs
DROP_PAIRS = [
    ("im", "i'm"), ("dont", "don't"), ("cant", "can't"), ("its", "it's"),
    ("thats", "that's"), ("youre", "you're"), ("didnt", "didn't"), ("wont", "won't")
]

def get_drop_ratio(txt):
    dr = sum(len(re.findall(r"\b" + p[0] + r"\b", txt, re.I)) for p in DROP_PAIRS)
    fm = sum(len(re.findall(r"\b" + re.escape(p[1]) + r"\b", txt, re.I)) for p in DROP_PAIRS)
    return dr / (dr + fm) if (dr + fm) > 0 else 0.5

conf_drop_ratio = get_drop_ratio(confession)

# Build corpus token stats for Zipfian Surprisal
all_corpus_tokens = []
for a in corpus["authors"].values():
    for m in a["messages"]:
        c = m.get("content", "")
        toks = re.findall(r"[\U0001F1E0-\U0001FAFF\u2000-\u3300]+|[A-Za-z0-9_']+|[~]{2,}|[!]{2,}|\?{2,}|\.{2,}|[^\s\w]", c)
        all_corpus_tokens.extend([t.lower() for t in toks])

total_tokens = len(all_corpus_tokens)
corpus_freq = Counter(all_corpus_tokens)

# Confession tokens
conf_tokens = [t.lower() for t in re.findall(r"[\U0001F1E0-\U0001FAFF\u2000-\u3300]+|[A-Za-z0-9_']+|[~]{2,}|[!]{2,}|\?{2,}|\.{2,}|[^\s\w]", confession)]
conf_token_set = set(conf_tokens)

# Also detect compound emojis in confession
conf_compounds = re.findall(r"[\U0001F1E0-\U0001FAFF\u2000-\u3300][\s]*[\U0001F1E0-\U0001FAFF\u2000-\u3300]", confession)

# Process each author
results = []
for aid, a in corpus["authors"].items():
    msgs = [m.get("content", "") for m in a["messages"] if m.get("content")]
    text = " \n ".join(msgs)
    msg_count = len(msgs)
    
    # 1. Author tokens
    a_tokens = [t.lower() for t in re.findall(r"[\U0001F1E0-\U0001FAFF\u2000-\u3300]+|[A-Za-z0-9_']+|[~]{2,}|[!]{2,}|\?{2,}|\.{2,}|[^\s\w]", text)]
    a_token_set = set(a_tokens)
    
    # 2. Shared tokens and Zipfian Surprisal sum
    shared_tokens = conf_token_set.intersection(a_token_set)
    surprisal_sum = 0.0
    shared_rare_details = {}
    
    for tok in shared_tokens:
        cnt = corpus_freq.get(tok, 0)
        # Surprisal formula
        I_w = math.log2((total_tokens + 1) / (cnt + 1))
        # Ignore extremely common stopwords like "the", "and", "a" from surprisal dominance
        if tok not in {"the", "and", "to", "of", "a", "in", "it", "is", "for", "on", "her", "she", "he", "at", "as"}:
            surprisal_sum += I_w
            if I_w > 8.0:
                shared_rare_details[tok] = round(I_w, 2)
                
    # Check compound emojis
    for comp in conf_compounds:
        comp_clean = re.sub(r"\s+", "", comp)
        if comp_clean in re.sub(r"\s+", "", text):
            # Compound emojis have massive information surprisal
            surprisal_sum += 25.0
            shared_rare_details[comp_clean] = 25.0

    # 3. Orthographic Biometrics: Apostrophe Drop Ratio & Spacing
    a_drop_ratio = get_drop_ratio(text)
    sim_drop = 1.0 - abs(a_drop_ratio - conf_drop_ratio)
    
    # Spacing around tildes
    has_tilde_space_conf = bool(re.search(r"\s~+", confession))
    has_tilde_space_author = bool(re.search(r"\s~+", text))
    sim_spacing = 1.0 if (has_tilde_space_conf == has_tilde_space_author) else 0.8
    
    # Non-standard clause delimiters (| or // or --)
    has_pipe_conf = "|" in confession
    has_pipe_author = "|" in text
    
    # 4. Negative Constraint Hard-Penalties (Process of Elimination)
    # If candidate has N > 120 messages and exhibits 0 occurrences of a mandatory habit
    penalty = 1.0
    negative_reasons = []
    
    if msg_count > 120:
        # If confession drops apostrophes, but author has 100% formal apostrophe usage
        if conf_drop_ratio > 0.4 and a_drop_ratio < 0.15:
            penalty *= (1.0 - 0.35)
            negative_reasons.append("Strict formal apostrophe usage across >120 msgs")
        # If confession uses non-standard separators (|) and author with >150 msgs has 0
        if has_pipe_conf and not has_pipe_author:
            penalty *= (1.0 - 0.40)
            negative_reasons.append("Zero pipe delimiter usage across >120 msgs")
            
    # 5. Adversarial Disguise & Mimicry Detection
    # If an author has low message count or only shares 1 isolated slang token without broader alignment
    is_anomaly = False
    if len(shared_rare_details) == 1 and msg_count < 25:
        # Single isolated loud slang without structural depth
        is_anomaly = True
        surprisal_sum *= 0.5  # Dampen isolated catchphrase

    # 6. Sample Volume Credibility Sigmoid
    credibility = 1.0 / (1.0 + math.exp(-(msg_count - 25.0) / 10.0))
    
    # 7. Synergy Multiplier
    k_hits = len(shared_rare_details)
    synergy = 1.0 + 0.35 * max(0, k_hits - 1) if k_hits > 0 else 0.0
    
    final_score = (surprisal_sum * synergy * credibility * penalty * sim_spacing) + (sim_drop * 10.0)
    
    results.append({
        "username": a["username"],
        "display_name": a["display_name"],
        "msg_count": msg_count,
        "shared_rare_count": k_hits,
        "shared_rare_details": shared_rare_details,
        "drop_ratio": round(a_drop_ratio, 2),
        "surprisal_sum": round(surprisal_sum, 2),
        "penalty": round(penalty, 2),
        "is_anomaly": is_anomaly,
        "final_score": round(final_score, 2)
    })

results.sort(key=lambda x: x["final_score"], reverse=True)

# Softmax temperature scaling
scores = np.array([r["final_score"] for r in results])
mean_s = np.mean(scores)
std_s = np.std(scores) if np.std(scores) > 1e-6 else 1.0
z = (scores - mean_s) / std_s
T = 1.2
p = (np.exp(z / T) / np.sum(np.exp(z / T))) * 100

print("--- ADVANCED FORENSIC ATTRIBUTION RESULTS ---")
for i, r in enumerate(results[:5]):
    r["posterior"] = round(float(p[i]), 1)
    print(f"\n#{i+1}: {r['display_name']} (@{r['username']}) -> Posterior: {r['posterior']}% (Score: {r['final_score']})")
    print(f"    Shared Rare Tokens: {r['shared_rare_details']}")
    print(f"    Drop Ratio: {r['drop_ratio']} | Penalty: {r['penalty']} | Is Anomaly: {r['is_anomaly']}")
