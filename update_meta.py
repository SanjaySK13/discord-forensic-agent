import json
from datetime import datetime

filepath = r"C:\Users\sanja\.gemini\antigravity\scratch\discord_scraper\discord_messages.json"
data = json.load(open(filepath, encoding="utf-8"))
timestamps = [m.get("timestamp") for a in data.get("authors", {}).values() for m in a.get("messages", []) if m.get("timestamp")]
timestamps.sort()
if timestamps:
    t0 = datetime.fromisoformat(timestamps[0])
    t1 = datetime.fromisoformat(timestamps[-1])
    diff = t1 - t0
    dur = f"{diff.days}d {diff.seconds // 3600}h {(diff.seconds % 3600) // 60}m"
    disp = f"{t0.strftime('%b %d, %H:%M')} → {t1.strftime('%b %d, %H:%M UTC')} ({dur})"
    data["metadata"]["oldest_timestamp"] = timestamps[0]
    data["metadata"]["newest_timestamp"] = timestamps[-1]
    data["metadata"]["duration"] = dur
    data["metadata"]["time_window"] = disp
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print("Updated metadata successfully:", disp)

