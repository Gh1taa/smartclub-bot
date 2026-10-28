# Put the bot online 24/7 (free, no credit card)

Today the bot only works while your PC is on. These steps move it to **Render** (free web
service, no credit card), and use **cron-job.org** (free) to keep it awake.

Total time: about 30 minutes. You only do this once.

> Render asks some new accounts for a card even on the free plan. If that happens, use
> `PYTHONANYWHERE.md` instead (free, no card).

## Why Render + cron-job.org?

| Host | Free without a card? | Runs 24/7? |
|---|---|---|
| **Render (free web service)** | ✅ Yes | ✅ Yes, if something visits it every few minutes (that is cron-job.org's job). 750 free hours/month, a month has at most 744. |
| Koyeb | ❌ Card required since 2026 | Sleeps after 1 h |
| Railway | Trial only, then ~$1/month of credit: not enough for 24/7 | ❌ |
| Fly.io, Oracle Cloud, Google Cloud | ❌ Card required | — |
| PythonAnywhere (free) | ✅ | ❌ Programs that run forever ("always-on tasks") are paid only |

How it works: a free Render web service falls asleep after 15 minutes without visits.
`host.py` opens a tiny page ("Smart Club bot is running") and cron-job.org visits it every
10 minutes, so it never sleeps. If it ever does fall asleep, Telegram keeps students'
messages (up to 24 h) and the bot answers them when it wakes up.

---

## ⚠️ Rule n°1: only ONE copy of the bot at a time

Telegram lets only one program read the bot's messages. If your PC copy and the Render copy
run together, they fight and you see `Telegram: Conflict: terminated by other getUpdates request`
in the logs (error 409), and students get answers late or not at all.

👉 **Before step 4, stop the bot on your PC**: go to the black window where it runs and press
`Ctrl + C` (or close the window). From then on, do not start the bot on the PC again
(`start_bot.bat`), unless you suspend the Render service first
(see "Use the PC again" at the end).

---

## Step 1: Put the code on GitHub (private)

Render takes the code from GitHub.

1. Go to <https://github.com> and create a free account (or sign in). No card needed.
2. Top right, click **+** → **New repository**.
   - Repository name: `smartclub-bot`
   - Choose **Private** ⚠️ (important)
   - Leave the rest unticked, click **Create repository**.
3. On the next page, click the link **uploading an existing file**.
4. Open the `telegram-simple` folder in File Explorer.
   Select **everything EXCEPT** these two:
   - ❌ `.env` (your secret keys: never upload it)
   - ❌ `embeddings_cache.json` (not needed, rebuilt automatically)

   (If you also see `.venv` or `__pycache__` there, leave those out too.)

   Tip: press `Ctrl + A` to select all, then hold `Ctrl` and click `.env` and
   `embeddings_cache.json` to unselect them.

   You should be uploading: `knowledge` (folder), `.env.example`, `.gitignore`,
   `.python-version`, `agent.py`, `bot.py`, `DEPLOY.md`, `host.py`, `knowledge.py`,
   `prompt.md`, `README.md`, `requirements.txt`.
5. Drag the selection into the GitHub page (use Chrome or Edge on the PC).
6. Wait for the upload, then click **Commit changes** at the bottom.
7. Check: the repo page shows the files with `bot.py`, `host.py`, `requirements.txt`
   and the `knowledge` folder **at the top level** (not inside another folder), and **no `.env`**.
   If you see `.env`: click it → `...` (top right) → **Delete file** → **Commit changes**,
   then change your keys (Gemini key on aistudio.google.com, bot token with
   @BotFather `/revoke`), because they were exposed.

## Step 2: Create the bot on Render

1. Go to <https://render.com> → **Get Started** → **GitHub** (sign in with your GitHub account).
   No card is asked for the free plan. If it ever asks for a card, stop and tell me.
2. In the dashboard click **+ New** → **Web Service**.
3. Under **Git Provider**, click **GitHub** / **Configure GitHub**, allow Render to see
   the repo `smartclub-bot` ("Only select repositories" → pick `smartclub-bot` → **Install**).
4. Click `smartclub-bot` in the list → **Connect**.
5. Fill the form exactly like this:

   | Field | Value |
   |---|---|
   | Name | `smartclub-bot` |
   | Language | `Python 3` |
   | Branch | `main` |
   | Region | `Frankfurt (EU Central)` (closest to Morocco) |
   | Root Directory | *(leave empty)* |
   | Build Command | `pip install -r requirements.txt` |
   | Start Command | `python host.py` |
   | Instance Type | **Free** ⚠️ |

6. Scroll to **Environment Variables**. Click **Add Environment Variable** for each line
   below. Copy each value from your `.env` file (open it with Notepad on your PC):

   | NAME | VALUE |
   |---|---|
   | `TELEGRAM_BOT_TOKEN` | same as in `.env` |
   | `GEMINI_API_KEY` | same as in `.env` |
   | `GEMINI_MODEL` | same as in `.env` (e.g. `gemini-3.5-flash`) |
   | `SHEET_CSV_URL` | same as in `.env` |
   | `ADMIN_CHAT_ID` | same as in `.env` |
   | `PYTHONUNBUFFERED` | `1` (makes the logs appear right away) |

   Names must be written exactly like that (capitals, underscores, no spaces).
   These stay secret on Render; they are not in GitHub.

## Step 3: Stop the bot on your PC

Go to the window where the bot runs on your PC and press `Ctrl + C` (or close it).
See Rule n°1 above.

## Step 4: Deploy

1. Click **Deploy Web Service** at the bottom of the Render form.
2. You land on the **Logs**. After 2–5 minutes you should see:
   ```
   Loaded … pieces of club information.
   @YourBotName is running. Press Ctrl+C to stop.
   ==> Your service is live 🎉
   ```
3. Send a message to the bot on Telegram from your phone. It should answer. 🎉
4. At the top of the Render page, copy your service address. It looks like
   `https://smartclub-bot-xxxx.onrender.com`. Open it in the browser: you should read
   **Smart Club bot is running**.

Problems in the logs:
- `KeyError: 'TELEGRAM_BOT_TOKEN'` (or `GEMINI_API_KEY`): a variable name is misspelled or
  missing in **Environment** (left menu). Fix it, then **Manual Deploy** → **Deploy latest commit**.
- `Telegram rejected the token`: the token value is wrong.
- `Telegram: Conflict: terminated by other getUpdates request`: the bot is still running on
  your PC (Rule n°1). Stop it there. Seeing this once or twice right after a deploy is normal
  (the old and new copies overlap for a few seconds).

## Step 5: Keep it awake with cron-job.org

1. Go to <https://cron-job.org> → **Sign up** (free, email only), confirm your email, log in.
2. Click **Create cronjob**.
   - Title: `Smart Club bot`
   - URL: your Render address from step 4 (e.g. `https://smartclub-bot-xxxx.onrender.com`)
   - Execution schedule: **Every 10 minutes**
3. Click **Create**.
4. After 10 minutes, the cronjob's history should show **200 OK**.

Done: you can switch the PC off. The bot runs on its own.

(UptimeRobot.com, "HTTP(s)" monitor every 5 minutes, works too if you prefer.)

---

## Everyday use

- **Change the club information in the Google Sheet**: nothing else to do, the bot reloads it
  every 5 minutes.
- **Change `prompt.md` or a file in `knowledge/`**: on GitHub, open the repo → click the
  file → ✏️ pencil (Edit) → change → **Commit changes**. Render redeploys automatically
  in a few minutes. You can also do this from your phone in the browser.
- **Add a new file in `knowledge/`**: on GitHub open the `knowledge/info` folder →
  **Add file** → **Upload files** (or **Create new file**, name ending in `.md`) → **Commit changes**.
- **Change a key** (e.g. new Gemini key): Render → your service → **Environment** →
  edit → **Save, rebuild, and deploy**.
- **See what the bot is doing**: Render → your service → **Logs** (works on the phone too).

Good to know:
- Conversations are kept in memory, so they are forgotten every time the bot restarts
  (after each change, and sometimes when Render restarts it). Students just ask again.
  Paused chats (after a handoff) also resume after a restart.
- The free plan has 750 hours per month (enough for 24/7) and 5 GB of traffic per month
  (this bot uses far less). If one runs out, Render pauses the bot until the 1st of the next
  month; you get an email. Never add a card unless you want to pay.
- If the bot doesn't answer: open the Render address in the browser (this wakes it up),
  wait 1 minute, try again, then look at the **Logs**.

## Use the PC again instead of Render

1. Render → your service → **Settings** → bottom → **Suspend Web Service**.
2. Then run it on the PC as before. To go back to Render: stop the PC copy, then
   Render → **Resume Web Service**.
