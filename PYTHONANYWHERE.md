# Put the bot online 24/7 on PythonAnywhere (free, no credit card)

Use this if Render asks you for a credit card.

How it works: the bot becomes a small website, `https://<your-username>.pythonanywhere.com`.
Telegram sends every student message to that site (a "webhook") and the site answers.
Nothing needs to run all the time, so the free plan is enough, and there is no cron job to set up.

Files used: `webapp.py` (the website) and `set_webhook.py` (gives Telegram the address).

---

## Step 1: Create the account

1. Go to <https://www.pythonanywhere.com> → **Pricing & signup** → **Create a Beginner account** (free).
2. Choose a username. It will be in the bot's address (`username.pythonanywhere.com`).
3. Confirm your email.

## Step 2: Get the code from GitHub

PythonAnywhere downloads the code from GitHub. The easiest way is to make the repo public. That is
safe here: the keys (`.env`) are not on GitHub, only the code and the club's public information.

1. On GitHub, open `smartclub-bot` → **Settings** → bottom (**Danger Zone**) → **Change visibility**
   → **Public**.
2. On PythonAnywhere, open the **Consoles** tab → **Bash**. A black window opens. Type these lines
   one by one (press Enter after each):
   ```
   git clone https://github.com/Gh1taa/smartclub-bot.git
   cd smartclub-bot
   pip3.11 install --user -r requirements.txt
   ```
   The last one takes a few minutes.

## Step 3: Add your keys

1. **Files** tab → open the `smartclub-bot` folder.
2. In "Enter new file name", type `.env` → **New file**.
3. Open `.env` on your PC with Notepad, copy everything, paste it in the PythonAnywhere editor → **Save**.

## Step 4: Create the website

1. **Web** tab → **Add a new web app** → **Next** → **Manual configuration** → **Python 3.11** → **Next**.
2. In the **Code** section, click the link next to **WSGI configuration file**
   (it ends in `_wsgi.py`).
3. Delete everything in that file and paste this instead. Replace `USERNAME` with your
   PythonAnywhere username:
   ```python
   import sys
   sys.path.insert(0, "/home/USERNAME/smartclub-bot")
   from webapp import application
   ```
4. **Save**, go back to the **Web** tab and click the green **Reload** button.
5. Open `https://USERNAME.pythonanywhere.com` in your browser: you should read
   **Smart Club bot is running**.

## Step 5: Switch Telegram to the website

⚠️ Stop the bot on your PC first (close its black window). From now on Telegram sends the messages
to the website, so the PC version can't receive any.

In the Bash console (Consoles tab, the one from step 2):
```
cd ~/smartclub-bot
python3.11 set_webhook.py
```
You should see `{'ok': True, 'result': True, 'description': 'Webhook was set'}`.

Send a message to the bot on Telegram. It should answer. 🎉 You can switch off your PC.
The first answer can take a little longer: the bot loads the club's information.

---

## Everyday use

- **Google Sheet**: nothing to do, the bot reloads it (at most every 5 minutes, on the next message).
- **Change `prompt.md` or `knowledge/`**: edit the file on GitHub (✏️ → **Commit changes**), then on
  PythonAnywhere: Bash console → `cd ~/smartclub-bot` → `git pull`, then **Web** tab → **Reload**.
- **Change a key**: **Files** tab → `smartclub-bot/.env` → edit → **Save** → **Web** tab → **Reload**.
- **See what the bot is doing**: **Web** tab → **Log files** → **Server log** (messages in and out)
  and **Error log** (problems).
- **Keep it on** ⚠️: free websites are switched off after 3 months unless you click
  **Run until 3 months from today** in the **Web** tab. PythonAnywhere emails you before that.
  Put a reminder in your calendar.

Good to know:
- Students are answered one at a time. If several write at the same moment, the others wait a few
  seconds.
- Conversations are kept in memory: they are forgotten when the site reloads. Students just ask again.

## Use the PC again instead

On the PC, in the `telegram-simple` folder:
```
.venv\Scripts\python set_webhook.py --delete
```
then start `start_bot.bat`. To go back to PythonAnywhere: close the PC bot, then run
`python3.11 set_webhook.py` again in the PythonAnywhere Bash console.
