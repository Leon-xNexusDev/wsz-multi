# Server für das Protestversprechen

Kleiner Node-Server ohne Framework. Speichert Zusagen in einer SQLite-Datei (sql.js, kein Kompilieren nötig), verschickt eine Bestätigungsmail und liefert die Zahlen für die Seite.

- Eine Zusage zählt erst, wenn der Link in der Bestätigungsmail angeklickt wurde (Double-Opt-in).
- Unbestätigte Zusagen werden nach 48 Stunden gelöscht.
- Jede Mail enthält einen Link, mit dem man seine Daten sofort löscht.
- Eine E-Mail-Adresse = eine Zusage. Wer die Stadt wechseln will, löscht sich über den Link und trägt sich neu ein.
- IP-Adressen werden nicht gespeichert, nur kurz und gehasht im Arbeitsspeicher für die Begrenzung (5 Versuche pro Stunde).
- Spamschutz ohne Captcha: verstecktes Feld + Begrenzung pro IP.
- Öffentlich sieht man nur Zahlen pro Stadt, nie Namen.

## Einrichten

Voraussetzung: Node 18 oder neuer.

```
cd _server
npm install --omit=dev
npm test            # 12 Tests, ohne echte Mails
```

Die Städte kommen aus `staedte.json`. Die Datei erzeugt `python3 _quellen/build.py` aus `ECHT` (nur echte Städte).

### Einstellungen (Umgebungsvariablen)

| Variable | Bedeutung | Beispiel |
|---|---|---|
| `PORT` | Port, nur lokal erreichbar | `3003` |
| `SITE_URL` | öffentliche Adresse der Seite (für Links in der Mail) | `https://wirstehenzusammen.org/` |
| `DB_FILE` | Datenbank-Datei | `/var/lib/wsz/wsz.sqlite` |
| `ADMIN_KEY` | Schlüssel für den Export, mindestens 24 Zeichen | `openssl rand -hex 24` |
| `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS`, `SMTP_SECURE` | Mailserver. Ohne `SMTP_HOST` läuft der Testmodus: Mails landen nur im Log. | `smtp.example.org`, `587`, …, `0` |
| `MAIL_FROM` | Absender | `Wir stehen zusammen <kontakt@wirstehenzusammen.org>` |
| `PENDING_HOURS` | Stunden bis unbestätigte Zusagen gelöscht werden | `48` |
| `RATE_PER_HOUR` | Zusagen pro IP und Stunde | `5` |
| `ALLOW_ORIGIN` | nur nötig, wenn Seite und Server auf verschiedenen Domains laufen | `https://wirstehenzusammen.org` |

### systemd

`/etc/systemd/system/wsz.service`:

```ini
[Unit]
Description=WSZ Protestversprechen
After=network.target

[Service]
WorkingDirectory=/var/www/wsz/_server
ExecStart=/usr/bin/node server.js
EnvironmentFile=/etc/wsz.env
Restart=on-failure
User=www-data
StateDirectory=wsz

[Install]
WantedBy=multi-user.target
```

`/etc/wsz.env` (Rechte `600`, gehört root):

```
PORT=3003
SITE_URL=https://wirstehenzusammen.org/
DB_FILE=/var/lib/wsz/wsz.sqlite
ADMIN_KEY=…
SMTP_HOST=…
SMTP_USER=…
SMTP_PASS=…
MAIL_FROM=Wir stehen zusammen <kontakt@wirstehenzusammen.org>
```

```
systemctl daemon-reload && systemctl enable --now wsz
journalctl -u wsz -f     # Log ansehen
```

### nginx

Im `server`-Block der Seite:

```nginx
location /api/ {
    proxy_pass http://127.0.0.1:3003;
    proxy_set_header X-Forwarded-For $remote_addr;
    proxy_set_header Host $host;
}
location /_server/  { deny all; }
location /_quellen/ { deny all; }
location /entwurf/  { auth_basic "Entwurf"; auth_basic_user_file /etc/nginx/wsz-entwurf.htpasswd; }
```

Wichtig: `X-Forwarded-For` auf `$remote_addr` setzen (nicht anhängen), sonst kann man die Begrenzung umgehen.

### Seite anschließen

In `_quellen/build.py` `API_URL = '/api/'` setzen und `python3 _quellen/build.py` laufen lassen. Ohne `API_URL` zeigt die öffentliche Seite „Zusagen sind bald möglich“ statt des Formulars.

## Export fürs Orga-Team

```
curl -H "Authorization: Bearer $ADMIN_KEY" https://wirstehenzusammen.org/api/export.csv -o versprechen.csv
```

Nur bestätigte Zusagen. Die CSV öffnet sich direkt in Excel/LibreOffice (Semikolon, UTF-8). Die Datei enthält Namen, Mailadressen und Arbeitgeber, also vertraulich behandeln und nicht in Chats oder Clouds teilen.

## Sicherung

Die ganze Datenbank ist eine Datei (`DB_FILE`). Zum Sichern einfach kopieren, z. B. nachts per Cron. Sicherungen genauso vertraulich behandeln wie den Export.
