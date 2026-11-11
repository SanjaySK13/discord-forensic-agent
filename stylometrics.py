"""
Advanced Stylometric Author Attribution Engine for Discord Messages
-------------------------------------------------------------------
Extracts stylistic fingerprints dynamically from a target confession text
and scores all authors in the scraped Discord corpus across 5 core dimensions:
1. Contraction habits & informal slang shortcuts
2. Punctuation cadence
3. Capitalization quirks
4. Emoji selection, placement & combinations
5. Sentence structure, vocabulary & tone
"""

import math
import re
from typing import Any, Dict, List, Set, Tuple

# Comprehensive slang dictionary & regex patterns for Internet / Discord culture
COMMON_SLANG_PATTERNS = [
    r"\bjs\b", r"\bfrd\b", r"\bcos\b", r"\bcus\b", r"\bcuz\b", r"\bshi\b", r"\bshyt\b",
    r"\bicl\b", r"\batp\b", r"\bts\b", r"\bsv\b", r"\bvc\b", r"\blowkey\b", r"\blowk\b",
    r"\blwk\b", r"\bpick me\b", r"\bicks?\b", r"\bsimps?\b", r"\bsimping\b", r"\byo\b",
    r"\bbro\b", r"\bfr\b", r"\bfrfr\b", r"\bngl\b", r"\bidk\b", r"\bidek\b", r"\btbh\b",
    r"\brn\b", r"\bblatant\b", r"\bcringe\b", r"\bdrools?\b", r"\bobv\b", r"\bobvi\b",
    r"\bobviously\b", r"\bget a life\b", r"\bshavvv?\b", r"\bradiant\b", r"\bdih\b",
    r"\bwby\b", r"\bwbu\b", r"\bwyd\b", r"\blyk\b", r"\bistg\b", r"\bikr\b", r"\bikrr\b"
]

EMOJI_PATTERN = re.compile(
    "["
    "\U0001F1E0-\U0001F1FF"
    "\U0001F300-\U0001F5FF"
    "\U0001F600-\U0001F64F"
    "\U0001F680-\U0001F6FF"
    "\U0001F700-\U0001F77F"
    "\U0001F780-\U0001F7FF"
    "\U0001F800-\U0001F8FF"
    "\U0001F900-\U0001F9FF"
    "\U0001FA00-\U0001FAFF"
    "\U00002702-\U000027B0"
    "\U000024C2-\U0001F251"
    "\u2000-\u3300"
    "]+",
    flags=re.UNICODE
)

DISCORD_CUSTOM_EMOTE_REGEX = re.compile(r"<a?:[a-zA-Z0-9_]+:([0-9]+)>")


def extract_confession_features(text: str) -> Dict[str, Any]:
    """Dynamically extracts all stylistic cues present in the confession text."""
    # 1. Slang & Keywords
    found_slang = []
    for pat in COMMON_SLANG_PATTERNS:
        matches = re.findall(pat, text, flags=re.IGNORECASE)
        if matches:
            found_slang.append((pat, len(matches)))

    # Also detect any unusual words or abbreviations
    words = re.findall(r"\b[A-Za-z']+\b", text)
    custom_tokens = set()
    for w in words:
        wl = w.lower()
        if len(wl) <= 6 and wl not in {"the", "and", "for", "with", "from", "that", "this", "are", "you", "was", "her", "his", "around", "every"}:
            custom_tokens.add(wl)

    # 2. Emojis and Clusters
    raw_emoji_tokens = EMOJI_PATTERN.findall(text)
    individual_emojis = []
    for tok in raw_emoji_tokens:
        for char in tok:
            if ord(char) > 255:
                individual_emojis.append(char)

    return {
        "text": text,
        "slang": found_slang,
        "custom_tokens": custom_tokens,
        "emojis": list(set(individual_emojis)),
        "emoji_clusters": [tok for tok in raw_emoji_tokens if len(tok) > 1],
        "punctuation": {
            "tildes": len(re.findall(r"~+", text)),
            "multiple_exclamations": len(re.findall(r"!{2,}", text)),
            "multiple_questions": len(re.findall(r"\?{2,}", text)),
            "missing_apostrophes": len(re.findall(r"\b(im|dont|cant|wont|didnt|youre|ure)\b", text, flags=re.IGNORECASE)),
            "double_spaces": len(re.findall(r"  ", text)),
            "no_terminal_period": not text.strip().endswith(".")
        },
        "all_caps_words": [w for w in words if w.isupper() and len(w) > 1],
        "mid_sentence_caps": [
            w for line in text.split("\n") for w in line.strip().split()[1:]
            if w and w[0].isupper() and not w.isupper() and w not in {"I", "God"}
        ]
    }


def analyze_author_match(
    author_data: Dict[str, Any],
    conf_features: Dict[str, Any]
) -> Dict[str, Any]:
    """Compares one author's messages against the confession's feature set."""
    messages = [m.get("content", "") for m in author_data.get("messages", []) if m.get("content")]
    all_text = " \n ".join(messages)

    if not messages:
        return {
            "author_id": author_data.get("author_id"),
            "username": author_data.get("username"),
            "display_name": author_data.get("display_name"),
            "message_count": 0,
            "overall_score": 0.0,
            "marker_scores": {},
            "evidence": []
        }

    evidence_quotes: List[Dict[str, Any]] = []

    # 1. Slang & Contraction Matches (Weight: 35%)
    slang_score = 0.0
    slang_matches = {}
    for pat, count in conf_features["slang"]:
        clean_name = pat.replace(r"\b", "").replace("s?", "")
        found = re.findall(pat, all_text, flags=re.IGNORECASE)
        if found:
            # Rarity weight: rare slang scores higher
            weight = 8.0 if clean_name in {"icl", "frd", "atp", "ts", "shi"} else 3.0
            slang_score += len(found) * weight
            slang_matches[clean_name] = len(found)

    # 2. Emoji & Combo Matches (Weight: 30%)
    emoji_score = 0.0
    emoji_matches = {}
    for emo in set(conf_features["emojis"]):
        cnt = all_text.count(emo)
        if cnt > 0:
            weight = 15.0 if emo in {"🫩", "✌️", "🤡", "✌"} else 4.0
            emoji_score += cnt * weight
            emoji_matches[emo] = cnt

    # Check for exact multi-emoji sequences (e.g. 😭 ✌️ or 😭✌️)
    for cluster in conf_features["emoji_clusters"]:
        cluster_clean = re.sub(r"\s+", "", cluster)
        if cluster_clean in re.sub(r"\s+", "", all_text):
            emoji_score += 45.0
            emoji_matches[f"combo: {cluster_clean}"] = 1

    # 3. Punctuation Cadence (Weight: 15%)
    punct_score = 0.0
    punct_matches = {}
    if conf_features["punctuation"]["tildes"] > 0:
        t_cnt = all_text.count("~")
        if t_cnt > 0:
            punct_score += min(t_cnt * 5.0, 20.0)
            punct_matches["tildes (~)"] = t_cnt

    # 4. Capitalization & Quirks (Weight: 10%)
    caps_score = 0.0
    caps_matches = {}
    for cap_word in conf_features["all_caps_words"]:
        if re.search(r"\b" + re.escape(cap_word) + r"\b", all_text):
            caps_score += 5.0
            caps_matches[cap_word] = 1

    for mid_cap in conf_features["mid_sentence_caps"]:
        if re.search(r"\b" + re.escape(mid_cap) + r"\b", all_text):
            caps_score += 4.0
            caps_matches[mid_cap] = 1

    # 5. Tone & Vocabulary Overlap (Weight: 10%)
    vocab_score = 0.0
    vocab_matches = {}
    for tok in conf_features["custom_tokens"]:
        matches = len(re.findall(r"\b" + re.escape(tok) + r"\b", all_text, flags=re.IGNORECASE))
        if matches > 0:
            vocab_score += min(matches * 1.5, 6.0)
            vocab_matches[tok] = matches

    # Collect direct quotation evidence
    keywords_to_quote = list(slang_matches.keys()) + list(emoji_matches.keys()) + list(caps_matches.keys())
    for msg in messages:
        matched_tags = []
        for kw in keywords_to_quote:
            clean_kw = kw.replace("combo: ", "")
            if clean_kw in msg or (len(clean_kw) > 1 and re.search(r"\b" + re.escape(clean_kw) + r"\b", msg, flags=re.IGNORECASE)):
                matched_tags.append(clean_kw)
        if matched_tags:
            evidence_quotes.append({
                "message": msg,
                "matched_markers": list(set(matched_tags))
            })
            if len(evidence_quotes) >= 8:
                break

    # Total raw score
    raw_score = slang_score + emoji_score + punct_score + caps_score + vocab_score

    # Damping / Normalization by message volume so high-frequency talkers don't dominate purely on noise
    normalized_score = raw_score / (math.log(len(messages) + 2)) if messages else 0.0

    return {
        "author_id": author_data.get("author_id"),
        "username": author_data.get("username"),
        "display_name": author_data.get("display_name"),
        "message_count": len(messages),
        "raw_score": round(raw_score, 2),
        "overall_score": round(normalized_score, 2),
        "marker_scores": {
            "slang": round(slang_score, 1),
            "emoji": round(emoji_score, 1),
            "punctuation": round(punct_score, 1),
            "capitalization": round(caps_score, 1),
            "vocabulary": round(vocab_score, 1)
        },
        "breakdown": {
            "slang_matches": slang_matches,
            "emoji_matches": emoji_matches,
            "punct_matches": punct_matches,
            "caps_matches": caps_matches,
            "vocab_matches": dict(list(vocab_matches.items())[:8])
        },
        "evidence": evidence_quotes
    }


def predict_confession_author(
    corpus: Dict[str, Any],
    confession_text: str
) -> Dict[str, Any]:
    """Runs full attribution across all authors in the corpus."""
    conf_features = extract_confession_features(confession_text)
    authors = corpus.get("authors", {})

    results = []
    for aid, a_data in authors.items():
        res = analyze_author_match(a_data, conf_features)
        if res["message_count"] > 0:
            results.append(res)

    results.sort(key=lambda x: x["overall_score"], reverse=True)

    # Calculate softmax / proportional confidence percentages for top 5
    top_candidates = results[:5]
    total_top_score = sum(c["overall_score"] for c in top_candidates) or 1.0

    for c in top_candidates:
        c["confidence_pct"] = round((c["overall_score"] / total_top_score) * 100, 1) if total_top_score > 0 else 0.0

    return {
        "confession_features": {
            "slang_count": len(conf_features["slang"]),
            "emojis_found": conf_features["emojis"],
            "all_caps": conf_features["all_caps_words"],
            "custom_tokens": list(conf_features["custom_tokens"])[:15]
        },
        "total_authors_analyzed": len(results),
        "total_messages_analyzed": sum(r["message_count"] for r in results),
        "top_rankings": top_candidates,
        "all_rankings": results
    }
