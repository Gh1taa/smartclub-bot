# Smart Club Telegram assistant (simple version)

Answers students on Telegram in French or Arabic, from the club's information, and alerts
an admin when a human is needed.

## Files
| File | What it does |
|---|---|
| `bot.py` | Telegram: receives messages, replies, commands, handoff alerts |
| `agent.py` | The AI agent: Gemini + 2 tools (search the club info, hand off to a human) |
| `knowledge.py` | Loads `knowledge/` + the Google Sheet, and finds the right info for a question |
| `prompt.md` | The bot's rules (edit freely, applies on the next message) |
| `knowledge/` | The club's information as text files |
| `.env` | Your keys (never share) |
| `host.py` | Starts the bot on Render (free 24/7 hosting), see `DEPLOY.md` |
| `webapp.py`, `set_webhook.py` | The bot as a website on PythonAnywhere (free, no card), see `PYTHONANYWHERE.md` |
| `.python-version` | Python version used on Render |

This folder is self-contained: copy or move it anywhere, it needs nothing outside it
(except Python installed on the PC).

## Easiest: double-click `start_bot.bat`
The first time it installs everything into `.venv` (a minute or two), then starts the bot.
Close the window to stop the bot.

## Setup by hand (once)
```
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
```
Copy `.env.example` to `.env` and fill it in.

## Run
```
.venv\Scripts\python bot.py
```
The bot runs while this window is open. Stop it with Ctrl+C.

## Updating the information
- Edit files in `knowledge/` or rows in the Google Sheet. The bot reloads every 5 minutes
  (or restart it to reload now).
- Sheet columns: `Sujet` | `Information` | `Lien` | `Actif` (`non` hides a row).

## Handoff to a human
1. Send `/myid` to the bot and put the number in `.env` as `ADMIN_CHAT_ID`, then restart.
2. When a student needs a person, you get an alert. Answer with `/reply <chat_id> <message>`,
   and give control back with `/resume <chat_id>` (or it resumes by itself after 12 hours).

Conversations are kept in memory: restarting the bot forgets them.
