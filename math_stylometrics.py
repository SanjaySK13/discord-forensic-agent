"""
Mathematical Attribution Engine & Hybrid AI Backend (Advanced Forensic Architecture)
====================================================================================
Implements:
1. Negative Constraint Hard-Penalties (Process of Elimination via Prior Penalization)
2. Orthographic Structural Biometrics (Keystroke, Spacing, Capitalization & Contraction Drop Ratio R_drop)
3. Rare-Token Zipfian Surprisal with Author-Frequency Scaling & Levenshtein Typo Fingerprinting
4. Density Normalization to eliminate document-length chatter volume bias
5. Regularized Burrows' Delta & Sub-Word Character 3-5 Gram TF-IDF Cosine
6. Deep Semantic Vector Embeddings (Sentence Transformers all-MiniLM-L6-v2)
7. Calibrated Bayesian Softmax Posterior Probabilities
"""

import math
import os
import re
from collections import Counter
from typing import Any, Dict, List, Optional, Set, Tuple

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Set environment variables for offline transformer loading
os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
os.environ["DO_NOT_TRACK"] = "1"
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

# SMP Emoji Pattern (Unicode 15/16 + Emoticons + Dingbats)
EMOJI_PATTERN = re.compile(
    "["
    "\U0001F1E0-\U0001FAFF"
    "\U00002702-\U000027B0"
    "\U000024C2-\U0001F251"
    "\u2000-\u3300"
    "]+",
    flags=re.UNICODE
)

FUNCTION_WORDS = [
    "the", "and", "to", "of", "a", "in", "that", "is", "it", "i", "you", "for", "on", "with",
    "he", "she", "as", "at", "this", "but", "his", "by", "from", "they", "we", "say", "her",
    "or", "an", "will", "my", "one", "all", "would", "there", "their", "what", "so", "up",
    "out", "if", "about", "who", "get", "which", "go", "me", "when", "make", "can", "like",
    "time", "no", "just", "him", "know", "take", "people", "into", "year", "your", "good",
    "some", "could", "them", "see", "other", "than", "then", "now", "look", "only", "come",
    "its", "over", "think", "also", "back", "after", "use", "two", "how", "our", "work",
    "first", "well", "way", "even", "new", "want", "because", "any", "these", "give", "day",
    "most", "us", "are", "was", "were", "been", "has", "have", "had", "do", "does", "did"
]

CONTRACTION_PAIRS = [
    ("im", "i'm"), ("dont", "don't"), ("cant", "can't"), ("its", "it's"),
    ("thats", "that's"), ("youre", "you're"), ("didnt", "didn't"), ("wont", "won't"),
    ("isnt", "isn't"), ("hes", "he's"), ("shes", "she's"), ("theyre", "they're")
]

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

_TRANSFORMER_MODEL = None
_AUTHOR_EMBEDDINGS_CACHE = {}


def get_embedding_model():
    """Lazily loads SentenceTransformer model from local cache snapshot."""
    global _TRANSFORMER_MODEL
    if _TRANSFORMER_MODEL is not None:
        return _TRANSFORMER_MODEL

    snapshot_path = os.path.expanduser(
        r"~/.cache/huggingface/hub/models--sentence-transformers--all-MiniLM-L6-v2/snapshots/1110a243fdf4706b3f486440f8e97a38cb694fa7"
    )

    try:
        from sentence_transformers import SentenceTransformer
        if os.path.exists(snapshot_path):
            _TRANSFORMER_MODEL = SentenceTransformer(snapshot_path, local_files_only=True)
        else:
            _TRANSFORMER_MODEL = SentenceTransformer("all-MiniLM-L6-v2", local_files_only=True)
    except Exception as e:
        print(f"[!] SentenceTransformer offline loading fallback: {e}")
        _TRANSFORMER_MODEL = False

    return _TRANSFORMER_MODEL


def levenshtein_dist(s1: str, s2: str) -> int:
    """Computes Levenshtein edit distance between two strings."""
    if len(s1) < len(s2):
        return levenshtein_dist(s2, s1)
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


# =========================================================================
# LAYER 1: Forensic Tokenization & Descriptive Stylometrics
# =========================================================================

def tokenize_forensic(text: str) -> List[str]:
    """Forensic regex tokenizer capturing contractions, emojis, and symbols."""
    token_pattern = re.compile(
        r"(?:[a-zA-Z]+'[a-zA-Z]+)"
        r"|(?:[a-zA-Z]+)"
        r"|[\U0001F1E0-\U0001FAFF\u2000-\u3300]"
        r"|(?:~{2,}|\!{2,}|\?{2,}|\.{2,}|\|{1,}|-{2,}|/{2,})"
        r"|[^\w\s]",
        flags=re.UNICODE
    )
    return token_pattern.findall(text)


def compute_contraction_drop_ratio(text: str) -> float:
    """Calculates Contraction Apostrophe Drop Rate R_drop."""
    text_lower = text.lower()
    words = set(re.findall(r"\b[a-z']+\b", text_lower))

    dropped_count = 0
    standard_count = 0

    for dropped, standard in CONTRACTION_PAIRS:
        if dropped in words:
            dropped_count += 1
        if standard in words:
            standard_count += 1

    total = dropped_count + standard_count
    return round(dropped_count / total, 3) if total > 0 else 0.5


def compute_descriptive_stylometrics(tokens: List[str], raw_text: str) -> Dict[str, Any]:
    """Calculates Yule's K, Shannon Entropy, Clause stats, Punctuation/Case ratios."""
    N = len(tokens)
    if N == 0:
        return {
            "yules_k": 0.0,
            "shannon_entropy": 0.0,
            "mean_clause_len": 0.0,
            "std_clause_len": 0.0,
            "skew_clause_len": 0.0,
            "punct_ratio": 0.0,
            "case_ratio": 0.0,
            "drop_ratio": 0.5,
            "cap_rate": 0.5
        }

    tok_counts = Counter(t.lower() for t in tokens)
    m1 = N
    m2 = sum(c * c for c in tok_counts.values())
    yules_k = 10000.0 * (m2 - m1) / (m1 * m1) if m1 > 1 else 0.0

    shannon_entropy = 0.0
    for count in tok_counts.values():
        p = count / N
        shannon_entropy -= p * math.log2(p)

    clauses = [c.strip() for c in re.split(r"[,;:\n|]+|\.\.\.", raw_text) if c.strip()]
    clause_lens = [len(c.split()) for c in clauses if len(c.split()) > 0]
    if clause_lens:
        arr_lens = np.array(clause_lens, dtype=np.float64)
        mean_len = float(np.mean(arr_lens))
        std_len = float(np.std(arr_lens))
        skew_len = float(np.mean(((arr_lens - mean_len) / (std_len + 1e-6)) ** 3))
    else:
        mean_len, std_len, skew_len = 0.0, 0.0, 0.0

    punct_count = len(re.findall(r"[^\w\s]", raw_text))
    punct_ratio = punct_count / max(len(raw_text), 1)

    upper_count = sum(1 for c in raw_text if c.isupper())
    lower_count = sum(1 for c in raw_text if c.islower())
    case_ratio = upper_count / max(lower_count, 1)

    sentences = [s.strip() for s in re.split(r"[.!?\n]+", raw_text) if s.strip()]
    cap_rate = sum(1 for s in sentences if s[0].isupper()) / max(len(sentences), 1)

    drop_ratio = compute_contraction_drop_ratio(raw_text)

    return {
        "yules_k": round(yules_k, 2),
        "shannon_entropy": round(shannon_entropy, 3),
        "mean_clause_len": round(mean_len, 2),
        "std_clause_len": round(std_len, 2),
        "skew_clause_len": round(skew_len, 3),
        "punct_ratio": round(punct_ratio, 4),
        "case_ratio": round(case_ratio, 4),
        "drop_ratio": round(drop_ratio, 2),
        "cap_rate": round(cap_rate, 2)
    }


# =========================================================================
# LAYER 2: Regularized Burrows' Delta on Top-N Function Words
# =========================================================================

def compute_burrows_delta(
    authors_tokens: Dict[str, List[str]],
    confession_tokens: List[str],
    top_n: int = 100,
    lambd: float = 1.0
) -> Dict[str, float]:
    """Regularized Burrows' Delta with Empirical Bayes shrinkage."""
    corpus_all_tokens = [tok.lower() for tokens in authors_tokens.values() for tok in tokens]
    token_freqs = Counter(corpus_all_tokens)

    selected_function_words = [w for w in FUNCTION_WORDS if token_freqs.get(w, 0) > 0]
    selected_function_words.sort(key=lambda w: token_freqs.get(w, 0), reverse=True)
    selected_function_words = selected_function_words[:top_n]

    if not selected_function_words:
        return {aid: 0.5 for aid in authors_tokens}

    n_words = len(selected_function_words)
    author_ids = list(authors_tokens.keys())
    freq_matrix = np.zeros((n_words, len(author_ids)), dtype=np.float64)

    for col_idx, aid in enumerate(author_ids):
        toks = authors_tokens[aid]
        N_j = max(len(toks), 1)
        author_counter = Counter(t.lower() for t in toks)
        for row_idx, fw in enumerate(selected_function_words):
            freq_matrix[row_idx, col_idx] = author_counter[fw] / N_j

    mu = np.mean(freq_matrix, axis=1, keepdims=True)
    sigma = np.std(freq_matrix, axis=1, keepdims=True)
    sigma[sigma < 1e-9] = 1e-4

    Z_authors = (freq_matrix - mu) / sigma

    N_T = max(len(confession_tokens), 1)
    conf_counter = Counter(t.lower() for t in confession_tokens)
    conf_freqs = np.array([[conf_counter[fw] / N_T] for fw in selected_function_words], dtype=np.float64)
    Z_T = (conf_freqs - mu) / sigma

    delta_distances = np.mean(np.abs(Z_authors - Z_T), axis=0)
    mean_delta = float(np.mean(delta_distances))

    delta_scores = {}
    for col_idx, aid in enumerate(author_ids):
        d_val = float(delta_distances[col_idx])
        tok_len = len(authors_tokens[aid])
        alpha = min(1.0, tok_len / 45.0)
        d_reg = alpha * d_val + (1.0 - alpha) * mean_delta
        s_val = float(np.exp(-lambd * d_reg))
        delta_scores[aid] = round(s_val, 4)

    return delta_scores


# =========================================================================
# LAYER 3: Sub-Word Character N-Grams & Author-Frequency Zipfian Surprisal
# =========================================================================

def compute_ngram_tfidf_similarity(
    authors_texts: Dict[str, str],
    confession_text: str
) -> Dict[str, float]:
    """Sub-Word Character N-Gram (3-5 grams) TF-IDF vectors with sublinear scaling."""
    author_ids = list(authors_texts.keys())
    documents = [authors_texts[aid] for aid in author_ids] + [confession_text]

    try:
        vec = TfidfVectorizer(
            analyzer="char",
            ngram_range=(3, 5),
            sublinear_tf=True,
            min_df=1,
            max_features=12000
        )
        tfidf_matrix = vec.fit_transform(documents)

        conf_vec = tfidf_matrix[-1]
        author_vecs = tfidf_matrix[:-1]

        cos_sims = cosine_similarity(author_vecs, conf_vec).flatten()
        return {aid: round(float(cos_sims[i]), 4) for i, aid in enumerate(author_ids)}
    except Exception as e:
        print(f"[!] TFIDF error: {e}")
        return {aid: 0.0 for aid in author_ids}


def compute_dynamic_zipfian_surprisal(
    authors_tokens: Dict[str, List[str]],
    authors_texts: Dict[str, str],
    confession_tokens: List[str],
    confession_text: str
) -> Tuple[Dict[str, float], Dict[str, Dict[str, float]], Dict[str, bool]]:
    """
    Computes Information-Theoretic Self-Information with Author-Frequency Scaling:
    - Filters out general English conversational vocabulary from inflating scores.
    - Evaluates slang, contractions, and compound emojis.
    - Matches micro-typos via Levenshtein distance <= 1 (e.g. 'scsred' <-> 'scared', 'drool' <-> 'drools').
    - Evaluates author prevalence (rare across authors = massive forensic fingerprint).
    - Normalizes by author log-token volume (Surprisal Density) to eliminate document-length chatter bias.
    """
    author_ids = list(authors_tokens.keys())

    conf_words = [
        w for w in re.findall(r"\b[a-zA-Z]+\b", confession_text.lower())
        if (len(w) > 1 and w not in COMMON_VOCAB) or w in KNOWN_SLANG
    ]
    conf_emojis = EMOJI_PATTERN.findall(confession_text)
    has_shout_curse_conf = bool(re.search(r"\b[A-Z]{3,}\b", confession_text))

    # Precompute lowercase texts and word sets per author
    author_words_map = {}
    for aid in author_ids:
        text = authors_texts[aid].lower()
        author_words_map[aid] = set(re.findall(r"\b[a-zA-Z]+\b", text))

    raw_surprisal_densities = {}
    shared_rare_map = {}
    anomaly_map = {}

    for aid in author_ids:
        a_text = authors_texts[aid]
        a_toks = authors_tokens[aid]
        total_a_tokens = len(a_toks)
        a_words_set = author_words_map[aid]

        matched_hits = {}

        # 1. Slang & Distinctive Non-Stopword Matches
        for w in conf_words:
            if w in a_words_set:
                # Count author frequency (how many authors use this word)
                author_freq = sum(1 for words in author_words_map.values() if w in words)
                surprisal = 25.0 / (author_freq + 0.5)
                matched_hits[w] = round(surprisal, 1)
            else:
                # Levenshtein Typo Fingerprinting (distance == 1 for words of len >= 5)
                if len(w) >= 5:
                    for aw in a_words_set:
                        if len(aw) >= 5 and abs(len(aw) - len(w)) <= 1:
                            if levenshtein_dist(w, aw) == 1:
                                author_freq = sum(1 for words in author_words_map.values() if aw in words)
                                surprisal = 30.0 / (author_freq + 0.5)
                                matched_hits[f"{aw} (typo for {w})"] = round(surprisal, 1)
                                break

        # 2. Compound Emojis & Individual Rare Emoji Hits
        for em in conf_emojis:
            em_clean = re.sub(r"\s+", "", em)
            if em_clean in re.sub(r"\s+", "", a_text):
                matched_hits[em_clean] = 22.0
            else:
                for char in em:
                    if char in a_text and char in ["✌", "✌️", "🫩", "🤡", "🙏", "😭"]:
                        matched_hits[f"partial:{char}"] = 8.0

        # 3. Capitalized Shout Profanity / Closed Compound Acronyms
        if has_shout_curse_conf and re.search(r"\b[A-Z]{3,}\b", a_text):
            matched_hits["ALL_CAPS_EXP"] = 8.0

        # Calculate Surprisal Density
        surprisal_sum = sum(matched_hits.values())
        surprisal_density = surprisal_sum / math.log(total_a_tokens + 15) if total_a_tokens > 0 else 0.0

        # Jitter / Mimicry anomaly check
        is_anomaly = False
        if len(matched_hits) == 1 and total_a_tokens > 400:
            is_anomaly = True
            surprisal_density *= 0.65

        raw_surprisal_densities[aid] = surprisal_density
        shared_rare_map[aid] = matched_hits
        anomaly_map[aid] = is_anomaly

    # Normalize to [0, 1]
    max_d = max(raw_surprisal_densities.values()) if raw_surprisal_densities else 1.0
    norm_surprisals = {
        aid: round(raw_surprisal_densities[aid] / max_d, 4) if max_d > 0 else 0.0
        for aid in author_ids
    }

    return norm_surprisals, shared_rare_map, anomaly_map


# =========================================================================
# LAYER 4: Deep Semantic Vector Embeddings (Sentence Transformers)
# =========================================================================

EMBEDDINGS_CACHE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "author_embeddings_cache.npz")


def load_cached_embeddings():
    """Loads author vector embeddings from disk cache if present."""
    global _AUTHOR_EMBEDDINGS_CACHE
    if not _AUTHOR_EMBEDDINGS_CACHE and os.path.exists(EMBEDDINGS_CACHE_FILE):
        try:
            data = np.load(EMBEDDINGS_CACHE_FILE)
            for k in data.files:
                _AUTHOR_EMBEDDINGS_CACHE[k] = data[k]
        except Exception as e:
            print(f"[!] Error reading embeddings cache: {e}")


def save_cached_embeddings():
    """Persists author vector embeddings to disk for instant subsequent runs."""
    global _AUTHOR_EMBEDDINGS_CACHE
    if _AUTHOR_EMBEDDINGS_CACHE:
        try:
            np.savez_compressed(EMBEDDINGS_CACHE_FILE, **_AUTHOR_EMBEDDINGS_CACHE)
        except Exception as e:
            print(f"[!] Error writing embeddings cache: {e}")


def compute_semantic_embeddings_similarity(
    authors_texts: Dict[str, str],
    confession_text: str
) -> Dict[str, float]:
    """Computes angular cosine semantic similarity using local SentenceTransformer with disk caching."""
    global _AUTHOR_EMBEDDINGS_CACHE
    load_cached_embeddings()
    model = get_embedding_model()
    author_ids = list(authors_texts.keys())

    if not model:
        return {aid: 0.5 for aid in author_ids}

    try:
        v_T = model.encode([confession_text], convert_to_numpy=True)[0]
        norm_vT = np.linalg.norm(v_T)

        missing_aids = [aid for aid in author_ids if aid not in _AUTHOR_EMBEDDINGS_CACHE]
        if missing_aids:
            batch_texts = [authors_texts[aid][:1000] for aid in missing_aids]
            new_embs = model.encode(batch_texts, convert_to_numpy=True, batch_size=32)
            for i, aid in enumerate(missing_aids):
                _AUTHOR_EMBEDDINGS_CACHE[aid] = new_embs[i]
            save_cached_embeddings()

        v_A = np.array([_AUTHOR_EMBEDDINGS_CACHE[aid] for aid in author_ids])
        norms_A = np.linalg.norm(v_A, axis=1)
        norms_A[norms_A < 1e-9] = 1.0

        cos_sims = np.dot(v_A, v_T) / (norms_A * norm_vT)
        rescaled = (cos_sims + 1.0) / 2.0

        return {aid: round(float(rescaled[i]), 4) for i, aid in enumerate(author_ids)}
    except Exception as e:
        print(f"[!] Semantic embedding exception: {e}")
        return {aid: 0.5 for aid in author_ids}


# =========================================================================
# LAYER 5: Master Scoring & Bayesian Posterior Formulation
# =========================================================================

def run_ensemble_attribution(
    corpus: Dict[str, Any],
    confession_text: str,
    temperature: float = 1.8,
    progress_callback: Optional[Any] = None
) -> Dict[str, Any]:
    """
    Master Forensic Scoring Formulation:
    Combines Burrows' Delta, Character N-Grams, Density-Normalized Zipfian Surprisal,
    Capitalization Cadence, Contraction Drop Ratios, and Process-of-Elimination Penalties.
    """
    if progress_callback:
        progress_callback("tokenizing", "Tokenizing messages across authors...", 55)

    authors_data = corpus.get("authors", {})

    authors_texts: Dict[str, str] = {}
    authors_tokens: Dict[str, List[str]] = {}
    authors_msg_counts: Dict[str, int] = {}
    authors_meta: Dict[str, Dict[str, Any]] = {}

    for aid, a in authors_data.items():
        messages = [m.get("content", "") for m in a.get("messages", []) if m.get("content")]
        text = " \n ".join(messages)
        authors_texts[aid] = text
        authors_tokens[aid] = tokenize_forensic(text)
        authors_msg_counts[aid] = len(messages)
        authors_meta[aid] = {
            "author_id": aid,
            "username": a.get("username", "unknown"),
            "display_name": a.get("display_name", "Unknown")
        }

    confession_tokens = tokenize_forensic(confession_text)

    # 1. Descriptive stylometrics of confession
    conf_descriptive = compute_descriptive_stylometrics(confession_tokens, confession_text)
    conf_drop_ratio = conf_descriptive["drop_ratio"]
    conf_cap_rate = conf_descriptive["cap_rate"]

    # 2. Layer 2: Regularized Burrows' Delta on Top Function Words
    if progress_callback:
        progress_callback("stylometrics", "Computing Burrows' Delta & character n-grams...", 70)

    delta_scores = compute_burrows_delta(authors_tokens, confession_tokens, top_n=100)

    # 3. Layer 3A: Sub-word character n-gram cosine similarity (3-5 grams)
    ngram_scores = compute_ngram_tfidf_similarity(authors_texts, confession_text)

    # 4. Layer 3B: Density-Scaled Zipfian Surprisal & Typo Fingerprinting
    surprisal_norm, shared_rare_map, anomaly_map = compute_dynamic_zipfian_surprisal(
        authors_tokens,
        authors_texts,
        confession_tokens,
        confession_text
    )

    # 5. Layer 4: Deep Semantic Vector Embeddings
    if progress_callback:
        progress_callback("embedding", "Retrieving neural semantic vector embeddings...", 85)

    embed_scores = compute_semantic_embeddings_similarity(authors_texts, confession_text)

    if progress_callback:
        progress_callback("attributing", "Calibrating Bayesian posteriors & biometrics...", 95)

    # 6. Orthographic Structural Biometrics & Process of Elimination
    has_pipe_conf = "|" in confession_text
    has_tilde_conf = "~" in confession_text

    author_ids = list(authors_texts.keys())
    master_scores = {}
    negative_penalties = {}
    biometric_scores = {}

    for aid in author_ids:
        text = authors_texts[aid]
        msg_count = authors_msg_counts.get(aid, 1)

        # Baseline Stylometric Signal C(A)
        s_delta = delta_scores.get(aid, 0.0)
        s_ngram = ngram_scores.get(aid, 0.0)
        s_embed = embed_scores.get(aid, 0.0)
        c_base = (0.35 * s_delta) + (0.35 * s_ngram) + (0.30 * s_embed)

        # Contraction Apostrophe Drop Rate Biometric Matching
        a_drop_ratio = compute_contraction_drop_ratio(text)
        sim_drop = 1.0 - abs(a_drop_ratio - conf_drop_ratio)

        # Sentence-start Capitalization Rate Biometric Matching
        author_sentences = [s.strip() for s in re.split(r"[.!?\n]+", text) if s.strip()]
        a_cap_rate = sum(1 for s in author_sentences if s[0].isupper()) / max(len(author_sentences), 1)
        sim_case = 1.0 - abs(a_cap_rate - conf_cap_rate)

        biometric_scores[aid] = {
            "drop_ratio": round(a_drop_ratio, 2),
            "sim_drop": round(sim_drop, 2),
            "cap_rate": round(a_cap_rate, 2),
            "sim_case": round(sim_case, 2)
        }

        # Multi-Marker Synergy Multiplier
        k_hits = len(shared_rare_map.get(aid, {}))
        synergy = 1.0 + 0.35 * max(0, k_hits - 1) if k_hits > 0 else 0.40

        # Sample Volume Credibility Factor
        credibility = 1.0 - math.exp(-(msg_count + 1) / 8.0)

        # Negative Constraint Hard-Penalties (Process of Elimination)
        penalty = 1.0
        violations = []

        if msg_count > 40:
            # Extreme case discordance (e.g., all-lowercase chatter vs 100% capitalized confession)
            if conf_cap_rate > 0.8 and a_cap_rate < 0.2:
                penalty *= 0.50
                violations.append("All-lowercase typing habit on fully capitalized confession (>40 msgs)")
            elif conf_cap_rate < 0.2 and a_cap_rate > 0.8:
                penalty *= 0.50
                violations.append("Strict sentence capitalization habit on all-lowercase confession (>40 msgs)")

            # Pipe delimiter habit violation
            if has_pipe_conf and "|" not in text:
                penalty *= 0.60
                violations.append("Zero pipe delimiter usage across >40 msgs")

            # Tilde cadence violation
            if has_tilde_conf and "~" not in text:
                penalty *= 0.75
                violations.append("Zero tilde usage across >40 msgs")

        negative_penalties[aid] = {
            "penalty_multiplier": round(penalty, 2),
            "violations": violations
        }

        # Density-Normalized Surprisal term
        s_surprisal = surprisal_norm.get(aid, 0.0)

        # Master Formula:
        # Core Signal integrates Stylometric Baseline with Idiolect Surprisal Density and Casing Biometrics
        core_signal = (c_base * (0.50 + 0.50 * credibility)) + (2.5 * s_surprisal) + (0.50 * sim_case) + (0.20 * sim_drop)
        final_score = (core_signal * synergy) * penalty
        master_scores[aid] = max(0.01, final_score)

    # Calibrated Softmax Posterior Probabilities
    s_arr = np.array([master_scores[aid] for aid in author_ids], dtype=np.float64)
    mean_s = np.mean(s_arr)
    std_s = np.std(s_arr) if np.std(s_arr) > 1e-6 else 1.0
    z_scores = (s_arr - mean_s) / std_s

    exp_s = np.exp(z_scores / max(temperature, 0.1))
    posterior_probs = exp_s / np.sum(exp_s)

    results = []
    for idx, aid in enumerate(author_ids):
        prob_pct = round(float(posterior_probs[idx]) * 100.0, 1)
        author_stat = compute_descriptive_stylometrics(authors_tokens[aid], authors_texts[aid])

        # Evidence quotes
        evidence_snippets = []
        author_msgs = [m.get("content", "") for m in authors_data[aid].get("messages", []) if m.get("content")]
        for m in author_msgs:
            m_lower = m.lower()
            if any(t in m_lower or t in m for t in [
                "😭 ✌", "😭✌", "lowkey", "drool", "icl", "atp", "shi", "~~", "🫩",
                "ts", "gotta", "pick me", "scsred", "scared", "wtf", "bro", "lmao", "asfuck", "asf"
            ]):
                evidence_snippets.append(m)
                if len(evidence_snippets) >= 6:
                    break

        rare_dict = shared_rare_map.get(aid, {})
        slang_matches = {k: v for k, v in rare_dict.items() if not EMOJI_PATTERN.search(k)}
        emoji_matches = {k: v for k, v in rare_dict.items() if EMOJI_PATTERN.search(k)}

        results.append({
            "author_id": aid,
            "username": authors_meta[aid]["username"],
            "display_name": authors_meta[aid]["display_name"],
            "message_count": authors_msg_counts[aid],
            "posterior_probability_pct": prob_pct,
            "composite_score": round(float(master_scores[aid]), 4),
            "layer_breakdown": {
                "burrows_delta_proximity": delta_scores.get(aid, 0.0),
                "ngram_tfidf_cosine": ngram_scores.get(aid, 0.0),
                "zipfian_surprisal": surprisal_norm.get(aid, 0.0),
                "semantic_embedding_cosine": embed_scores.get(aid, 0.0)
            },
            "biometrics": biometric_scores.get(aid, {}),
            "negative_penalties": negative_penalties.get(aid, {}),
            "is_anomaly": anomaly_map.get(aid, False),
            "breakdown": {
                "slang_matches": slang_matches,
                "emoji_matches": emoji_matches
            },
            "descriptive_stylometrics": author_stat,
            "evidence": evidence_snippets
        })

    results.sort(key=lambda x: x["posterior_probability_pct"], reverse=True)

    return {
        "confession_stylometrics": conf_descriptive,
        "total_authors_analyzed": len(results),
        "total_messages_analyzed": sum(authors_msg_counts.values()),
        "top_rankings": results[:5],
        "all_rankings": results
    }
