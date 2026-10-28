"""Smart Club assistant on Telegram.

Run:  python bot.py   (stop with Ctrl+C)

Commands:
  /start                       welcome message
  /myid                        shows your chat ID (put it in .env as ADMIN_CHAT_ID)
Admin only:
  /reply <chat_id> <message>   answer a student through the bot
  /resume <chat_id>            let the bot answer that student again
"""
import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import httpx
from dotenv import load_dotenv

ROOT = Path(__file__).parent
load_dotenv(ROOT / ".env")

import agent       # noqa: E402  (after load_dotenv so the keys are available)
import knowledge   # noqa: E402

API = f"https://api.telegram.org/bot{os.environ['TELEGRAM_BOT_TOKEN']}"
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID", "")
PAUSE_HOURS = 12  # how long the bot stays silent with a student after a handoff

WELCOME = ("Bonjour 👋 Je suis l'assistant de Smart Club ENSEM. Posez-moi vos questions sur le club : "
           "adhésion, formations, événements, projets…\n\n"
           "مرحباً 👋 أنا المساعد الآلي لنادي Smart Club ENSEM. اطرح أسئلتك حول النادي: الانضمام، التكوينات، الفعاليات، المشاريع…")
TEXT_ONLY = ("Désolé, je ne lis que les messages écrits. Pouvez-vous écrire votre question ?\n"
             "عذراً، أستطيع قراءة الرسائل المكتوبة فقط. هل يمكنك كتابة سؤالك؟")

paused: dict[int, float] = {}   # chat id -> time when the bot may answer again


def send(chat_id, text: str):
    for i in range(0, len(text), 4000):  # Telegram limit: 4096 characters per message
        httpx.post(f"{API}/sendMessage", json={"chat_id": chat_id, "text": text[i:i + 4000]}, timeout=30)


def show_typing(chat_id, stop: threading.Event):
    while not stop.is_set():  # "typing…" lasts about 5 seconds, so repeat it
        httpx.post(f"{API}/sendChatAction", json={"chat_id": chat_id, "action": "typing"}, timeout=30)
        stop.wait(4)


def notify_admin(text: str):
    if ADMIN_CHAT_ID:
        send(ADMIN_CHAT_ID, text)


def admin_command(text: str) -> str:
    parts = text.split(maxsplit=2)
    if parts[0] == "/reply" and len(parts) == 3:
        send(int(parts[1]), parts[2])
        return f"✓ Envoyé à {parts[1]}"
    if parts[0] == "/resume" and len(parts) >= 2:
        paused.pop(int(parts[1]), None)
        return f"✓ Le bot répond de nouveau à {parts[1]}"
    return "Utilisation : /reply <chat_id> <message>  ou  /resume <chat_id>"


def handle(msg: dict):
    chat_id = msg["chat"]["id"]
    if msg["chat"]["type"] != "private":
        return  # ignore groups
    text = (msg.get("text") or "").strip()
    user = msg.get("from", {})
    name = user.get("first_name", "?") + (f" (@{user['username']})" if user.get("username") else "")

    if text == "/start":
        return send(chat_id, WELCOME)
    if text == "/myid":
        return send(chat_id, f"Votre chat ID : {chat_id}")
    if text.split()[:1] in (["/reply"], ["/resume"]) and str(chat_id) == ADMIN_CHAT_ID:
        return send(chat_id, admin_command(text))
    if not text:
        return send(chat_id, TEXT_ONLY)

    if paused.get(chat_id, 0) > time.time():
        # A human is handling this student: forward the message instead of answering.
        return notify_admin(f"💬 {name} [{chat_id}] :\n{text}\n\n/reply {chat_id} votre message")

    print(f"IN  {name}: {text}")
    stop = threading.Event()
    threading.Thread(target=show_typing, args=(chat_id, stop), daemon=True).start()
    try:
        answer, handoff = agent.reply(str(chat_id), text)
    finally:
        stop.set()
    print(f"OUT {name}: {answer}")
    send(chat_id, answer)

    if handoff is not None:
        paused[chat_id] = time.time() + PAUSE_HOURS * 3600
        notify_admin(f"🙋 Transfert à un humain\nDe : {name} [{chat_id}]\nRaison : {handoff}\nMessage : {text}\n\n"
                     f"Répondre : /reply {chat_id} votre message\nRendre la main au bot : /resume {chat_id}")


def safe_handle(msg: dict):
    try:
        handle(msg)
    except Exception as e:
        print(f"ERROR while handling a message: {e!r}")


def main():
    me = httpx.get(f"{API}/getMe", timeout=30).json()
    if not me.get("ok"):
        raise SystemExit(f"Telegram rejected the token: {me.get('description')}")
    print(f"Loaded {knowledge.refresh()} pieces of club information.")
    knowledge.start_auto_refresh(minutes=5)
    if not ADMIN_CHAT_ID:
        print("ADMIN_CHAT_ID is empty: handoff alerts are off. Send /myid to the bot to get yours.")
    print(f"@{me['result']['username']} is running. Press Ctrl+C to stop.")

    pool = ThreadPoolExecutor(max_workers=8)  # answer several people at the same time
    offset = None
    while True:
        try:
            # Long polling: Telegram waits up to 50 s and returns as soon as a message arrives.
            data = httpx.post(f"{API}/getUpdates", json={"timeout": 50, "offset": offset}, timeout=60).json()
        except httpx.HTTPError:
            time.sleep(5)
            continue
        if not data.get("ok"):  # e.g. 409 Conflict: another copy of the bot is running
            print(f"Telegram: {data.get('description')}")
            time.sleep(5)
            continue
        for update in data.get("result", []):
            offset = update["update_id"] + 1
            if "message" in update:
                pool.submit(safe_handle, update["message"])


if __name__ == "__main__":
    main()
