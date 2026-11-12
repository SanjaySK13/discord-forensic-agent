"""
Flask Server for Discord Stylometric Confession Predictor & AI Forensics
------------------------------------------------------------------------
Serves the web UI and provides prediction, AI forensic dossier, and interrogation API.
"""

import json
import os
import sys
from datetime import datetime, timezone
from typing import Any, Dict, Optional
import threading
from flask import Flask, jsonify, render_template, request

# Import scraping, mathematical stylometrics, and Gemini AI analyst modules
import scrape_discord
import math_stylometrics as stylometrics
import gemini_analyst

app = Flask(__name__, template_folder="templates", static_folder="static")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, "config.json")
CACHE_FILE = os.path.join(BASE_DIR, "discord_messages.json")


def load_config() -> Dict[str, Any]:
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_config(cfg: Dict[str, Any]) -> None:
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)


def get_cached_corpus(channel_id: str) -> Dict[str, Any]:
    specific_cache = os.path.join(BASE_DIR, f"cache_{channel_id}.json")
    if os.path.exists(specific_cache):
        with open(specific_cache, "r", encoding="utf-8") as f:
            return json.load(f)
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def get_time_window_info(corpus_data: Dict[str, Any]) -> Dict[str, str]:
    """Calculates human-readable start, end, and duration from all message timestamps."""
    if not corpus_data or "authors" not in corpus_data:
        return {"display": "No cached messages", "duration": "0m", "start": "", "end": ""}

    timestamps = []
    for a in corpus_data.get("authors", {}).values():
        for m in a.get("messages", []):
            t = m.get("timestamp")
            if t:
                timestamps.append(t)

    if not timestamps:
        return {"display": "Timestamps unavailable", "duration": "0m", "start": "", "end": ""}

    timestamps.sort()
    try:
        t0 = datetime.fromisoformat(timestamps[0])
        t1 = datetime.fromisoformat(timestamps[-1])
        diff = t1 - t0
        days = diff.days
        hours = diff.seconds // 3600
        mins = (diff.seconds % 3600) // 60
        dur_parts = []
        if days > 0: dur_parts.append(f"{days}d")
        if hours > 0 or days > 0: dur_parts.append(f"{hours}h")
        dur_parts.append(f"{mins}m")
        dur_str = " ".join(dur_parts) if dur_parts else "0m"

        return {
            "start": t0.strftime("%b %d, %H:%M UTC"),
            "end": t1.strftime("%b %d, %H:%M UTC"),
            "duration": dur_str,
            "display": f"{t0.strftime('%b %d, %H:%M')} → {t1.strftime('%b %d, %H:%M UTC')} ({dur_str})"
        }
    except Exception:
        return {"display": f"{timestamps[0][:16]} → {timestamps[-1][:16]}", "duration": "N/A", "start": "", "end": ""}


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/status", methods=["GET"])
def api_status():
    cfg = load_config()
    cache_exists = os.path.exists(CACHE_FILE)
    cached_info = {}
    saved_token = cfg.get("token") or os.getenv("DISCORD_BOT_TOKEN")
    saved_gemini = cfg.get("gemini_api_key") or os.getenv("GEMINI_API_KEY")

    token_preview = None
    if saved_token:
        token_preview = f"{saved_token[:5]}••••••••{saved_token[-4:]}" if len(saved_token) > 10 else "••••••••"

    gemini_preview = None
    if saved_gemini:
        gemini_preview = f"{saved_gemini[:4]}••••••••{saved_gemini[-4:]}" if len(saved_gemini) > 8 else "••••••••"

    if cache_exists:
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                meta = data.get("metadata", {})
                tw_info = get_time_window_info(data)
                cached_info = {
                    "total_messages": meta.get("human_messages_kept", 0),
                    "total_authors": len(data.get("authors", {})),
                    "generated_at": meta.get("generated_at", ""),
                    "time_window": tw_info.get("display", ""),
                    "duration": tw_info.get("duration", ""),
                    "start": tw_info.get("start", ""),
                    "end": tw_info.get("end", "")
                }
        except Exception:
            pass

    return jsonify({
        "has_token": bool(saved_token),
        "token_preview": token_preview,
        "has_gemini": bool(saved_gemini),
        "gemini_preview": gemini_preview,
        "cache_available": cache_exists,
        "cached_info": cached_info
    })


@app.route("/api/save_token", methods=["POST"])
def api_save_token():
    data = request.json or {}
    token = data.get("token", "").strip()
    gemini_key = data.get("gemini_api_key", "").strip()
    cfg = load_config()
    if token:
        cfg["token"] = token
    if gemini_key:
        cfg["gemini_api_key"] = gemini_key
    save_config(cfg)
    return jsonify({"success": True, "message": "Credentials updated successfully."})


_JOB_PROGRESS: Dict[str, Any] = {
    "active": False,
    "stage": "idle",
    "message": "System ready",
    "pct": 0,
    "error": None
}


def update_progress(stage: str, message: str, pct: int) -> None:
    global _JOB_PROGRESS
    _JOB_PROGRESS["active"] = True
    _JOB_PROGRESS["stage"] = stage
    _JOB_PROGRESS["message"] = message
    _JOB_PROGRESS["pct"] = max(0, min(100, pct))
    _JOB_PROGRESS["error"] = None
    print(f"[{pct}%] {stage.upper()}: {message}")


@app.route("/api/progress", methods=["GET"])
def api_progress():
    return jsonify(_JOB_PROGRESS)


@app.route("/api/predict", methods=["POST"])
def api_predict():
    global _JOB_PROGRESS
    data = request.json or {}
    channel_id = str(data.get("channel_id", "1516697578107043850")).strip()
    limit = int(data.get("limit", 10000))
    limit = max(50, min(100000, limit))
    confession = data.get("confession", "").strip()
    force_scrape = bool(data.get("force_scrape", False))

    if not confession:
        return jsonify({"error": "CONFESSION_EMPTY", "message": "Please enter a confession text to analyze."}), 400

    cfg = load_config()
    req_token = data.get("token", "").strip()
    req_gemini = data.get("gemini_api_key", "").strip()
    updated = False
    if req_token and req_token != cfg.get("token"):
        cfg["token"] = req_token
        updated = True
    if req_gemini and req_gemini != cfg.get("gemini_api_key"):
        cfg["gemini_api_key"] = req_gemini
        updated = True
    if updated:
        save_config(cfg)
        print("[+] Credentials saved to local config.json")

    token = req_token or cfg.get("token") or os.getenv("DISCORD_BOT_TOKEN")

    print(f"[*] API /predict received: limit={limit}, channel={channel_id}, token={'YES' if token else 'NO'}, confession='{confession[:70]}...'")

    update_progress("initializing", "Checking local corpus and parameters...", 5)

    corpus = get_cached_corpus(channel_id)
    cached_count = corpus.get("metadata", {}).get("human_messages_kept", 0) if corpus else 0
    scraped_new = False
    notice = None

    # Determine if we should perform incremental scraping
    if token:
        try:
            new_raw_messages = []

            # 1. Forward sync: check if new messages were sent today after the newest cached message
            if corpus and not force_scrape and corpus.get("metadata", {}).get("newest_message_id"):
                newest_id = corpus["metadata"]["newest_message_id"]
                update_progress("scraping", "Checking for latest messages sent in Discord...", 10)
                forward_msgs = scrape_discord.fetch_new_messages_forward(
                    token,
                    channel_id,
                    after_id=newest_id,
                    max_to_fetch=50000,
                    progress_callback=lambda cur, tot, msg: update_progress("scraping", f"Syncing latest: {cur:,} new messages...", 10 + int(min(cur / 1000, 1.0) * 20))
                )
                if forward_msgs:
                    print(f"[+] Forward sync fetched {len(forward_msgs)} new messages posted since last scrape!")
                    new_raw_messages.extend(forward_msgs)

            # 2. Backward sync: fetch older messages if requested limit exceeds cached count
            cached_count = corpus.get("metadata", {}).get("human_messages_kept", 0) if corpus else 0
            if force_scrape or cached_count < limit:
                before_id = None
                if corpus and not force_scrape:
                    before_id = corpus.get("metadata", {}).get("oldest_message_id")

                fetch_target = limit if force_scrape else (limit - cached_count)
                print(f"[*] Incrementally scraping {fetch_target} older messages for channel {channel_id} (before={before_id})...")

                def on_scrape_progress(cur, total, msg=""):
                    pct = int(30 + (cur / max(total, 1)) * 22)
                    detail = msg or f"Scraping Discord: {cur:,} / {total:,} messages..."
                    update_progress("scraping", detail, pct)

                older_raw = scrape_discord.fetch_messages(
                    token,
                    channel_id,
                    total_limit=fetch_target,
                    before_id=before_id,
                    progress_callback=on_scrape_progress
                )
                if older_raw:
                    new_raw_messages.extend(older_raw)

            if new_raw_messages:
                update_progress("merging", f"Merging and deduplicating {len(new_raw_messages):,} new messages...", 52)
                corpus = scrape_discord.merge_and_deduplicate_messages(
                    None if force_scrape else corpus,
                    new_raw_messages
                )

                specific_cache = os.path.join(BASE_DIR, f"cache_{channel_id}.json")
                with open(specific_cache, "w", encoding="utf-8") as f:
                    json.dump(corpus, f, indent=2, ensure_ascii=False)
                with open(CACHE_FILE, "w", encoding="utf-8") as f:
                    json.dump(corpus, f, indent=2, ensure_ascii=False)

                scraped_new = True
                cached_count = corpus.get("metadata", {}).get("human_messages_kept", len(new_raw_messages))

        except Exception as e:
            print(f"[!] Scrape warning: {e}")
            if not corpus or not corpus.get("authors"):
                _JOB_PROGRESS["active"] = False
                _JOB_PROGRESS["error"] = str(e)
                return jsonify({"error": "SCRAPE_FAILED", "message": str(e)}), 500
            notice = f"Could not fetch new messages ({str(e)}). Used {cached_count} cached messages."
    elif not token and cached_count < limit and cached_count > 0:
        notice = f"Analyzed {cached_count} cached messages. Add your Discord Token to fetch up to {limit} messages."

    # If no corpus available at all
    if not corpus or not corpus.get("authors"):
        _JOB_PROGRESS["active"] = False
        return jsonify({
            "error": "TOKEN_REQUIRED",
            "message": f"No cached messages found for channel {channel_id}. Please provide a Discord Bot Token to scrape."
        }), 400

    # Run Ensemble Stylometric Attribution
    try:
        def on_math_progress(stage, msg, pct):
            update_progress(stage, msg, pct)

        results = stylometrics.run_ensemble_attribution(
            corpus,
            confession,
            progress_callback=on_math_progress
        )
        results["channel_id"] = channel_id
        results["used_cache"] = not scraped_new
        results["total_cached_messages"] = cached_count
        results["notice"] = notice
        results["time_window"] = get_time_window_info(corpus)

        update_progress("complete", "Attribution complete!", 100)
        _JOB_PROGRESS["active"] = False

        return jsonify({"success": True, "data": results})
    except Exception as e:
        _JOB_PROGRESS["active"] = False
        _JOB_PROGRESS["error"] = str(e)
        return jsonify({"error": "ANALYSIS_FAILED", "message": str(e)}), 500


@app.route("/api/ai_analysis", methods=["POST"])
def api_ai_analysis():
    """Generates deep forensic dossier and motive analysis using Gemini 3.5 Flash."""
    data = request.json or {}
    confession = data.get("confession", "").strip()
    prediction_data = data.get("prediction_data", {})
    api_key = data.get("gemini_api_key", "").strip() or None

    if not confession or not prediction_data:
        return jsonify({"error": "MISSING_DATA", "message": "Confession text and mathematical prediction data are required."}), 400

    try:
        dossier = gemini_analyst.generate_forensic_dossier(confession, prediction_data, api_key=api_key)
        return jsonify({"success": True, "dossier": dossier})
    except Exception as e:
        print(f"[!] Gemini analysis error: {e}")
        return jsonify({"error": "GEMINI_ERROR", "message": str(e)}), 500


@app.route("/api/chat", methods=["POST"])
def api_chat():
    """Interactive interrogation chat agent powered by Gemini 3.5 Flash."""
    data = request.json or {}
    message = data.get("message", "").strip()
    history = data.get("history", [])
    confession = data.get("confession", "").strip()
    prediction_data = data.get("prediction_data", {})
    api_key = data.get("gemini_api_key", "").strip() or None

    if not message:
        return jsonify({"error": "MESSAGE_EMPTY", "message": "Please enter a question or command."}), 400

    try:
        reply = gemini_analyst.chat_interrogate(
            user_message=message,
            conversation_history=history,
            confession=confession,
            prediction_data=prediction_data,
            api_key=api_key
        )
        return jsonify({"success": True, "reply": reply})
    except Exception as e:
        print(f"[!] Gemini chat error: {e}")
        return jsonify({"error": "GEMINI_CHAT_ERROR", "message": str(e)}), 500


@app.route("/api/members", methods=["GET"])
def api_members():
    """Returns top active members for quick-selection in the UI."""
    corpus = get_cached_corpus("1516697578107043850")
    authors = corpus.get("authors", {})
    top = sorted(authors.items(), key=lambda x: len(x[1].get("messages", [])), reverse=True)[:80]
    member_list = []
    for uid, a in top:
        member_list.append({
            "uid": uid,
            "username": a.get("username", ""),
            "display_name": a.get("display_name", ""),
            "count": len(a.get("messages", []))
        })
    return jsonify({"success": True, "members": member_list})


@app.route("/api/behavioral_analysis", methods=["POST"])
def api_behavioral_analysis():
    """Analyzes a specific member's past messages and generates a 3-line roast."""
    data = request.json or {}
    person_query = data.get("person", "").strip()
    limit = int(data.get("limit", 100))
    channel_id = str(data.get("channel_id", "1516697578107043850")).strip()
    api_key = data.get("gemini_api_key", "").strip() or None

    if not person_query:
        return jsonify({"error": "MISSING_PERSON", "message": "Please specify a person's name or username to analyze."}), 400

    corpus = get_cached_corpus(channel_id)
    authors = corpus.get("authors", {})
    if not authors:
        return jsonify({"error": "NO_DATA", "message": "No server messages found in cache."}), 400

    matched_author = None
    q = person_query.lower()
    if q.startswith("@"):
        q = q[1:]

    # Pass 1: exact match on username (permanent handle, e.g. napkinwastaken)
    for uid, a in authors.items():
        if a.get("username", "").lower() == q:
            matched_author = a
            break

    # Pass 2: exact match on display name (e.g. napkin)
    if not matched_author:
        for uid, a in authors.items():
            if a.get("display_name", "").lower() == q:
                matched_author = a
                break

    # Pass 3: substring match prioritizing username
    if not matched_author:
        for uid, a in authors.items():
            if q in a.get("username", "").lower():
                matched_author = a
                break

    # Pass 4: substring match on display name
    if not matched_author:
        for uid, a in authors.items():
            if q in a.get("display_name", "").lower():
                matched_author = a
                break

    if not matched_author:
        return jsonify({
            "error": "MEMBER_NOT_FOUND",
            "message": f"Could not find member '{person_query}' in the server archives. Please check the spelling or select from the list."
        }), 404

    all_msgs = [m.get("content", "") for m in matched_author.get("messages", []) if m.get("content")]
    
    # Support arbitrary message sample size (or all available messages)
    if limit <= 0 or limit >= 50000:
        sample = all_msgs
    else:
        sample = all_msgs[-limit:] if len(all_msgs) > limit else all_msgs

    if not sample:
        return jsonify({
            "error": "NO_MESSAGES",
            "message": f"Member '{matched_author.get('display_name')}' has no text messages recorded."
        }), 400

    try:
        res = gemini_analyst.analyze_member_behavior(
            author_name=matched_author.get("display_name", "Unknown"),
            author_username=matched_author.get("username", "unknown"),
            messages=sample,
            api_key=api_key
        )
        res["member"] = {
            "display_name": matched_author.get("display_name", ""),
            "username": matched_author.get("username", ""),
            "analyzed_count": len(sample),
            "total_count": len(all_msgs)
        }
        return jsonify(res)
    except Exception as e:
        print(f"[!] Behavioral analysis error: {e}")
        return jsonify({"error": "ANALYSIS_FAILED", "message": str(e)}), 500


# Global Real-Time Background Scraper Job State
user_scrape_job: Dict[str, Any] = {
    "thread": None,
    "should_cancel": False,
    "active": False,
    "target_person": "",
    "target_uid": "",
    "target_count": 0,
    "user_found": 0,
    "user_start_total": 0,
    "user_current_total": 0,
    "channel_scanned": 0,
    "channel_total": 0,
    "percent": 0,
    "status_text": "Idle",
    "completed": False,
    "error": None
}
user_scrape_lock = threading.Lock()


def _run_background_user_scrape(channel_id: str, person_query: str, target_uid: Optional[str], fetch_goal: int, token: str):
    """Background worker thread that runs Discord scrape and streams live updates."""
    global user_scrape_job

    with user_scrape_lock:
        user_scrape_job["active"] = True
        user_scrape_job["should_cancel"] = False
        user_scrape_job["completed"] = False
        user_scrape_job["error"] = None
        user_scrape_job["target_person"] = person_query
        user_scrape_job["target_uid"] = target_uid or ""
        user_scrape_job["target_count"] = fetch_goal
        user_scrape_job["user_found"] = 0
        user_scrape_job["channel_scanned"] = 0
        user_scrape_job["percent"] = 0
        user_scrape_job["status_text"] = f"Connecting to Discord for {person_query}..."

    try:
        corpus = get_cached_corpus(channel_id)
        oldest_id = corpus.get("metadata", {}).get("oldest_message_id") if corpus else None

        def on_progress(scanned: int, found: int, msg: str):
            with user_scrape_lock:
                user_scrape_job["channel_scanned"] = scanned
                user_scrape_job["user_found"] = found
                user_scrape_job["user_current_total"] = user_scrape_job["user_start_total"] + found
                user_scrape_job["percent"] = min(100, int((found / max(fetch_goal, 1)) * 100))
                user_scrape_job["status_text"] = msg

        fetch_result = scrape_discord.fetch_messages_for_user_backward(
            token=token,
            channel_id=channel_id,
            target_author_query=person_query,
            target_uid=target_uid,
            target_user_new_count=fetch_goal,
            before_id=oldest_id,
            max_channel_scan=50000,
            progress_callback=on_progress,
            should_cancel=lambda: user_scrape_job.get("should_cancel", False)
        )

        older_raw = fetch_result.get("raw_messages", [])
        user_found = fetch_result.get("target_found_count", 0)
        reached_beginning = fetch_result.get("reached_beginning", False)

        if older_raw:
            updated_corpus = scrape_discord.merge_and_deduplicate_messages(corpus, older_raw)
            specific_cache = os.path.join(BASE_DIR, f"cache_{channel_id}.json")
            with open(specific_cache, "w", encoding="utf-8") as f:
                json.dump(updated_corpus, f, indent=2, ensure_ascii=False)
            with open(CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(updated_corpus, f, indent=2, ensure_ascii=False)

            user_total = 0
            if target_uid and target_uid in updated_corpus.get("authors", {}):
                user_total = len(updated_corpus["authors"][target_uid].get("messages", []))
            else:
                q = person_query.lower().strip()
                if q.startswith("@"): q = q[1:]
                for uid, a in updated_corpus.get("authors", {}).items():
                    if a.get("username", "").lower() == q or a.get("display_name", "").lower() == q or q in a.get("username", "").lower():
                        user_total = len(a.get("messages", []))
                        break

            meta = updated_corpus.get("metadata", {})
            channel_total = meta.get("human_messages_kept", 0)

            msg = f"Done! Found +{user_found} new messages for {person_query} (scanned {len(older_raw):,} Discord msgs). Total is now {user_total:,} msgs!"
            if reached_beginning:
                msg += " (Reached the very beginning of the Discord channel history)."

            with user_scrape_lock:
                user_scrape_job["user_found"] = user_found
                user_scrape_job["user_current_total"] = user_total
                user_scrape_job["channel_scanned"] = len(older_raw)
                user_scrape_job["channel_total"] = channel_total
                user_scrape_job["percent"] = 100
                user_scrape_job["status_text"] = msg
                user_scrape_job["completed"] = True
                user_scrape_job["active"] = False
        else:
            with user_scrape_lock:
                user_scrape_job["status_text"] = "Reached beginning of channel history. No older messages found."
                user_scrape_job["completed"] = True
                user_scrape_job["active"] = False
                user_scrape_job["percent"] = 100
    except Exception as e:
        print(f"[!] Background user scrape error: {e}")
        with user_scrape_lock:
            user_scrape_job["error"] = str(e)
            user_scrape_job["status_text"] = f"Error: {e}"
            user_scrape_job["completed"] = True
            user_scrape_job["active"] = False


@app.route("/api/start_fetch_user_messages", methods=["POST"])
def api_start_fetch_user_messages():
    """Starts asynchronous background Discord history scraper for a member with live tracking."""
    global user_scrape_job
    data = request.json or {}
    channel_id = str(data.get("channel_id", "1516697578107043850")).strip()
    person_query = data.get("person", "").strip()
    fetch_goal = int(data.get("count", 500))
    fetch_goal = max(50, min(5000, fetch_goal))

    if user_scrape_job.get("active"):
        return jsonify({
            "error": "ALREADY_ACTIVE",
            "message": f"A Discord scrape is currently running for {user_scrape_job.get('target_person')}. Please wait or cancel it."
        }), 409

    cfg = load_config()
    token = data.get("token", "").strip() or cfg.get("token") or os.getenv("DISCORD_BOT_TOKEN")
    if not token:
        return jsonify({"error": "TOKEN_REQUIRED", "message": "Discord bot token is required to fetch older messages."}), 400

    corpus = get_cached_corpus(channel_id)
    if not corpus:
        return jsonify({"error": "NO_CORPUS", "message": "No cache exists yet."}), 400

    # Look up author UID and initial count
    target_uid = None
    initial_count = 0
    q = person_query.lower().strip()
    if q.startswith("@"):
        q = q[1:]

    for uid, a in corpus.get("authors", {}).items():
        if a.get("username", "").lower() == q or a.get("display_name", "").lower() == q or q in a.get("username", "").lower():
            target_uid = uid
            initial_count = len(a.get("messages", []))
            break

    with user_scrape_lock:
        user_scrape_job["active"] = True
        user_scrape_job["should_cancel"] = False
        user_scrape_job["completed"] = False
        user_scrape_job["error"] = None
        user_scrape_job["target_person"] = person_query
        user_scrape_job["target_uid"] = target_uid or ""
        user_scrape_job["target_count"] = fetch_goal
        user_scrape_job["user_found"] = 0
        user_scrape_job["user_start_total"] = initial_count
        user_scrape_job["user_current_total"] = initial_count
        user_scrape_job["channel_scanned"] = 0
        user_scrape_job["percent"] = 0
        user_scrape_job["status_text"] = f"Starting targeted fetch for {person_query}..."

    t = threading.Thread(
        target=_run_background_user_scrape,
        args=(channel_id, person_query, target_uid, fetch_goal, token),
        daemon=True
    )
    user_scrape_job["thread"] = t
    t.start()

    return jsonify({
        "success": True,
        "message": f"Hunting +{fetch_goal} messages for {person_query} in background.",
        "initial_total": initial_count
    })


@app.route("/api/user_scrape_progress", methods=["GET"])
def api_user_scrape_progress():
    """Pollable endpoint for live scraping progress and real-time counter updates."""
    with user_scrape_lock:
        return jsonify({
            "active": user_scrape_job["active"],
            "target_person": user_scrape_job["target_person"],
            "target_count": user_scrape_job["target_count"],
            "user_found": user_scrape_job["user_found"],
            "user_start_total": user_scrape_job["user_start_total"],
            "user_current_total": user_scrape_job["user_current_total"],
            "channel_scanned": user_scrape_job["channel_scanned"],
            "channel_total": user_scrape_job["channel_total"],
            "percent": user_scrape_job["percent"],
            "status_text": user_scrape_job["status_text"],
            "completed": user_scrape_job["completed"],
            "error": user_scrape_job["error"]
        })


@app.route("/api/cancel_user_scrape", methods=["POST"])
def api_cancel_user_scrape():
    """Gracefully requests cancellation of active user history scrape."""
    with user_scrape_lock:
        if user_scrape_job["active"]:
            user_scrape_job["should_cancel"] = True
            user_scrape_job["status_text"] = "Cancelling and saving progress..."
            return jsonify({"success": True, "message": "Cancellation requested."})
        return jsonify({"success": True, "message": "No scrape currently running."})


@app.route("/api/fetch_more_user_messages", methods=["POST"])
def api_fetch_more_user_messages():
    """Backwards-compatible synchronous endpoint (redirects internally or runs synchronously)."""
    return api_start_fetch_user_messages()


@app.route("/api/sync_latest", methods=["POST"])
def api_sync_latest():
    """Syncs new messages posted in Discord since the newest cached message."""
    data = request.json or {}
    channel_id = str(data.get("channel_id", "1516697578107043850")).strip()
    cfg = load_config()
    token = data.get("token", "").strip() or cfg.get("token") or os.getenv("DISCORD_BOT_TOKEN")

    if not token:
        return jsonify({"error": "TOKEN_REQUIRED", "message": "Discord bot token is required to sync new messages."}), 400

    corpus = get_cached_corpus(channel_id)
    newest_id = corpus.get("metadata", {}).get("newest_message_id") if corpus else None

    try:
        new_raw_messages = scrape_discord.fetch_new_messages_forward(
            token,
            channel_id,
            after_id=newest_id or "0",
            max_to_fetch=50000
        )
        if new_raw_messages:
            updated_corpus = scrape_discord.merge_and_deduplicate_messages(corpus, new_raw_messages)
            specific_cache = os.path.join(BASE_DIR, f"cache_{channel_id}.json")
            with open(specific_cache, "w", encoding="utf-8") as f:
                json.dump(updated_corpus, f, indent=2, ensure_ascii=False)
            with open(CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(updated_corpus, f, indent=2, ensure_ascii=False)

            tw_info = get_time_window_info(updated_corpus)
            meta = updated_corpus.get("metadata", {})
            return jsonify({
                "success": True,
                "added_count": len(new_raw_messages),
                "total_messages": meta.get("human_messages_kept", 0),
                "total_authors": len(updated_corpus.get("authors", {})),
                "time_window": tw_info.get("display", ""),
                "message": f"Successfully synced {len(new_raw_messages):,} new messages from Discord!"
            })
        else:
            meta = corpus.get("metadata", {}) if corpus else {}
            tw_info = get_time_window_info(corpus) if corpus else {}
            return jsonify({
                "success": True,
                "added_count": 0,
                "total_messages": meta.get("human_messages_kept", 0),
                "total_authors": len(corpus.get("authors", {})) if corpus else 0,
                "time_window": tw_info.get("display", ""),
                "message": "Cache is already up to date with the latest messages."
            })
    except Exception as e:
        return jsonify({"error": "SYNC_FAILED", "message": str(e)}), 500


@app.route("/api/bot_status", methods=["GET"])
def api_bot_status():
    """Returns the live online presence status of the Discord Gateway Bot."""
    try:
        import bot
        b = bot.get_gateway_bot()
        return jsonify({
            "is_online": b.is_online,
            "username": b.bot_user.get("username") if b.bot_user else None,
            "id": b.bot_user.get("id") if b.bot_user else None,
            "status_message": b.status_message
        })
    except Exception as e:
        return jsonify({"is_online": False, "error": str(e)})


@app.route("/api/shutdown", methods=["POST"])
def api_shutdown():
    """Cleanly shuts down the web server and Discord bot."""
    def _do_shutdown():
        time.sleep(0.6)
        print("[*] Graceful shutdown requested. Terminating server and Discord bot...")
        os._exit(0)

    threading.Thread(target=_do_shutdown, daemon=True).start()
    return jsonify({"success": True, "message": "Server and Discord bot are shutting down..."})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    # Automatically start Discord Gateway bot so it shows ONLINE in Discord
    try:
        import bot
        gateway_bot = bot.get_gateway_bot()
        gateway_bot.start_background()
        print("[+] Discord Gateway bot background service launched.")
    except Exception as e:
        print(f"[!] Warning: Could not start Discord Gateway presence: {e}")

    print(f"[*] Starting Discord Stylometric & AI Analyzer on http://127.0.0.1:{port}")
    app.run(host="0.0.0.0", port=port, debug=False)
