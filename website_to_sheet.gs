/**
 * Smart Club: copies the text of the club's website into the "Site web" tab of the Google Sheet,
 * so the Telegram bot always has the latest version (PythonAnywhere's free plan can't reach the site).
 *
 * Setup (once): in the Google Sheet, Extensions > Apps Script, paste this file, run updateWebsite,
 * then add an hourly trigger. See WEBSITE.md.
 */
const SITE = 'https://ensemsmartclub.netlify.app';
const PAGES = ['/', '/about', '/what-we-do', '/projects', '/join'];
const TAB = 'Site web';

function updateWebsite() {
  const rows = [['Sujet', 'Information', 'Lien', 'Actif']];
  PAGES.forEach(function (path) {
    const url = SITE + path;
    try {
      const res = UrlFetchApp.fetch(url, {muteHttpExceptions: true, followRedirects: true});
      if (res.getResponseCode() !== 200) {
        console.log(url + ': HTTP ' + res.getResponseCode());
        return;
      }
      const html = res.getContentText('UTF-8');
      const title = (html.match(/<title[^>]*>([\s\S]*?)<\/title>/i) || [null, path])[1];
      rows.push(['Site web : ' + decode_(title).trim(), textOf_(html).slice(0, 45000), url, 'oui']);
    } catch (e) {
      console.log(url + ': ' + e);
    }
  });
  if (rows.length === 1) return;  // site unreachable: keep the previous copy

  const ss = SpreadsheetApp.getActive();
  const sheet = ss.getSheetByName(TAB) || ss.insertSheet(TAB);
  sheet.clearContents();
  sheet.getRange(1, 1, rows.length, 4).setValues(rows);
  console.log((rows.length - 1) + ' pages copied. WEBSITE_CSV_URL=https://docs.google.com/spreadsheets/d/' +
              ss.getId() + '/export?format=csv&gid=' + sheet.getSheetId());
}

// The visible text of a page, without menus, scripts and styles.
function textOf_(html) {
  const text = html
    .replace(/<(script|style|noscript|svg|nav|header|footer)[\s\S]*?<\/\1>/gi, ' ')
    .replace(/<\/(p|div|section|article|li|h[1-6]|br|tr)>|<br\s*\/?>/gi, '\n')
    .replace(/<[^>]+>/g, ' ');
  return decode_(text)
    .split('\n')
    .map(function (line) { return line.replace(/\s+/g, ' ').trim(); })
    .filter(function (line) { return line; })
    .join('\n');
}

function decode_(text) {
  return text
    .replace(/&nbsp;/g, ' ').replace(/&amp;/g, '&').replace(/&lt;/g, '<').replace(/&gt;/g, '>')
    .replace(/&quot;/g, '"').replace(/&#39;|&apos;|&rsquo;/g, "'")
    .replace(/&#(\d+);/g, function (m, n) { return String.fromCharCode(Number(n)); });
}
