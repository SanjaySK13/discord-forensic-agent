"""
Discord Channel Message Scraper & Grouping Utility
--------------------------------------------------
Fetches messages from a Discord channel using the Discord REST API,
filters out bot messages, and groups them by author into clean JSON and text files.
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import requests

API_BASE = "https://discord.com/api/v10"


def fetch_messages(
    token: str,
    channel_id: str,
    total_limit: int = 1000,
    is_bot: bool = True,
    before_id: Optional[str] = None,
    progress_callback: Optional[Any] = None
) -> List[Dict[str, Any]]:
    """
    Fetches up to `total_limit` messages from a Discord channel using pagination.
    Optionally starts before `before_id` for incremental backwards pagination.
    """
    auth_header = f"Bot {token}" if is_bot and not token.startswith("Bot ") else token
    headers = {
        "Authorization": auth_header,
        "User-Agent": "DiscordMessageScraper/1.0 (Python/requests)",
        "Content-Type": "application/json",
    }

    messages: List[Dict[str, Any]] = []
    batch_size = 100

    print(f"[*] Starting scrape of channel {channel_id} (Target: {total_limit} messages)...")

    while len(messages) < total_limit:
        fetch_count = min(batch_size, total_limit - len(messages))
        params: Dict[str, Any] = {"limit": fetch_count}
        if before_id:
            params["before"] = before_id

        url = f"{API_BASE}/channels/{channel_id}/messages"
        response = requests.get(url, headers=headers, params=params)

        if response.status_code == 429:
            retry_data = response.json()
            retry_after = retry_data.get("retry_after", 1.0)
            print(f"[!] Rate limited. Waiting {retry_after:.2f} seconds...")
            if progress_callback:
                try:
                    progress_callback(len(messages), total_limit, f"Rate limited by Discord. Waiting {retry_after:.1f}s...")
                except Exception:
                    pass
            time.sleep(retry_after)
            continue

        if response.status_code == 401:
            print("[X] Error 401: Unauthorized. Please check your Discord bot token.")
            raise PermissionError("Error 401: Unauthorized Discord bot token.")

        if response.status_code == 403:
            print("[X] Error 403: Forbidden. Ensure bot has View Channel & Read History permissions.")
            raise PermissionError("Error 403: Forbidden. Bot lacks channel permissions.")

        if response.status_code == 404:
            print(f"[X] Error 404: Channel ID {channel_id} not found.")
            raise FileNotFoundError(f"Error 404: Channel ID {channel_id} not found.")

        if not response.ok:
            print(f"[X] HTTP error {response.status_code}: {response.text}")
            response.raise_for_status()

        batch = response.json()
        if not batch:
            print("[*] No more older messages found in channel.")
            break

        messages.extend(batch)
        before_id = batch[-1]["id"]
        print(f"    Fetched {len(messages)} / {total_limit} messages...")

        if progress_callback:
            try:
                progress_callback(len(messages), total_limit, f"Fetched {len(messages):,} / {total_limit:,} messages from Discord...")
            except Exception:
                pass

        time.sleep(0.35)

    return messages


def fetch_new_messages_forward(
    token: str,
    channel_id: str,
    after_id: str,
    max_to_fetch: int = 50000,
    is_bot: bool = True,
    progress_callback: Optional[Any] = None
) -> List[Dict[str, Any]]:
    """
    Fetches all new messages posted AFTER `after_id` up to the present.
    Discord returns messages in ascending chronological order when using 'after'.
    """
    auth_header = f"Bot {token}" if is_bot and not token.startswith("Bot ") else token
    headers = {
        "Authorization": auth_header,
        "User-Agent": "DiscordMessageScraper/1.0 (Python/requests)",
        "Content-Type": "application/json",
    }
    new_messages: List[Dict[str, Any]] = []
    current_after = after_id

    print(f"[*] Checking for new messages after ID {after_id}...")

    while len(new_messages) < max_to_fetch:
        params: Dict[str, Any] = {"limit": 100, "after": current_after}
        url = f"{API_BASE}/channels/{channel_id}/messages"
        response = requests.get(url, headers=headers, params=params)

        if response.status_code == 429:
            retry_after = response.json().get("retry_after", 1.0)
            print(f"[!] Rate limited. Waiting {retry_after:.2f}s...")
            if progress_callback:
                progress_callback(len(new_messages), max_to_fetch, f"Rate limited. Waiting {retry_after:.1f}s...")
            time.sleep(retry_after)
            continue

        if not response.ok:
            print(f"[!] Forward sync request returned {response.status_code}: {response.text}")
            break

        batch = response.json()
        if not batch:
            print("[*] Reached latest head message. No more new messages.")
            break

        new_messages.extend(batch)
        batch_sorted = sorted(batch, key=lambda m: int(m["id"]))
        current_after = batch_sorted[-1]["id"]
        print(f"    Synced {len(new_messages)} new messages so far...")

        if progress_callback:
            progress_callback(len(new_messages), len(new_messages), f"Synced {len(new_messages):,} new messages...")

        if len(batch) < 100:
            break

        time.sleep(0.35)

    return new_messages


def fetch_messages_for_user_backward(
    token: str,
    channel_id: str,
    target_author_query: str = "",
    target_uid: Optional[str] = None,
    target_user_new_count: int = 500,
    before_id: Optional[str] = None,
    max_channel_scan: int = 50000,
    is_bot: bool = True,
    progress_callback: Optional[Any] = None,
    should_cancel: Optional[Any] = None
) -> Dict[str, Any]:
    """
    Scrapes Discord channel history backwards specifically hunting for messages
    belonging to `target_author_query` / `target_uid`.
    Paginates backwards until `target_user_new_count` messages from this user are collected,
    or until `max_channel_scan` total messages are inspected, or until channel start.
    """
    auth_header = f"Bot {token}" if is_bot and not token.startswith("Bot ") else token
    headers = {
        "Authorization": auth_header,
        "User-Agent": "DiscordMessageScraper/1.0 (Python/requests)",
        "Content-Type": "application/json",
    }
    
    q = target_author_query.lower().strip()
    if q.startswith("@"):
        q = q[1:]

    all_scraped_messages: List[Dict[str, Any]] = []
    target_found_count = 0
    current_before = before_id
    reached_beginning = False

    print(f"[*] Starting targeted backward scrape for '{target_author_query}' (UID: {target_uid}, Goal: +{target_user_new_count} msgs, before={before_id})...")

    while len(all_scraped_messages) < max_channel_scan:
        # Check cancellation request
        if should_cancel and should_cancel():
            print("[*] User cancelled scrape operation.")
            break

        params: Dict[str, Any] = {"limit": 100}
        if current_before:
            params["before"] = current_before

        url = f"{API_BASE}/channels/{channel_id}/messages"
        response = requests.get(url, headers=headers, params=params)

        if response.status_code == 429:
            retry_data = response.json() if "application/json" in response.headers.get("content-type", "") else {}
            retry_after = float(retry_data.get("retry_after", 1.5))
            backoff = retry_after + 0.35
            print(f"[!] Discord rate limit (429). Pausing {backoff:.2f}s...")
            if progress_callback:
                progress_callback(len(all_scraped_messages), target_found_count, f"Discord rate limit. Pausing {backoff:.1f}s...")
            time.sleep(backoff)
            continue

        if not response.ok:
            print(f"[!] Discord API returned {response.status_code}: {response.text}")
            break

        batch = response.json()
        if not batch:
            print("[*] Reached the very beginning of the Discord channel history!")
            reached_beginning = True
            break

        all_scraped_messages.extend(batch)
        current_before = batch[-1]["id"]

        # Accurate user matching: UID match takes precedence, then username/display
        batch_matched = 0
        if target_uid or q:
            for m in batch:
                author = m.get("author", {})
                u_id = str(author.get("id", ""))
                u_name = author.get("username", "").lower()
                d_name = (author.get("global_name") or author.get("display_name") or "").lower()
                
                is_match = False
                if target_uid and u_id == target_uid:
                    is_match = True
                elif q and (q == u_name or q == d_name or q == u_id or (len(q) >= 3 and (q in u_name or q in d_name))):
                    is_match = True

                if is_match:
                    target_found_count += 1
                    batch_matched += 1
        else:
            target_found_count = len(all_scraped_messages)

        if progress_callback:
            progress_callback(
                len(all_scraped_messages),
                target_found_count,
                f"Scanned {len(all_scraped_messages):,} Discord msgs — Found +{target_found_count} / {target_user_new_count} for '{target_author_query}'..."
            )

        # Stop if we hit the user target
        if (target_uid or q) and target_found_count >= target_user_new_count:
            print(f"[+] Reached target of +{target_user_new_count} messages for '{target_author_query}'! (Total scanned: {len(all_scraped_messages)})")
            break

        if len(batch) < 100:
            print("[*] Reached end of available Discord messages.")
            reached_beginning = True
            break

        time.sleep(0.42)

    return {
        "raw_messages": all_scraped_messages,
        "target_found_count": target_found_count,
        "reached_beginning": reached_beginning,
        "channel_scanned": len(all_scraped_messages)
    }


def merge_and_deduplicate_messages(
    existing_corpus: Optional[Dict[str, Any]],
    new_raw_messages: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Merges newly scraped raw messages with an existing corpus, deduplicating
    by message ID so existing history is never overwritten or lost.
    """
    all_raw_messages: Dict[str, Dict[str, Any]] = {}

    # Extract all messages from existing corpus
    if existing_corpus and "authors" in existing_corpus:
        for aid, a_data in existing_corpus["authors"].items():
            author_info = {
                "id": a_data.get("author_id", aid),
                "username": a_data.get("username", "Unknown"),
                "global_name": a_data.get("display_name", "Unknown"),
                "bot": False
            }
            for m in a_data.get("messages", []):
                mid = str(m.get("id"))
                all_raw_messages[mid] = {
                    "id": mid,
                    "timestamp": m.get("timestamp"),
                    "content": m.get("content", ""),
                    "author": author_info,
                    "attachments": [{"url": u} for u in m.get("attachments", [])]
                }

    # Add/merge new raw messages
    for msg in new_raw_messages:
        mid = str(msg.get("id"))
        all_raw_messages[mid] = msg

    # Re-group into clean author structure
    return process_and_group(list(all_raw_messages.values()))


def process_and_group(messages: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Filters out bot messages and groups human messages by author.
    """
    grouped: Dict[str, Dict[str, Any]] = {}
    ignored_bots = 0
    total_human_messages = 0

    # Sort chronologically (earliest to latest)
    messages_sorted = sorted(messages, key=lambda m: m["id"])

    for msg in messages_sorted:
        author = msg.get("author", {})
        if author.get("bot", False):
            ignored_bots += 1
            continue

        author_id = author.get("id", "unknown")
        username = author.get("username", "Unknown")
        global_name = author.get("global_name") or username

        if author_id not in grouped:
            grouped[author_id] = {
                "author_id": author_id,
                "username": username,
                "display_name": global_name,
                "message_count": 0,
                "messages": []
            }
        else:
            # Continuously update to the latest active username and display name
            if username and username != "Unknown":
                grouped[author_id]["username"] = username
            if global_name and global_name != "Unknown":
                grouped[author_id]["display_name"] = global_name

        grouped[author_id]["message_count"] += 1
        grouped[author_id]["messages"].append({
            "id": msg.get("id"),
            "timestamp": msg.get("timestamp"),
            "content": msg.get("content", ""),
            "attachments": [a.get("url") for a in msg.get("attachments", [])],
        })
        total_human_messages += 1

    oldest_id = messages_sorted[0]["id"] if messages_sorted else None
    newest_id = messages_sorted[-1]["id"] if messages_sorted else None

    # Calculate actual timestamp window
    timestamps = [m.get("timestamp") for m in messages_sorted if m.get("timestamp")]
    timestamps.sort()
    oldest_ts = timestamps[0] if timestamps else None
    newest_ts = timestamps[-1] if timestamps else None

    time_window_str = ""
    duration_str = ""
    if oldest_ts and newest_ts:
        try:
            t0 = datetime.fromisoformat(oldest_ts)
            t1 = datetime.fromisoformat(newest_ts)
            diff = t1 - t0
            days = diff.days
            hours = diff.seconds // 3600
            mins = (diff.seconds % 3600) // 60
            dur_parts = []
            if days > 0: dur_parts.append(f"{days}d")
            if hours > 0 or days > 0: dur_parts.append(f"{hours}h")
            dur_parts.append(f"{mins}m")
            duration_str = " ".join(dur_parts)
            time_window_str = f"{t0.strftime('%b %d, %H:%M')} → {t1.strftime('%b %d, %H:%M UTC')} ({duration_str})"
        except Exception:
            pass

    return {
        "metadata": {
            "total_messages_retrieved": len(messages),
            "bot_messages_ignored": ignored_bots,
            "human_messages_kept": total_human_messages,
            "unique_authors": len(grouped),
            "oldest_message_id": oldest_id,
            "newest_message_id": newest_id,
            "oldest_timestamp": oldest_ts,
            "newest_timestamp": newest_ts,
            "duration": duration_str,
            "time_window": time_window_str,
            "generated_at": datetime.now(timezone.utc).isoformat()
        },
        "authors": grouped
    }


def save_to_json(data: Dict[str, Any], filepath: str) -> None:
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"[+] Saved grouped JSON output to: {filepath}")


def save_to_text(data: Dict[str, Any], filepath: str) -> None:
    with open(filepath, "w", encoding="utf-8") as f:
        meta = data["metadata"]
        f.write("=" * 80 + "\n")
        f.write("DISCORD MESSAGES GROUPED BY AUTHOR\n")
        f.write(f"Generated At: {meta['generated_at']}\n")
        f.write(f"Total Scraped: {meta['total_messages_retrieved']} | Ignored Bots: {meta['bot_messages_ignored']} | Human Messages: {meta['human_messages_kept']} | Unique Authors: {meta['unique_authors']}\n")
        f.write("=" * 80 + "\n\n")

        for author_id, user_data in data["authors"].items():
            f.write(f"Author: {user_data['display_name']} (@{user_data['username']}) [ID: {author_id}]\n")
            f.write(f"Total Messages: {user_data['message_count']}\n")
            f.write("-" * 60 + "\n")

            for m in user_data["messages"]:
                ts = m["timestamp"]
                content = m["content"]
                f.write(f"  [{ts}] {content}\n")
                if m["attachments"]:
                    f.write(f"    Attachments: {', '.join(m['attachments'])}\n")

            f.write("\n" + "=" * 80 + "\n\n")

    print(f"[+] Saved human-readable text output to: {filepath}")


def main():
    parser = argparse.ArgumentParser(description="Scrape and group Discord messages by author.")
    parser.add_argument("--token", type=str, default=os.getenv("DISCORD_BOT_TOKEN"),
                        help="Discord bot token (or set DISCORD_BOT_TOKEN environment variable)")
    parser.add_argument("--channel-id", type=str, default="1516697578107043850",
                        help="Discord channel ID to scrape")
    parser.add_argument("--limit", type=int, default=1000,
                        help="Maximum number of messages to fetch (default: 1000)")
    parser.add_argument("--out-json", type=str, default="discord_messages.json",
                        help="Path for output JSON file")
    parser.add_argument("--out-txt", type=str, default="discord_messages.txt",
                        help="Path for output text file")
    parser.add_argument("--mock", action="store_true",
                        help="Run in mock/simulation mode with generated messages for testing")

    args = parser.parse_args()

    if args.mock:
        print("[*] Running in mock test mode (generating 1000 sample messages)...")
        import random
        users = [
            {"id": "1001", "username": "alice", "global_name": "Alice in Wonderland", "bot": False},
            {"id": "1002", "username": "bob_builder", "global_name": "Bob B.", "bot": False},
            {"id": "1003", "username": "charlie_brown", "global_name": "Charlie", "bot": False},
            {"id": "9999", "username": "mee6", "global_name": "MEE6", "bot": True},
            {"id": "9998", "username": "midjourney_bot", "global_name": "Midjourney", "bot": True},
        ]
        sample_texts = [
            "Hey everyone! Has anyone looked into the latest release?",
            "Yes, testing it right now.",
            "Looks good on my end. Any blockers?",
            "Just checked the metrics, latency dropped by 15ms.",
            "Awesome work team!",
            "Level up! You are now level 10.",
            "Can you review my PR?",
            "LGTM! Merging now.",
        ]
        raw_messages = []
        base_id = 1500000000000000000
        for i in range(args.limit):
            user = random.choice(users)
            raw_messages.append({
                "id": str(base_id + i),
                "timestamp": f"2026-11-10T{(10 + (i // 100)) % 24:02d}:{(i % 60):02d}:00Z",
                "content": random.choice(sample_texts),
                "author": user,
                "attachments": []
            })
    elif not args.token:
        print("[!] Error: No Discord token provided.")
        print("    Please provide a bot token via --token <TOKEN> or by setting the DISCORD_BOT_TOKEN env variable.")
        print("\nExample:")
        print(f"    python {os.path.basename(__file__)} --token \"YOUR_BOT_TOKEN\" --channel-id {args.channel_id} --limit {args.limit}")
        print("    Or test the pipeline with: python scrape_discord.py --mock")
        sys.exit(1)
    else:
        raw_messages = fetch_messages(args.token, args.channel_id, total_limit=args.limit)
    processed = process_and_group(raw_messages)

    save_to_json(processed, args.out_json)
    save_to_text(processed, args.out_txt)

    meta = processed["metadata"]
    print("\n[✓] Done!")
    print(f"    Scraped: {meta['total_messages_retrieved']}")
    print(f"    Bot messages ignored: {meta['bot_messages_ignored']}")
    print(f"    Human messages saved: {meta['human_messages_kept']}")
    print(f"    Unique authors: {meta['unique_authors']}")


if __name__ == "__main__":
    main()
