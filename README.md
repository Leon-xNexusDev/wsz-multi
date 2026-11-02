# Wir stehen zusammen – Website

Mehrseitige Kampagnenseite für #WirStehenZusammen. Der Repo-Root ist die fertige Seite und kann direkt ins Webroot (oder GitHub Pages).

## Seiten
- `index.html` – Start: Teaser-Schleife, Protestversprechen mit Karte und Rangliste
- `worum-es-geht.html` – „Es reicht!“, Plan, Teaser mit Ton
- `staedte.html` und `staedte/<stadt>.html` – Übersicht und eine Seite pro Stadt
- `mitmachen.html`, `material.html`, `presse.html`
- `impressum.html`, `datenschutz.html` – Gliederung, rechtlich noch zu klären

## Bearbeiten
Quellen liegen in `_quellen/`. Nach Änderungen aus dem Repo-Root:

```
python3 _quellen/build.py
```

**Neue Stadt:** Eintrag in der Liste `CITIES` in `_quellen/build.py` ergänzen und das Script laufen lassen. Stadtseite, Kartenpunkt, Übersicht und Pressetabelle entstehen automatisch.

## Noch offen
- Teaser: übergangsweise ist „Wir fahren zusammen – Wir streiken zusammen“ von Vimeo eingebettet (oben stumm als Hintergrund, unten mit Ton). Eigenes Video später per Vimeo-ID tauschen (`909677587`)
- `material/WSZ_Flyer.pdf` und `material/WSZ_Logo_Sharepics.zip`
- Telegram-Link eintragen
- Alle Zahlen, Treffpunkte und Kontakte sind Beispieldaten

## Linkvorschau & Teilen
- Vorschaubilder (1200 × 630, JPEG unter 300 KB) liegen in `og/`: `start.jpg` für alle Seiten, dazu eins pro Stadt. Sie werden von `_quellen/og.py` beim Build erzeugt.
- **Wichtig bei eigener Domain:** `SITE_URL` oben in `_quellen/build.py` ändern und neu bauen. WhatsApp & Co. brauchen absolute Adressen für die Vorschaubilder.
- Nach einer Zusage und auf jeder Stadtseite gibt es Teilen-Buttons (WhatsApp, Telegram, Link kopieren, auf dem Handy zusätzlich „Teilen…“ für Instagram, Signal usw.).

## Schriften
League Spartan (wie im Flyer) und Figtree liegen in `fonts/` (OFL-Lizenz). Es gibt keine Verbindung zu Google Fonts.

## Öffentlich und Entwurf
Der Build erzeugt zwei Fassungen:
- **Repo-Root = öffentlich.** Nur echte Angaben: Städte aus `ECHT`, Zusagen ab 0 (Zahl erscheint erst ab 1), keine Platzhalter, keine Beispieladressen. Leere Felder werden einfach weggelassen.
- **`entwurf/` = für das Team.** Alle Städte mit Beispieldaten und Platzhalter-Markierungen, gelbe Leiste oben, für Suchmaschinen gesperrt (`noindex`).

Echte Angaben trägst du oben in `_quellen/build.py` ein:
- `ECHT` – Städte, in denen es die Gruppe wirklich gibt
- pro Stadt: `treffpunkt`, `aktion`, `treffen`, `instagram`, `telegram`, `presse`
- `TELEGRAM_URL`, `KONTAKT_MAIL`, `PRESSE_MAIL`
- Material erscheint öffentlich, sobald die Datei in `material/` liegt.

## Server für das Protestversprechen
Liegt in `_server/` (Node, ohne Framework). Anleitung zum Einrichten, Mail, nginx und Export: [`_server/README.md`](_server/README.md).
Solange `API_URL` in `_quellen/build.py` leer ist (z. B. auf GitHub Pages), zeigt die öffentliche Seite „Zusagen sind bald möglich“. Der Entwurf simuliert Zusagen im eigenen Browser.
