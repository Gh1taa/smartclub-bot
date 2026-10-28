"""Tell Telegram where to send the messages.

On PythonAnywhere (once):          python3.11 set_webhook.py
Back to the PC version (bot.py):   python set_webhook.py --delete
"""
import os
import sys

import httpx

import webapp  # also loads .env

if "--delete" in sys.argv:
    r = httpx.post(f"{webapp.bot.API}/deleteWebhook", timeout=30)
else:
    url = sys.argv[1] if len(sys.argv) > 1 else f"https://{os.environ['USER'].lower()}.pythonanywhere.com/telegram"
    print(f"Webhook address: {url}")
    r = httpx.post(f"{webapp.bot.API}/setWebhook", timeout=30, json={
        "url": url, "secret_token": webapp.SECRET, "allowed_updates": ["message"], "max_connections": 1})
print(r.json())
