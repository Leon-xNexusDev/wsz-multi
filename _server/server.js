'use strict';
/*
 * WSZ – Server für das Protestversprechen
 *
 * Endpunkte (hinter dem Webserver unter /api/ erreichbar):
 *   POST /api/versprechen      Zusage annehmen, Bestätigungsmail senden
 *   GET  /api/bestaetigen?t=…  Link aus der Mail: Zusage bestätigen, weiter zur Stadtseite
 *   GET  /api/abmelden?t=…     Link aus der Mail: Daten löschen
 *   GET  /api/zahlen           bestätigte Zusagen pro Stadt (öffentlich, ohne Namen)
 *   GET  /api/export.csv       bestätigte Zusagen fürs Orga-Team (Header: Authorization: Bearer ADMIN_KEY)
 *
 * Gespeichert wird nur, was das Formular abfragt. IP-Adressen werden nicht gespeichert,
 * nur kurz und gehasht im Arbeitsspeicher für die Begrenzung pro Stunde.
 */
const http = require('http');
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const initSqlJs = require('sql.js');

// ---------- Einstellungen (Umgebungsvariablen) ----------
const env = (k, d) => (process.env[k] !== undefined && process.env[k] !== '' ? process.env[k] : d);
const PORT = Number(env('PORT', 3003));
const HOST = env('HOST', '127.0.0.1');
const SITE_URL = env('SITE_URL', 'http://localhost:8000/').replace(/\/?$/, '/');
const DB_FILE = env('DB_FILE', path.join(__dirname, 'data', 'wsz.sqlite'));
const ADMIN_KEY = env('ADMIN_KEY', '');
const ALLOW_ORIGIN = env('ALLOW_ORIGIN', '');          // nur nötig, wenn Seite und API auf verschiedenen Domains liegen
const PENDING_HOURS = Number(env('PENDING_HOURS', 48)); // unbestätigte Zusagen werden danach gelöscht
const RATE_PER_HOUR = Number(env('RATE_PER_HOUR', 5));
const TRUST_PROXY = env('TRUST_PROXY', '1') === '1';
const MAIL = {
  host: env('SMTP_HOST', ''), port: Number(env('SMTP_PORT', 587)), secure: env('SMTP_SECURE', '0') === '1',
  user: env('SMTP_USER', ''), pass: env('SMTP_PASS', ''), from: env('MAIL_FROM', 'Wir stehen zusammen <kontakt@wirstehenzusammen.org>'),
};

const TVOED = ['Krankenhaus (TVöD-K)', 'Pflege- und Betreuungseinrichtung (TVöD-B)', 'Kita / Sozial- und Erziehungsdienst (TVöD SuE)',
  'Kommunalverwaltung (TVöD-V)', 'Entsorgung / Stadtreinigung (TVöD-E)', 'Sparkasse (TVöD-S)', 'Flughafen (TVöD-F)',
  'Bundesverwaltung (TVöD Bund)', 'Ausbildung im öffentlichen Dienst (TVAöD)', 'Anderer Tarifvertrag (z. B. TV-L, TV-N, TV-V)',
  'Nicht im öffentlichen Dienst / weiß nicht'];

// Städte kommen aus dem Build (nur echte Städte, siehe _quellen/build.py → ECHT)
const CITIES = JSON.parse(fs.readFileSync(path.join(__dirname, 'staedte.json'), 'utf8'));
const CITY = Object.fromEntries(CITIES.map(c => [c.id, c.n]));

// ---------- Datenbank ----------
let db;
let saveTimer = null;
function flush() {
  clearTimeout(saveTimer); saveTimer = null;
  fs.mkdirSync(path.dirname(DB_FILE), { recursive: true });
  const tmp = DB_FILE + '.tmp';
  fs.writeFileSync(tmp, Buffer.from(db.export()));
  fs.renameSync(tmp, DB_FILE);
}
function save() {
  // kurz bündeln, aber spätestens nach 200 ms schreiben (kein endloses Verschieben)
  if (!saveTimer) saveTimer = setTimeout(flush, 200);
}
// Beim Beenden (Neustart, Update) ungespeicherte Änderungen sichern
for (const sig of ['SIGTERM', 'SIGINT']) process.on(sig, () => { try { if (db && saveTimer) flush(); } finally { process.exit(0); } });
function run(sql, p = []) { db.run(sql, p); save(); }
function all(sql, p = []) {
  const st = db.prepare(sql); st.bind(p); const out = [];
  while (st.step()) out.push(st.getAsObject());
  st.free(); return out;
}
function one(sql, p = []) { return all(sql, p)[0] || null; }

async function openDb() {
  const SQL = await initSqlJs();
  db = fs.existsSync(DB_FILE) ? new SQL.Database(fs.readFileSync(DB_FILE)) : new SQL.Database();
  db.run(`CREATE TABLE IF NOT EXISTS versprechen (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    stadt TEXT NOT NULL, name TEXT NOT NULL, email TEXT NOT NULL,
    tvoed TEXT NOT NULL, betrieb TEXT NOT NULL DEFAULT '',
    token TEXT NOT NULL UNIQUE,
    erstellt TEXT NOT NULL, bestaetigt TEXT
  )`);
  db.run('CREATE UNIQUE INDEX IF NOT EXISTS email_eindeutig ON versprechen(email)');
  save();
}
function cleanup() {
  const grenze = new Date(Date.now() - PENDING_HOURS * 3600e3).toISOString();
  run('DELETE FROM versprechen WHERE bestaetigt IS NULL AND erstellt < ?', [grenze]);
}

// ---------- Mail ----------
let transport = null;
function mailer() {
  if (!MAIL.host) return null;
  if (!transport) {
    const nodemailer = require('nodemailer');
    transport = nodemailer.createTransport({ host: MAIL.host, port: MAIL.port, secure: MAIL.secure,
      auth: MAIL.user ? { user: MAIL.user, pass: MAIL.pass } : undefined });
  }
  return transport;
}
const API_URL = () => SITE_URL + 'api/';
async function sendConfirm(v) {
  const ok = `${API_URL()}bestaetigen?t=${v.token}`;
  const off = `${API_URL()}abmelden?t=${v.token}`;
  const stadt = CITY[v.stadt] || v.stadt;
  const text = `Hallo ${v.name},

danke für dein Protestversprechen für ${stadt}. Bitte bestätige es mit diesem Link:

${ok}

Erst dann zählt deine Zusage. Wenn du dich nicht eingetragen hast, ignorier diese Mail einfach. Unbestätigte Angaben löschen wir nach ${PENDING_HOURS} Stunden.

Du willst nicht mehr dabei sein? Hier löschst du deine Angaben jederzeit:
${off}

#WirStehenZusammen
${SITE_URL}`;
  const t = mailer();
  if (!t) { console.log(`[Mail-Testmodus] an ${v.email}\n${text}\n`); return; }
  await t.sendMail({ from: MAIL.from, to: v.email, subject: `Bitte bestätigen: dein Protestversprechen für ${stadt}`, text });
}

// ---------- Hilfen ----------
const hits = new Map();   // gehashte IP -> [Zeitpunkte]
function limited(ip) {
  const k = crypto.createHash('sha256').update(ip + (process.env.RATE_SALT || 'wsz')).digest('hex').slice(0, 16);
  const now = Date.now(), list = (hits.get(k) || []).filter(t => now - t < 3600e3);
  list.push(now); hits.set(k, list);
  return list.length > RATE_PER_HOUR;
}
setInterval(() => { const now = Date.now(); for (const [k, l] of hits) if (!l.some(t => now - t < 3600e3)) hits.delete(k); }, 600e3).unref();

function clientIp(req) {
  if (TRUST_PROXY && req.headers['x-forwarded-for']) return String(req.headers['x-forwarded-for']).split(',')[0].trim();
  return req.socket.remoteAddress || '';
}
function send(res, status, body, headers = {}) {
  const isStr = typeof body === 'string';
  res.writeHead(status, Object.assign({
    'Content-Type': isStr ? 'text/html; charset=utf-8' : 'application/json; charset=utf-8',
    'Cache-Control': 'no-store', 'X-Content-Type-Options': 'nosniff', 'Referrer-Policy': 'no-referrer',
  }, ALLOW_ORIGIN ? { 'Access-Control-Allow-Origin': ALLOW_ORIGIN, 'Vary': 'Origin' } : {}, headers));
  res.end(isStr ? body : JSON.stringify(body));
}
function readJson(req, max = 8192) {
  return new Promise((resolve, reject) => {
    let size = 0; const chunks = [];
    req.on('data', c => { size += c.length; if (size > max) { reject(new Error('zu groß')); req.destroy(); } else chunks.push(c); });
    req.on('end', () => { try { resolve(JSON.parse(Buffer.concat(chunks).toString('utf8') || '{}')); } catch (e) { reject(e); } });
    req.on('error', reject);
  });
}
const clean = (s, n) => String(s == null ? '' : s).replace(/[\u0000-\u001f\u007f]/g, ' ').trim().slice(0, n);
const page = (title, msg) => `<!doctype html><html lang="de"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex"><title>${title}</title>
<style>body{margin:0;font-family:system-ui,sans-serif;background:#26326b;color:#fff;display:grid;place-items:center;min-height:100vh;padding:24px;box-sizing:border-box}main{max-width:34rem}h1{font-size:28px;margin:0 0 12px}a{color:#fff;font-weight:700}</style></head>
<body><main><h1>${title}</h1><p>${msg}</p><p><a href="${SITE_URL}">Zur Startseite</a></p></main></body></html>`;

let zahlenCache = { t: 0, body: null };
function zahlen() {
  if (Date.now() - zahlenCache.t < 15e3 && zahlenCache.body) return zahlenCache.body;
  const rows = all('SELECT stadt, COUNT(*) AS n FROM versprechen WHERE bestaetigt IS NOT NULL GROUP BY stadt');
  const staedte = Object.fromEntries(CITIES.map(c => [c.id, 0]));
  let gesamt = 0;
  for (const r of rows) if (r.stadt in staedte) { staedte[r.stadt] = r.n; gesamt += r.n; }
  zahlenCache = { t: Date.now(), body: { gesamt, staedte } };
  return zahlenCache.body;
}
const csv = v => `"${String(v == null ? '' : v).replace(/"/g, '""').replace(/^[=+\-@\t\r]/, "'$&")}"`;

// ---------- Routen ----------
async function handle(req, res) {
  const url = new URL(req.url, 'http://x');
  const p = url.pathname.replace(/^\/api/, '') || '/';

  if (req.method === 'OPTIONS') return send(res, 204, '', { 'Access-Control-Allow-Methods': 'GET, POST', 'Access-Control-Allow-Headers': 'Content-Type' });

  if (req.method === 'GET' && p === '/zahlen') return send(res, 200, zahlen(), { 'Cache-Control': 'public, max-age=15' });

  if (req.method === 'POST' && p === '/versprechen') {
    if (limited(clientIp(req))) return send(res, 429, { fehler: 'Zu viele Versuche. Bitte versuch es in einer Stunde nochmal.' });
    let b; try { b = await readJson(req); } catch { return send(res, 400, { fehler: 'Ungültige Anfrage.' }); }
    if (clean(b.website, 200)) return send(res, 200, { status: 'gesendet' });   // Honigtopf: Bots bekommen „ok“, gespeichert wird nichts
    const v = { stadt: clean(b.stadt, 40), name: clean(b.name, 80), email: clean(b.email, 160).toLowerCase(),
      tvoed: clean(b.tvoed, 80), betrieb: clean(b.betrieb, 120) };
    if (!CITY[v.stadt]) return send(res, 400, { fehler: 'Diese Stadt gibt es bei uns noch nicht.' });
    if (!v.name) return send(res, 400, { fehler: 'Bitte gib deinen Namen ein.', feld: 'name' });
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(v.email)) return send(res, 400, { fehler: 'Bitte gib eine gültige E-Mail-Adresse ein.', feld: 'mail' });
    if (!TVOED.includes(v.tvoed)) return send(res, 400, { fehler: 'Bitte wähl aus, wo du angestellt bist.', feld: 'tvoed' });
    if (b.einwilligung !== true) return send(res, 400, { fehler: 'Bitte bestätige die Einwilligung.', feld: 'ok' });

    const vorhanden = one('SELECT * FROM versprechen WHERE email = ?', [v.email]);
    if (vorhanden && vorhanden.bestaetigt) {
      // Schon bestätigt: nichts ändern (sonst könnte jemand fremde Einträge umschreiben).
      // Wer die Stadt wechseln will, löscht sich über den Link in der Mail und trägt sich neu ein.
      // Die Antwort ist dieselbe wie sonst, damit niemand prüfen kann, ob eine Adresse schon eingetragen ist.
      return send(res, 200, { status: 'gesendet' });
    }
    v.token = crypto.randomBytes(24).toString('hex');
    const jetzt = new Date().toISOString();
    if (vorhanden) run('UPDATE versprechen SET stadt=?, name=?, tvoed=?, betrieb=?, token=?, erstellt=? WHERE id=?',
      [v.stadt, v.name, v.tvoed, v.betrieb, v.token, jetzt, vorhanden.id]);
    else run('INSERT INTO versprechen (stadt,name,email,tvoed,betrieb,token,erstellt) VALUES (?,?,?,?,?,?,?)',
      [v.stadt, v.name, v.email, v.tvoed, v.betrieb, v.token, jetzt]);
    try { await sendConfirm(v); } catch (e) {
      console.error('Mail fehlgeschlagen:', e.message);
      return send(res, 502, { fehler: 'Die Bestätigungsmail konnte nicht verschickt werden. Bitte versuch es später nochmal.' });
    }
    return send(res, 200, { status: 'gesendet' });
  }

  if (req.method === 'GET' && p === '/bestaetigen') {
    const t = clean(url.searchParams.get('t'), 64);
    const v = t && one('SELECT * FROM versprechen WHERE token = ?', [t]);
    if (!v) return send(res, 404, page('Link ungültig', 'Dieser Bestätigungslink ist abgelaufen oder wurde schon benutzt. Du kannst dein Versprechen einfach nochmal abgeben.'));
    if (!v.bestaetigt) { run('UPDATE versprechen SET bestaetigt = ? WHERE id = ?', [new Date().toISOString(), v.id]); zahlenCache.t = 0; }
    return send(res, 302, '', { Location: `${SITE_URL}staedte/${v.stadt}.html?bestaetigt=1` });
  }

  if (req.method === 'GET' && p === '/abmelden') {
    const t = clean(url.searchParams.get('t'), 64);
    const v = t && one('SELECT id FROM versprechen WHERE token = ?', [t]);
    if (v) { run('DELETE FROM versprechen WHERE id = ?', [v.id]); zahlenCache.t = 0; }
    return send(res, 200, page('Gelöscht', 'Deine Angaben sind gelöscht. Wir schreiben dir nicht mehr.'));
  }

  if (req.method === 'GET' && p === '/export.csv') {
    const auth = String(req.headers.authorization || '');
    const ok = ADMIN_KEY.length >= 24 && auth.length === ('Bearer ' + ADMIN_KEY).length &&
      crypto.timingSafeEqual(Buffer.from(auth), Buffer.from('Bearer ' + ADMIN_KEY));
    if (!ok) return send(res, 401, { fehler: 'Nicht berechtigt.' });
    const rows = all('SELECT stadt, name, email, tvoed, betrieb, bestaetigt FROM versprechen WHERE bestaetigt IS NOT NULL ORDER BY stadt, bestaetigt');
    const body = '﻿' + ['stadt;name;email;tvoed;betrieb;bestaetigt'].concat(
      rows.map(r => [CITY[r.stadt] || r.stadt, r.name, r.email, r.tvoed, r.betrieb, r.bestaetigt].map(csv).join(';'))).join('\r\n');
    return send(res, 200, body, { 'Content-Type': 'text/csv; charset=utf-8', 'Content-Disposition': 'attachment; filename="versprechen.csv"' });
  }

  return send(res, 404, { fehler: 'Nicht gefunden.' });
}

openDb().then(() => {
  cleanup(); setInterval(cleanup, 3600e3).unref();
  http.createServer((req, res) => handle(req, res).catch(e => { console.error(e); send(res, 500, { fehler: 'Serverfehler.' }); }))
    .listen(PORT, HOST, () => console.log(`WSZ-Server läuft auf http://${HOST}:${PORT} (Mail: ${MAIL.host ? MAIL.host : 'Testmodus, Links im Log'})`));
});
