"""
Gemini Forensic Analyst & Interrogation Module
----------------------------------------------
Provides deep qualitative forensic profiling, psychological motive analysis,
adversarial frame-job detection, interactive interrogation chat, and
individual member behavioral profiling with 3-line savage roasts.
"""

import json
import os
import re
import time
import requests
from typing import Dict, Any, List, Optional

# Reliable model fallback chain
MODEL_CHAIN = ["gemini-3.5-flash", "gemini-3.6-flash", "gemini-3.5-flash-lite"]

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, "config.json")
CACHE_FILE = os.path.join(BASE_DIR, "discord_messages.json")


def get_gemini_key() -> Optional[str]:
    """Retrieve Gemini API key from environment or config.json."""
    if os.getenv("GEMINI_API_KEY"):
        return os.getenv("GEMINI_API_KEY")
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("gemini_api_key")
        except Exception:
            pass
    return None


def call_gemini_api(contents: List[Dict[str, Any]], system_instruction: Optional[str] = None, api_key: Optional[str] = None) -> str:
    """Invokes Gemini endpoint with automatic model fallback and retry resilience."""
    key = api_key or get_gemini_key()
    if not key:
        raise ValueError("GEMINI_KEY_MISSING: No Gemini API key configured.")

    payload: Dict[str, Any] = {
        "contents": contents,
        "generationConfig": {
            "temperature": 0.4,
            "maxOutputTokens": 8192,
        }
    }

    if system_instruction:
        payload["system_instruction"] = {
            "parts": [{"text": system_instruction}]
        }

    last_error = None
    for model_name in MODEL_CHAIN:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={key}"
        for attempt in range(2):
            try:
                resp = requests.post(url, json=payload, timeout=45)
                if resp.status_code == 200:
                    result = resp.json()
                    candidates = result.get("candidates", [])
                    if candidates:
                        candidate = candidates[0]
                        finish_reason = candidate.get("finishReason", "")
                        parts = candidate.get("content", {}).get("parts", [])
                        text_parts = [p.get("text", "") for p in parts if isinstance(p, dict) and "text" in p]
                        full_text = "".join(text_parts).strip()
                        if full_text:
                            if finish_reason and finish_reason not in ["STOP", ""]:
                                print(f"[*] Gemini finishReason: {finish_reason}")
                            return full_text
                elif resp.status_code in [429, 503]:
                    time.sleep(1.0)
                    continue
                else:
                    err_msg = resp.text
                    try:
                        err_msg = resp.json().get("error", {}).get("message", resp.text)
                    except Exception:
                        pass
                    last_error = f"HTTP {resp.status_code}: {err_msg}"
            except Exception as e:
                last_error = str(e)
                time.sleep(0.5)

    raise RuntimeError(f"Gemini API invocation failed across models: {last_error}")


def get_active_corpus_data() -> Optional[Dict[str, Any]]:
    """Loads the active server corpus with highest message count."""
    candidates = [
        os.path.join(BASE_DIR, "cache_1516697578107043850.json"),
        CACHE_FILE
    ]
    best_data = None
    best_count = 0
    for path in candidates:
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    d = json.load(f)
                    cnt = d.get("metadata", {}).get("human_messages_kept", 0)
                    if cnt >= best_count:
                        best_count = cnt
                        best_data = d
            except Exception:
                pass
    return best_data


def load_corpus_summary() -> str:
    """Loads a comprehensive summary of the server message archive for Gemini's context."""
    data = get_active_corpus_data()
    if data:
        try:
            authors = data.get("authors", {})
            total_msgs = data.get("metadata", {}).get("human_messages_kept", len(authors))
            oldest_ts = data.get("metadata", {}).get("oldest_timestamp", "")[:16].replace("T", " ")
            newest_ts = data.get("metadata", {}).get("newest_timestamp", "")[:16].replace("T", " ")
            
            top_authors = sorted(authors.items(), key=lambda x: len(x[1].get("messages", [])), reverse=True)[:25]
            author_summaries = []
            for uid, a in top_authors:
                name = a.get("display_name") or a.get("username") or uid
                user = a.get("username") or uid
                count = len(a.get("messages", []))
                sample = [m.get("content", "") for m in a.get("messages", []) if m.get("content")][:2]
                author_summaries.append(f"- {name} (@{user}): {count:,} msgs. (Sample: {sample})")
            
            return (
                f"SERVER CORPUS OVERVIEW (FULL ARCHIVE ACCESS):\n"
                f"- Total messages in database: {total_msgs:,}\n"
                f"- Total unique human authors: {len(authors):,}\n"
                f"- Archive Time Span: {oldest_ts} UTC to {newest_ts} UTC\n"
                f"- Top 25 Most Active Members:\n" + "\n".join(author_summaries)
            )
        except Exception as e:
            print(f"[!] Error building corpus summary: {e}")
            pass
    return "SERVER CORPUS: Over 113,800 messages and 790+ members indexed."


def search_corpus_for_chat(query: str, max_results: int = 15) -> str:
    """Dynamically retrieves relevant quotes from the 113,800+ message database to ground Gemini's answers."""
    data = get_active_corpus_data()
    if not data or "authors" not in data:
        return ""

    authors = data["authors"]
    q = query.lower().strip()
    evidence_lines = []

    # 1. Target author matching (support finding up to 3 mentioned members)
    matched_uids = set()
    for uid, a in authors.items():
        if uid in matched_uids:
            continue
        u_name = a.get("username", "").lower()
        d_name = (a.get("display_name") or "").lower()
        if (f"@{u_name}" in q or (len(u_name) >= 3 and u_name in q) or (len(d_name) >= 3 and d_name in q)):
            matched_uids.add(uid)
            msgs = [m for m in a.get("messages", []) if m.get("content")]
            msg_texts = [m.get("content", "") for m in msgs]
            sample = msg_texts[-25:]  # Recent 25 quotes
            disp = a.get("display_name") or a.get("username") or uid
            evidence_lines.append(
                f"\n=== VERIFIED ARCHIVE RECORD FOR {disp} (@{a.get('username')}) ===\n"
                f"- User ID: {uid}\n"
                f"- Total Messages Archived in Database: {len(msgs):,} messages\n"
                f"- Representative Recent Quotes ({len(sample)} sample quotes):\n" +
                "\n".join(f'  * "{s}"' for s in sample)
            )
            if len(matched_uids) >= 3:
                break

    # 2. Topic/Keyword matching across the corpus if no authors were isolated
    tokens = [w for w in re.findall(r"\b\w{4,}\b", q) if w not in {"what", "tell", "about", "show", "from", "with", "this", "that", "have", "been", "some", "like", "who", "when", "where", "does", "many", "messages"}]
    if tokens and len(evidence_lines) == 0:
        found_quotes = []
        for uid, a in authors.items():
            u_name = a.get("username", "")
            d_name = a.get("display_name", "")
            for m in a.get("messages", []):
                c = m.get("content", "")
                if any(t in c.lower() for t in tokens[:2]):
                    found_quotes.append(f"[{d_name} / @{u_name}]: \"{c}\"")
                    if len(found_quotes) >= max_results:
                        break
            if len(found_quotes) >= max_results:
                break
        if found_quotes:
            evidence_lines.append(f"\n--- RELEVANT ARCHIVE QUOTES MATCHING KEYWORDS ({', '.join(tokens[:2])}) ---")
            evidence_lines.extend(found_quotes)

    return "\n".join(evidence_lines)


def build_forensic_context(confession: str, prediction_data: Dict[str, Any]) -> str:
    """Serializes mathematical metrics and evidence quotes for Gemini's context."""
    top_rankings = prediction_data.get("top_rankings", [])[:4]
    
    if not top_rankings:
        summary_lines = [
            load_corpus_summary(),
            "",
            "CURRENT STATUS: Standing by in interrogation mode.",
        ]
        if confession:
            summary_lines.append(f'INVESTIGATION CONFESSION ENTERED:\n"""\n{confession}\n"""')
        return "\n".join(summary_lines)

    time_window = prediction_data.get("time_window", {})
    total_msgs = prediction_data.get("total_messages_analyzed", 0)
    total_authors = prediction_data.get("total_authors_analyzed", 0)

    summary_lines = [
        "INVESTIGATION DATASET OVERVIEW:",
        f"- Total Messages in Corpus: {total_msgs}",
        f"- Total Candidate Authors Analyzed: {total_authors}",
        f"- Time Window Scraped: {time_window.get('display', 'Recent active window')}",
        "",
        "CONFESSION UNDER INVESTIGATION:",
        f'"""\n{confession}\n"""',
        "",
        "MATHEMATICAL FORENSIC RANKINGS (5-Layer Ensemble):"
    ]

    for idx, cand in enumerate(top_rankings, 1):
        name = cand.get("display_name", "Unknown")
        user = cand.get("username", "unknown")
        prob = cand.get("posterior_probability_pct", 0)
        msgs = cand.get("message_count", 0)
        lb = cand.get("layer_breakdown", {})
        ds = cand.get("descriptive_stylometrics", {})
        bio = cand.get("biometrics", {})

        summary_lines.append(f"\n--- CANDIDATE #{idx}: {name} (@{user}) ---")
        summary_lines.append(f"- Bayesian Posterior Probability: {prob}% (Messages Analyzed: {msgs})")
        summary_lines.append(f"- Burrows' Delta Proximity: {lb.get('burrows_delta_proximity')} (lower is closer)")
        summary_lines.append(f"- Character 3-5 Gram Cosine: {lb.get('ngram_tfidf_cosine')} (higher is closer)")
        summary_lines.append(f"- Zipfian Surprisal Density: {lb.get('zipfian_surprisal')}")
        summary_lines.append(f"- Semantic Embedding Cosine: {lb.get('semantic_embedding_cosine')}")
        summary_lines.append(f"- Contraction Drop Ratio R_drop: {bio.get('drop_ratio', ds.get('drop_ratio'))}")
        summary_lines.append(f"- Punctuation Density: {ds.get('punct_ratio')}")
        summary_lines.append(f"- Mean Clause Length: {ds.get('mean_clause_len')}")
        
        evidence = cand.get("evidence", [])[:4]
        if evidence:
            summary_lines.append(f"- Verified Discord Quotes from @{user}:")
            for ev in evidence:
                quote_text = ev if isinstance(ev, str) else ev.get("message", "")
                summary_lines.append(f'  * "{quote_text}"')

    return "\n".join(summary_lines)


def generate_forensic_dossier(confession: str, prediction_data: Dict[str, Any], api_key: Optional[str] = None) -> Dict[str, Any]:
    """Generates an exhaustive, structured forensic investigation dossier."""
    context_text = build_forensic_context(confession, prediction_data)

    system_instruction = (
        "You are an elite Digital Forensic Linguist, Intelligence Behavioral Profiler, and Cyber-Psychologist. "
        "Your task is to analyze anonymous confessions from online gaming/social Discord servers by uniting "
        "rigorous mathematical stylometrics (Burrows' Delta, Zipfian surprisal, character n-grams) with "
        "human behavioral psychology, socio-cultural context, and adversarial detection.\n\n"
        "Tone: Authoritative, forensic, intellectually rigorous, insightful, objective, yet engaging.\n"
        "Never use generic boilerplate. Cite exact linguistic markers, slang tokens, casing cadence, and psychological defense mechanisms."
    )

    prompt = f"""Conduct an exhaustive Forensic Intelligence Dossier on the following anonymous confession and stylometric findings:

{context_text}

Analyze and format your response with the following clear markdown sections:

### 1. 🔍 Executive Forensic Assessment & Verdict
- State the prime attribution suspect, confidence level (High/Moderate/Low), and the primary rationale combining mathematical evidence with psychological coherence.

### 2. 🧠 Motive & Psychological Profiling
- **Primary Driver:** Why did the author write this? (e.g., status grievance, romantic jealousy, server hierarchy frustration, social policing).
- **Subconscious Psychological Tells:** What emotional leakage or insecurities are evident beneath the casual slang?
- **Deconstruction of Potential 'Proxy Shields':** Analyze any claims of writing on behalf of friends, self-proclaimed gender/identity claims, or deliberate deflections. Is this authentic, or a psychological buffer to avoid accountability?

### 3. 🌐 Social Graph & Server Context Analysis
- Decode the interpersonal dynamic: Who is targeted and why? What do the observations reveal about the author's real-time monitoring of server text channels and voice chats?
- How frequently does this author monitor server social interactions?

### 4. 🎭 Adversarial Frame-Job & Mimicry Risk Analysis
- **Frame-Job Probability Rating:** Estimate the mathematical and behavioral likelihood (e.g. 5% vs 85%) that an adversary is deliberately framing the top suspect.
- **Organic Reflex vs. Planted Markers:** Differentiate between subconscious habitual reflexes (e.g., trailing tildes, specific contraction drop rates, lowercase capitalization habits) versus easily copy-pasted catchphrases. Does this read like an authentic writing sample or an engineered smear?

### 5. ⚖️ Suspect Comparison Matrix
- Provide a sharp, direct comparison explaining why Candidate #1 is a much stronger match than Candidate #2 or Candidate #3, referencing both mathematical closeness and behavioral fit.

### 6. 🎯 Actionable Interrogation Traps
- Give the investigator 2-3 precise conversational questions or bait topics to mention in the Discord server or in private messages to elicit a conclusive linguistic confession or guilty reaction.
"""

    contents = [{"parts": [{"text": prompt}]}]
    dossier_text = call_gemini_api(contents, system_instruction=system_instruction, api_key=api_key)

    return {
        "success": True,
        "dossier_markdown": dossier_text,
        "model": "gemini-3.5-flash"
    }


def chat_interrogate(
    user_message: str,
    conversation_history: List[Dict[str, str]],
    confession: str,
    prediction_data: Dict[str, Any],
    api_key: Optional[str] = None
) -> str:
    """Interactive conversational agent with full live access to the 113,800+ message corpus."""
    context_text = build_forensic_context(confession, prediction_data)
    dynamic_search = search_corpus_for_chat(user_message)

    system_instruction = (
        "You are 'Antigravity Forensic AI' — an interactive Discord Confession Investigator and Forensic Linguist bot. "
        "The user is talking with you directly in a real-time investigation room. "
        "You have direct, live access to the unified Discord server database (over 132,400 messages, 840+ members), member typing habits, and recent confessions.\n\n"
        "Guidelines:\n"
        "- Talk naturally, smartly, and forensically with the user as their expert forensic partner.\n"
        "- Answer any question about server members, confessions, typing habits, slang patterns, frame-job hypotheses, or mathematical metrics.\n"
        "- Ground your insights in real data and verified database facts.\n"
        "- When asked about a member's message count or stats, state the exact numbers clearly from the archive record.\n"
        "- Always complete your full response and sentences cleanly without cutting off abruptly.\n"
        "- Keep answers engaging, sharp, clear, and formatted with markdown."
    )

    contents: List[Dict[str, Any]] = []

    first_context = f"SERVER ARCHIVE & EVIDENCE FILE:\n{context_text}\n"
    if dynamic_search:
        first_context += f"\nEVIDENCE RETRIEVED FROM SERVER ARCHIVE FOR USER QUERY:\n{dynamic_search}\n"
    first_context += "\nThe user is now talking directly with you in the interrogation room."

    contents.append({"role": "user", "parts": [{"text": first_context}]})
    contents.append({"role": "model", "parts": [{"text": "Hello! I am your Forensic AI Investigator with full access to the live 132,400+ message server database. What would you like to investigate or discuss?"}]})

    for msg in conversation_history[-10:]:
        role = "user" if msg.get("role") in ["user", "human"] else "model"
        text = msg.get("text") or msg.get("content", "")
        if text:
            contents.append({"role": role, "parts": [{"text": text}]})

    contents.append({"role": "user", "parts": [{"text": user_message}]})

    reply = call_gemini_api(contents, system_instruction=system_instruction, api_key=api_key)
    return reply


def analyze_member_behavior(
    author_name: str,
    author_username: str,
    messages: List[str],
    api_key: Optional[str] = None
) -> Dict[str, Any]:
    """Generates an in-depth behavioral/psychological profile and an exact 3-line brutal roast."""
    total_provided = len(messages)

    # Intelligently format messages so Gemini sees full scope (early, middle, recent)
    if total_provided <= 400:
        sample_msgs = messages
    elif total_provided <= 1200:
        sample_msgs = messages[:150] + messages[len(messages)//2 - 100 : len(messages)//2 + 100] + messages[-250:]
    else:
        # Uniform sampling across their entire history + latest 150
        step = max(1, total_provided // 700)
        sample_msgs = messages[::step][:700]
        sample_msgs.extend(messages[-150:])

    sample_text = "\n".join(f"- {m}" for m in sample_msgs if m and m.strip())

    system_instruction = (
        "You are an elite Discord server behavioral psychologist and savage roast comedian. "
        "Your task is to analyze a Discord member's real messages across their chat history to create a sharp, hilarious, "
        "insightful behavioral profile followed by an EXACT 3-line roast tailored directly to their messages and evolution."
    )

    prompt = f"""Analyze the real Discord chat history of user '{author_name}' (@{author_username}) based on {total_provided} analyzed messages.

MESSAGES ARCHIVE SAMPLE ({len(sample_msgs)} representative messages across their history):
{sample_text}

Provide your analysis in the following format:

### Part 1: 🧠 Behavioral & Psychological Profile
- **Personality Archetype:** A funny yet insightful archetype title (e.g. 'The VC Ghost', 'The Chronic Overreactor', 'The Edgelord Philosopher').
- **Chat Vibe & Emotional Cadence:** How they communicate (e.g. all-caps screams, passive-aggressive replies, self-pity, meme flooding, speed-typing).
- **Core Obsessions & Topic Leaks:** The recurring topics, gripes, or server drama they fixate on.
- **Linguistic Quirks:** Repeated slang, idiosyncratic grammar, emoji crutches, or verbal tics.

### Part 2: 🔥 3-Line Brutal Roast
Provide EXACTLY 3 lines of a devastatingly accurate, hilarious roast targeting their specific Discord messaging habits, excuses, or personality shown in these messages.
Make each line punchy, witty, and tailored directly to their messages. Format each line starting with a bullet point:
- Line 1
- Line 2
- Line 3
"""

    contents = [{"parts": [{"text": prompt}]}]
    full_output = call_gemini_api(contents, system_instruction=system_instruction, api_key=api_key)

    # Extract the 3 roast lines
    roast_lines = []
    part2_match = re.search(r"### Part 2:.*?\n([\s\S]+)$", full_output, re.IGNORECASE)
    if part2_match:
        part2_text = part2_match.group(1).strip()
        lines = [line.strip() for line in part2_text.split("\n") if line.strip().startswith("- ") or line.strip().startswith("* ")]
        for l in lines[:3]:
            cleaned = re.sub(r"^[-*]\s*", "", l).strip()
            if cleaned:
                roast_lines.append(cleaned)

    # Fallback if parsing failed to extract exactly 3 bullets
    if len(roast_lines) < 3:
        all_bullets = [re.sub(r"^[-*]\s*", "", l).strip() for l in full_output.split("\n") if l.strip().startswith("- ") or l.strip().startswith("* ")]
        if len(all_bullets) >= 3:
            roast_lines = all_bullets[-3:]

    return {
        "success": True,
        "full_markdown": full_output,
        "roast_lines": roast_lines
    }
