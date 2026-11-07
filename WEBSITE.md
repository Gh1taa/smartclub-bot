# Keep the bot up to date with the website

A small script inside the Google Sheet copies the text of the club's website into a tab named
**Site web**, every hour. The bot reads that tab like the rest of the Sheet, so a change on the
website reaches the bot within about an hour, with nothing to restart.

Why a script in the Sheet: PythonAnywhere's free plan can only reach a list of allowed sites.
Google is on it, the club's website is not.

Pages copied: home, about, what-we-do, projects, join (list at the top of `website_to_sheet.gs`).
The project list on the Projects page is loaded by JavaScript from a database, so only that page's
fixed text is copied.

## Setup (once, about 5 minutes)

1. Open the club's Google Sheet → **Extensions** → **Apps Script**.
2. Delete what is in the editor, paste the whole content of `website_to_sheet.gs`, click 💾 **Save**.
3. At the top, choose the function **updateWebsite** and click **▶ Run**.
   Google asks for permission the first time: **Review permissions** → choose your account →
   **Advanced** → **Go to … (unsafe)** → **Allow**. (It is your own script; the warning is normal.)
4. At the bottom, the **Execution log** shows a line like:
   `5 pages copied. WEBSITE_CSV_URL=https://docs.google.com/spreadsheets/d/.../export?format=csv&gid=...`
   Copy everything after `WEBSITE_CSV_URL=`.
5. Make it run every hour: left menu ⏰ **Triggers** → **+ Add Trigger** →
   function `updateWebsite`, event source **Time-driven**, **Hour timer**, **Every hour** → **Save**.
6. Add the link to `.env`, on the PC and on PythonAnywhere (**Files** → `smartclub-bot/.env`):
   ```
   WEBSITE_CSV_URL=<the link from step 4>
   ```
   On PythonAnywhere: `git pull` in the Bash console, then **Web** → **Reload**.

Check: the Sheet now has a **Site web** tab with one row per page.

## Good to know

- Don't edit the **Site web** tab by hand: the script replaces it every hour. Add your own
  information in the first tab as usual.
- If the website is down, the script keeps the previous copy.
- New page on the website: add its path to `PAGES` at the top of the script, then **Save**.
