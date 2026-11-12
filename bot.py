"""
Discord Gateway Client & Real-Time Bot Runner
---------------------------------------------
Connects to Discord's WebSocket Gateway to maintain an active 'ONLINE' presence 🟢
and handle live interactions (mentions, roasts, forensic queries).
"""

import asyncio
import json
import os
import sys
import time
import threading
import aiohttp
import requests
from typing import Optional, Dict, Any

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, "config.json")
GATEWAY_URL = "wss://gateway.discord.gg/?v=10&encoding=json"
DISCORD_API_BASE = "https://discord.com/api/v10"


def load_token() -> Optional[str]:
    """Retrieves Discord bot token from config.json or environment."""
    if os.getenv("DISCORD_BOT_TOKEN"):
        return os.getenv("DISCORD_BOT_TOKEN")
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("token")
        except Exception:
            pass
    return None


class DiscordGatewayBot:
    """Maintains active WebSocket connection to Discord Gateway."""

    def __init__(self, token: Optional[str] = None):
        self.token = token or load_token()
        self.bot_user: Optional[Dict[str, Any]] = None
        self.is_online = False
        self.should_stop = False
        self.last_sequence: Optional[int] = None
        self.session_id: Optional[str] = None
        self.resume_gateway_url: Optional[str] = None
        self.status_message = "Watching Confessions & Forensics"

    def send_channel_message(self, channel_id: str, content: str, reply_to_id: Optional[str] = None):
        """Sends a message back to a Discord channel via REST API."""
        if not self.token or not channel_id:
            return
        url = f"{DISCORD_API_BASE}/channels/{channel_id}/messages"
        headers = {
            "Authorization": f"Bot {self.token}",
            "Content-Type": "application/json"
        }
        payload: Dict[str, Any] = {"content": content[:2000]}
        if reply_to_id:
            payload["message_reference"] = {"message_id": reply_to_id}
        try:
            requests.post(url, headers=headers, json=payload, timeout=10)
        except Exception as e:
            print(f"[!] Error sending Discord message: {e}")

    async def heartbeat_loop(self, ws: aiohttp.ClientWebSocketResponse, interval_ms: float):
        """Sends periodic heartbeats to maintain gateway connection."""
        interval_sec = interval_ms / 1000.0
        while not self.should_stop and not ws.closed:
            try:
                await asyncio.sleep(interval_sec)
                if ws.closed or self.should_stop:
                    break
                await ws.send_json({"op": 1, "d": self.last_sequence})
            except Exception as e:
                print(f"[!] Gateway heartbeat error: {e}")
                break

    async def handle_message_create(self, data: Dict[str, Any]):
        """Processes incoming Discord messages."""
        author = data.get("author", {})
        if author.get("bot"):
            return

        bot_id = self.bot_user.get("id") if self.bot_user else None
        content = data.get("content", "").strip()
        channel_id = data.get("channel_id")
        msg_id = data.get("id")

        # Check if the bot was mentioned or prefix command used
        is_mentioned = bool(bot_id and f"<@{bot_id}>" in content or f"<@!{bot_id}>" in content)
        is_command = content.startswith("!forensic") or content.startswith("!roast") or content.startswith("!stats")

        if not (is_mentioned or is_command):
            return

        clean_text = content
        if bot_id:
            clean_text = clean_text.replace(f"<@{bot_id}>", "").replace(f"<@!{bot_id}>", "").strip()

        print(f"[*] Live Discord interaction from @{author.get('username')}: '{clean_text}'")

        # Handle simple stats command
        if clean_text.lower() in ["status", "stats", "ping", "info"] or is_command and "stats" in clean_text.lower():
            reply = (
                f"🟢 **Forensic AI Bot is ONLINE!**\n"
                f"- **Connected as:** `{self.bot_user.get('username')}#{self.bot_user.get('discriminator', '0000')}`\n"
                f"- **Web Dashboard:** `http://localhost:5000`\n"
                f"- **Engine:** 5-Layer Mathematical Stylometrics + Gemini Flash\n"
                f"Mention me with any question, confession, or member name to interrogate server records!"
            )
            self.send_channel_message(channel_id, reply, reply_to_id=msg_id)
            return

        # Attempt to consult Gemini Forensic Analyst if installed
        try:
            import gemini_analyst
            reply = gemini_analyst.chat_interrogate(
                user_message=clean_text or "Hello! What can you do?",
                conversation_history=[],
                confession="",
                prediction_data={}
            )
            if reply:
                # Discord character limit is 2000
                chunks = [reply[i:i + 1950] for i in range(0, len(reply), 1950)]
                for chunk in chunks[:3]:
                    self.send_channel_message(channel_id, chunk, reply_to_id=msg_id)
                return
        except Exception as e:
            print(f"[!] Error processing AI response in Discord: {e}")

        # Fallback response
        self.send_channel_message(
            channel_id,
            f"🕵️ **Forensic Agent Active.** Received your inquiry: *\"{clean_text[:100]}\"*\nAccess the full investigation dashboard at `http://localhost:5000`.",
            reply_to_id=msg_id
        )

    async def run(self):
        """Main connection and reconnection loop."""
        if not self.token:
            print("[!] Cannot start bot: No Discord token configured in config.json or environment.")
            return

        while not self.should_stop:
            url = self.resume_gateway_url or GATEWAY_URL
            try:
                connector = aiohttp.TCPConnector(ssl=False)
                async with aiohttp.ClientSession(connector=connector) as session:
                    print(f"[*] Connecting to Discord Gateway...")
                    async with session.ws_connect(url) as ws:
                        heartbeat_task = None
                        async for msg in ws:
                            if self.should_stop:
                                break
                            if msg.type == aiohttp.WSMsgType.TEXT:
                                payload = json.loads(msg.data)
                                op = payload.get("op")
                                t = payload.get("t")
                                s = payload.get("s")
                                d = payload.get("d")

                                if s is not None:
                                    self.last_sequence = s

                                # OP 10: Hello
                                if op == 10:
                                    interval = d.get("heartbeat_interval", 41250)
                                    heartbeat_task = asyncio.create_task(self.heartbeat_loop(ws, interval))

                                    # Identify
                                    identify_payload = {
                                        "op": 2,
                                        "d": {
                                            "token": self.token,
                                            "intents": 33280,  # GUILDS (1) + GUILD_MESSAGES (512) + MESSAGE_CONTENT (32768)
                                            "properties": {
                                                "os": sys.platform,
                                                "browser": "discord-forensic-agent",
                                                "device": "discord-forensic-agent"
                                            },
                                            "presence": {
                                                "status": "online",
                                                "activities": [{
                                                    "name": self.status_message,
                                                    "type": 3  # Watching
                                                }],
                                                "afk": False
                                            }
                                        }
                                    }
                                    await ws.send_json(identify_payload)

                                # Dispatch
                                elif op == 0:
                                    if t == "READY":
                                        self.bot_user = d.get("user", {})
                                        self.session_id = d.get("session_id")
                                        self.resume_gateway_url = d.get("resume_gateway_url")
                                        self.is_online = True
                                        username = self.bot_user.get("username", "Unknown")
                                        bot_id = self.bot_user.get("id", "")
                                        print(f"[🟢 ONLINE] Discord Bot logged in as '{username}' (ID: {bot_id})")
                                        print(f"[🟢 ONLINE] Presence set to: 'Watching {self.status_message}'")
                                    elif t == "MESSAGE_CREATE":
                                        asyncio.create_task(self.handle_message_create(d))

                                # OP 7: Reconnect
                                elif op == 7:
                                    print("[*] Gateway requested reconnect.")
                                    break

                                # OP 9: Invalid session
                                elif op == 9:
                                    print("[!] Invalid gateway session. Re-authenticating...")
                                    self.session_id = None
                                    break

                            elif msg.type in (aiohttp.WSMsgType.CLOSED, aiohttp.WSMsgType.ERROR):
                                break

                        if heartbeat_task and not heartbeat_task.done():
                            heartbeat_task.cancel()

            except Exception as e:
                print(f"[!] Gateway connection dropped: {e}")

            if not self.should_stop:
                self.is_online = False
                print("[*] Waiting 5 seconds before reconnecting...")
                await asyncio.sleep(5)

    def start_background(self):
        """Starts the gateway bot in a separate background daemon thread."""
        def _thread_target():
            asyncio.run(self.run())

        t = threading.Thread(target=_thread_target, daemon=True, name="DiscordGatewayBotThread")
        t.start()
        return t


# Singleton instance
_bot_instance: Optional[DiscordGatewayBot] = None


def get_gateway_bot() -> DiscordGatewayBot:
    """Returns singleton gateway bot instance."""
    global _bot_instance
    if _bot_instance is None:
        _bot_instance = DiscordGatewayBot()
    return _bot_instance


if __name__ == "__main__":
    print("[*] Starting standalone Discord Gateway Bot...")
    bot = get_gateway_bot()
    try:
        asyncio.run(bot.run())
    except KeyboardInterrupt:
        print("\n[*] Bot stopped by user.")
