"""The bot as a small website, for PythonAnywhere (free hosting, no credit card).

Instead of bot.py asking Telegram for new messages all the time, Telegram sends each message
to https://<your-username>.pythonanywhere.com/telegram (a "webhook"). Nothing has to run 24/7.
Setup: see PYTHONANYWHERE.md. Run set_webhook.py once to give Telegram the address.
"""
import hashlib
import json
import os

import bot        # loads .env, the agent and the Telegram helpers
import knowledge

# Telegram sends this secret with every message, so nobody else can post fake messages to the site.
SECRET = hashlib.sha256(os.environ["TELEGRAM_BOT_TOKEN"].encode()).hexdigest()[:32]
_seen: list[int] = []  # recent update ids: Telegram sends a message again if the answer took too long


def application(environ, start_response):
    if environ.get("PATH_INFO") == "/telegram" and environ["REQUEST_METHOD"] == "POST":
        if environ.get("HTTP_X_TELEGRAM_BOT_API_SECRET_TOKEN") != SECRET:
            start_response("403 Forbidden", [("Content-Type", "text/plain")])
            return [b"forbidden"]
        size = int(environ.get("CONTENT_LENGTH") or 0)
        update = json.loads(environ["wsgi.input"].read(size) or b"{}")
        if update.get("update_id") not in _seen:
            _seen.append(update.get("update_id"))
            del _seen[:-200]
            if "message" in update:
                knowledge.refresh_if_old(minutes=5)
                bot.safe_handle(update["message"])
        start_response("200 OK", [("Content-Type", "text/plain")])
        return [b"ok"]

    start_response("200 OK", [("Content-Type", "text/plain; charset=utf-8")])
    return ["Smart Club bot is running".encode()]
