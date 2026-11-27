/**
 * PlotArt · Gmail → Studio Commercial (migration 0031). Runs in the founder's own Google account (script.google.com).
 *
 * What it does: every 10 minutes it sends the messages in threads labelled "PlotArt Lead" to PlotArt Studio, which records
 * each message once on the lead for that thread or sender (creating the lead when there is none). The thread is then
 * relabelled "PlotArt Lead/In Studio", so later replies in that thread are picked up on the next run as long as the thread
 * keeps either label. Nothing is sent to anyone; Gmail itself is not changed except for the two labels.
 *
 * Setup (once, about five minutes):
 *   1. script.google.com → New project → paste this file.
 *   2. Project Settings → Script properties: STUDIO_URL = https://plotart-enquiry.<account>.workers.dev/v1/lead-capture
 *      and LEAD_CAPTURE_TOKEN = the token set as the Worker secret (never put it in this file).
 *   3. Run setup() once and allow access to Gmail. It creates the labels and the 10-minute trigger.
 *   4. In Gmail, label a reply "PlotArt Lead" (or add a filter that labels replies to your outreach subjects).
 */
const LABEL = 'PlotArt Lead', DONE = 'PlotArt Lead/In Studio', BATCH = 40, BODY_MAX = 6000;

function setup() {
  GmailApp.getUserLabelByName(LABEL) || GmailApp.createLabel(LABEL);
  GmailApp.getUserLabelByName(DONE) || GmailApp.createLabel(DONE);
  ScriptApp.getProjectTriggers().filter(t => t.getHandlerFunction() === 'sync').forEach(t => ScriptApp.deleteTrigger(t));
  ScriptApp.newTrigger('sync').timeBased().everyMinutes(10).create();
  sync();
}

function sync() {
  const props = PropertiesService.getScriptProperties(), url = props.getProperty('STUDIO_URL'), token = props.getProperty('LEAD_CAPTURE_TOKEN');
  if (!url || !token) throw new Error('Set STUDIO_URL and LEAD_CAPTURE_TOKEN in Script properties');
  const sent = PropertiesService.getUserProperties();   // message ids already accepted by Studio (Studio also refuses duplicates)
  const done = GmailApp.getUserLabelByName(DONE) || GmailApp.createLabel(DONE);
  const threads = GmailApp.search(`label:"${LABEL}" OR (label:"${DONE}" newer_than:30d)`, 0, 50);
  let batch = [], tagged = [];
  const flush = () => {
    if (!batch.length) return;
    const r = UrlFetchApp.fetch(url, { method: 'post', contentType: 'application/json', muteHttpExceptions: true,
      headers: { Authorization: 'Bearer ' + token }, payload: JSON.stringify({ messages: batch }) });
    if (r.getResponseCode() !== 200) throw new Error('Studio refused the batch: ' + r.getResponseCode() + ' ' + r.getContentText().slice(0, 200));
    batch.forEach(m => sent.setProperty('m_' + m.message_id, '1'));
    batch = [];
  };
  threads.forEach(th => {
    th.getMessages().forEach(m => {
      const id = m.getId();
      if (sent.getProperty('m_' + id) || m.isDraft()) return;
      const from = m.getFrom(), mine = /@plotnua\.ie>?$/i.test(from);
      batch.push({ message_id: id, thread_id: th.getId(), date: m.getDate().toISOString(), from: from, to: m.getTo(),
        subject: m.getSubject(), direction: mine ? 'out' : 'in', body: stripQuoted(m.getPlainBody()).slice(0, BODY_MAX) });
      if (batch.length >= BATCH) flush();
    });
    tagged.push(th);
  });
  flush();
  tagged.forEach(th => { th.addLabel(done); const l = GmailApp.getUserLabelByName(LABEL); if (l) th.removeLabel(l); });
}

/* Keep only the new part of a reply: drop the quoted history ("On … wrote:" and lines starting with ">"). */
function stripQuoted(text) {
  const lines = String(text || '').split(/\r?\n/), out = [];
  for (const line of lines) {
    if (/^On .+wrote:\s*$/.test(line) || /^-{2,}\s*Original Message\s*-{2,}/i.test(line) || /^From: .+/.test(line) && out.length > 3) break;
    if (/^\s*>/.test(line)) continue;
    out.push(line);
  }
  return out.join('\n').trim();
}
