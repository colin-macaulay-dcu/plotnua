/* PlotArt · outgoing email (Phase 3). MAILER = 'resend' (production, once approved: RESEND_API_KEY secret, sending
   domain verified), 'none' (nothing sent; the artist sees enquiries in Studio), or 'capture' (local tests only). */
export async function send(env, { to, replyTo, subject, text }) {
  const mode = env.MAILER || 'none';
  if (mode === 'none') return { sent: false, detail: 'no mailer configured' };
  if (mode === 'capture') {
    if (env.ENVIRONMENT !== 'local') throw new Error('mail capture is for local tests only');
    await env.DB.prepare('INSERT INTO mail_capture (at, to_addr, reply_to, subject, body) VALUES (?,?,?,?,?)').bind(new Date().toISOString(), to, replyTo || null, subject, text).run();
    return { sent: true, detail: 'captured' };
  }
  if (mode === 'resend') {
    const r = await fetch('https://api.resend.com/emails', { method: 'POST', headers: { Authorization: `Bearer ${env.RESEND_API_KEY}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ from: env.MAIL_FROM, to: [to], reply_to: replyTo ? [replyTo] : undefined, subject, text }) });
    return r.ok ? { sent: true, detail: 'sent' } : { sent: false, detail: `mailer ${r.status}` };
  }
  throw new Error('unknown MAILER');
}
