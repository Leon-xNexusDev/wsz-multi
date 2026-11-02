'use strict';
/* Testet den Server ohne echte Mails:  npm test  */
const { spawn } = require('child_process');
const fs = require('fs'), os = require('os'), path = require('path'), assert = require('assert');

const PORT = 3999, BASE = `http://127.0.0.1:${PORT}/api/`;
const DB = path.join(fs.mkdtempSync(path.join(os.tmpdir(), 'wsz-')), 'test.sqlite');
const KEY = 'test-admin-schluessel-1234567890';
let log = '';

function start() {
  const p = spawn(process.execPath, [path.join(__dirname, 'server.js')], {
    env: Object.assign({}, process.env, { PORT, DB_FILE: DB, ADMIN_KEY: KEY, SITE_URL: 'https://example.org/', RATE_PER_HOUR: '6', SMTP_HOST: '' }),
  });
  p.stdout.on('data', d => { log += d; }); p.stderr.on('data', d => { log += d; });
  return new Promise(r => { const t = setInterval(() => { if (log.includes('läuft')) { clearInterval(t); r(p); } }, 50); });
}
const post = (b, ip = '1.1.1.1') => fetch(BASE + 'versprechen', { method: 'POST', headers: { 'Content-Type': 'application/json', 'X-Forwarded-For': ip }, body: JSON.stringify(b) });
const ok = { stadt: 'dresden', name: 'Alex Schmidt', email: 'Alex@Example.org', tvoed: 'Krankenhaus (TVöD-K)', betrieb: 'Uniklinik', einwilligung: true };
const tokenFor = mail => { const m = [...log.matchAll(/an (\S+)\n[\s\S]*?bestaetigen\?t=([0-9a-f]{48})/g)].filter(x => x[1] === mail).pop(); return m && m[2]; };

(async () => {
  const srv = await start();
  let n = 0; const t = async (name, fn) => { await fn(); n++; console.log('  ✓', name); };
  try {
    await t('Zahlen am Anfang 0', async () => { const z = await (await fetch(BASE + 'zahlen')).json(); assert.equal(z.gesamt, 0); assert.equal(z.staedte.dresden, 0); });
    await t('Pflichtfelder werden geprüft', async () => {
      for (const [k, v, feld] of [['name', '', 'name'], ['email', 'kein-mail', 'mail'], ['tvoed', 'Quatsch', 'tvoed'], ['einwilligung', false, 'ok']]) {
        const r = await post(Object.assign({}, ok, { [k]: v }), '9.9.9.' + k.length); assert.equal(r.status, 400); assert.equal((await r.json()).feld, feld);
      }
    });
    await t('Unbekannte Stadt abgelehnt', async () => { assert.equal((await post(Object.assign({}, ok, { stadt: 'berlin' }), '8.8.8.8')).status, 400); });
    await t('Honigtopf: Bot bekommt ok, nichts gespeichert', async () => {
      const r = await post(Object.assign({}, ok, { email: 'bot@x.org', website: 'http://spam' }), '7.7.7.7'); assert.equal(r.status, 200);
      assert.ok(!log.includes('an bot@x.org'));
    });
    await t('Zusage → Mail, zählt erst nach Bestätigung', async () => {
      assert.equal((await post(ok)).status, 200);
      const tok = tokenFor('alex@example.org'); assert.ok(tok, 'Bestätigungslink im Log');
      assert.equal((await (await fetch(BASE + 'zahlen')).json()).gesamt, 0);
      const r = await fetch(BASE + 'bestaetigen?t=' + tok, { redirect: 'manual' });
      assert.equal(r.status, 302); assert.equal(r.headers.get('location'), 'https://example.org/staedte/dresden.html?bestaetigt=1');
      await new Promise(r => setTimeout(r, 50));
      const z = await (await fetch(BASE + 'zahlen')).json(); assert.equal(z.gesamt, 1); assert.equal(z.staedte.dresden, 1);
    });
    await t('Bestätigte Adresse lässt sich nicht von außen umschreiben', async () => {
      const vorher = log.length;
      assert.equal((await post(Object.assign({}, ok, { stadt: 'magdeburg', name: 'Fremd' }), '2.2.2.2')).status, 200);
      assert.ok(!log.slice(vorher).includes('an alex@example.org'), 'keine neue Mail');
      const csv = await (await fetch(BASE + 'export.csv', { headers: { Authorization: 'Bearer ' + KEY } })).text();
      assert.ok(csv.includes('"Dresden";"Alex Schmidt"'), 'Eintrag unverändert');
    });
    await t('Export nur mit Schlüssel', async () => {
      assert.equal((await fetch(BASE + 'export.csv')).status, 401);
      assert.equal((await fetch(BASE + 'export.csv', { headers: { Authorization: 'Bearer falsch' } })).status, 401);
      const r = await fetch(BASE + 'export.csv', { headers: { Authorization: 'Bearer ' + KEY } });
      assert.equal(r.status, 200); const buf = Buffer.from(await r.arrayBuffer());
      assert.ok(buf.slice(0, 3).equals(Buffer.from([0xef, 0xbb, 0xbf])), 'BOM für Excel'); assert.ok(buf.toString('utf8').includes('stadt;name;email'));
    });
    await t('CSV entschärft Formeln', async () => {
      await post(Object.assign({}, ok, { email: 'f@x.org', name: '=HYPERLINK("x")' }), '3.3.3.3');
      await fetch(BASE + 'bestaetigen?t=' + tokenFor('f@x.org'), { redirect: 'manual' });
      const csv = await (await fetch(BASE + 'export.csv', { headers: { Authorization: 'Bearer ' + KEY } })).text();
      assert.ok(csv.includes(`"'=HYPERLINK(""x"")"`));
    });
    await t('Abmelden löscht', async () => {
      await new Promise(r => setTimeout(r, 20));
      const r = await fetch(BASE + 'abmelden?t=' + tokenFor('alex@example.org')); assert.equal(r.status, 200);
      await new Promise(r => setTimeout(r, 50));
      assert.equal((await (await fetch(BASE + 'zahlen')).json()).staedte.dresden, 1);   // f@x.org bleibt
      const csv = await (await fetch(BASE + 'export.csv', { headers: { Authorization: 'Bearer ' + KEY } })).text();
      assert.ok(!csv.includes('alex@example.org'));
    });
    await t('Ungültiger Link', async () => { assert.equal((await fetch(BASE + 'bestaetigen?t=abc')).status, 404); });
    await t('Begrenzung pro IP', async () => {
      let last; for (let i = 0; i < 8; i++) last = await post(Object.assign({}, ok, { email: `r${i}@x.org` }), '5.5.5.5');
      assert.equal(last.status, 429);
    });
    await t('Daten bleiben nach Neustart erhalten', async () => {
      srv.kill('SIGTERM'); await new Promise(r => srv.on('exit', r)); log = '';
      const s2 = await start();
      try { assert.equal((await (await fetch(BASE + 'zahlen')).json()).staedte.dresden, 1); } finally { s2.kill(); }
    });
    console.log(`\n${n} Tests bestanden`);
  } catch (e) {
    console.error('\n✗', e.message, '\n--- Server-Log ---\n' + log.slice(-1500)); process.exitCode = 1;
  } finally { srv.kill(); }
})();
