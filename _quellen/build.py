#!/usr/bin/env python3
"""Baut die WSZ-Website aus _quellen/src/ in den Repo-Root.

Aufruf aus dem Repo-Root:  python3 _quellen/build.py
"""
import json, os, re, shutil, sys

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, 'src')
DIST = os.path.dirname(ROOT)
ART = os.path.join(ROOT, 'artifact')
IMG = os.path.join(SRC, 'img')

# Öffentliche Adresse der Seite – für Linkvorschauen nötig (muss absolut sein).
# Bei eigener Domain hier ändern, z. B. 'https://wirstehenzusammen.de/'
SITE_URL = 'https://leon-xnexusdev.github.io/wsz-multi/'

# Kontakt – öffentlich sichtbar, nur echte Adressen eintragen
KONTAKT_MAIL = 'kontakt@wirstehenzusammen.de'
PRESSE_MAIL = 'presse@wirstehenzusammen.de'
TELEGRAM_URL = ''   # Link zum bundesweiten Kanal, z. B. 'https://t.me/...'; leer = öffentlich ausgeblendet

# Städte, in denen es die Gruppe wirklich gibt. Nur diese erscheinen öffentlich.
ECHT = {'dresden', 'magdeburg'}

sys.path.insert(0, ROOT)
from og import make_og

# ---------- Städte ----------
# id, n, lon, lat, side: Stammdaten.  c, tp: nur Beispieldaten für den Entwurf.
# Echte Angaben (leer = öffentlich nicht angezeigt): treffpunkt, aktion, treffen, instagram, telegram, presse
CITIES = [
    dict(id='dresden', n='Dresden', lon=13.74, lat=51.05, tp='Theaterplatz', c=1840, side='r'),
    dict(id='magdeburg', n='Magdeburg', lon=11.63, lat=52.13, tp='Domplatz', c=1215, side='r'),
    dict(id='berlin', n='Berlin', lon=13.40, lat=52.52, tp='Treffpunkt folgt', c=2960, side='r'),
    dict(id='hamburg', n='Hamburg', lon=9.99, lat=53.55, tp='Treffpunkt folgt', c=2110, side='r'),
    dict(id='leipzig', n='Leipzig', lon=12.37, lat=51.34, tp='Treffpunkt folgt', c=1530, side='r'),
    dict(id='koeln', n='Köln', lon=6.96, lat=50.94, tp='Treffpunkt folgt', c=1495, side='r'),
    dict(id='muenchen', n='München', lon=11.58, lat=48.14, tp='Treffpunkt folgt', c=1380, side='r'),
    dict(id='frankfurt', n='Frankfurt', lon=8.68, lat=50.11, tp='Treffpunkt folgt', c=990, side='r'),
    dict(id='stuttgart', n='Stuttgart', lon=9.18, lat=48.78, tp='Treffpunkt folgt', c=760, side='r'),
    dict(id='hannover', n='Hannover', lon=9.73, lat=52.37, tp='Treffpunkt folgt', c=705, side='r'),
    dict(id='bremen', n='Bremen', lon=8.80, lat=53.08, tp='Treffpunkt folgt', c=540, side='l'),
    dict(id='dortmund', n='Dortmund', lon=7.47, lat=51.51, tp='Treffpunkt folgt', c=610, side='r'),
    dict(id='nuernberg', n='Nürnberg', lon=11.08, lat=49.45, tp='Treffpunkt folgt', c=480, side='r'),
    dict(id='chemnitz', n='Chemnitz', lon=12.92, lat=50.83, tp='Treffpunkt folgt', c=395, side='b'),
    dict(id='erfurt', n='Erfurt', lon=11.03, lat=50.98, tp='Treffpunkt folgt', c=360, side='l'),
    dict(id='rostock', n='Rostock', lon=12.10, lat=54.09, tp='Treffpunkt folgt', c=330, side='r'),
    dict(id='bielefeld', n='Bielefeld', lon=8.53, lat=52.02, tp='Treffpunkt folgt', c=275, side='r'),
    dict(id='mainz', n='Mainz', lon=8.27, lat=50.00, tp='Treffpunkt folgt', c=250, side='l'),
    dict(id='freiburg', n='Freiburg', lon=7.85, lat=47.99, tp='Treffpunkt folgt', c=420, side='r'),
    dict(id='goettingen', n='Göttingen', lon=9.93, lat=51.54, tp='Treffpunkt folgt', c=230, side='r'),
]
for _c in CITIES:
    _c['echt'] = _c['id'] in ECHT
    for _k in ('treffpunkt', 'aktion', 'treffen', 'instagram', 'telegram', 'presse'):
        _c.setdefault(_k, '')

DRAFT, CUR, ALPHA, TOTAL = True, [], [], 0

def set_mode(draft):
    """Entwurf: alle Städte mit Beispieldaten. Öffentlich: nur echte Städte, Zahlen ab 0, nur echte Angaben."""
    global DRAFT, CUR, ALPHA, TOTAL
    DRAFT = draft
    if draft:
        CUR = [dict(c) for c in CITIES]
    else:
        CUR = [dict(c, c=0, tp=c['treffpunkt']) for c in CITIES if c['echt']]
    ALPHA = sorted(CUR, key=lambda c: c['n'].replace('Ö', 'O').replace('ü', 'u'))
    TOTAL = sum(c['c'] for c in CUR)

def fmt(n):
    return f'{n:,}'.replace(',', '.')

NAV = [('index.html', 'Start'), ('worum-es-geht.html', 'Worum es geht'), ('staedte.html', 'Städte'),
       ('mitmachen.html', 'Mitmachen'), ('material.html', 'Material'), ('presse.html', 'Presse')]

def PH(txt, dark=False):
    return f'<span class="ph{" dark" if dark else ""}">{txt}</span>' if DRAFT else ''
MENU_ICON = '<svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"><path d="M4 7h16M4 12h16M4 17h16"/></svg>'
PLAY = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M7 4l13 8-13 8z" fill="currentColor"/></svg>'


def header(base, active):
    links = ''.join(
        f'<a href="{base}{href}"{" aria-current=\"page\"" if href == active else ""}>{label}</a>' for href, label in NAV)
    return f'''<a class="skip" href="#start">Zum Inhalt springen</a>
<header class="top">
  <div class="wrap">
    <a class="brand" href="{base}index.html" aria-label="Wir stehen zusammen – Startseite"><img src="{base}img/logo.webp" alt="" width="44" height="44"><span translate="no">#WirStehenZusammen</span></a>
    <nav class="navlinks" id="navlinks" aria-label="Hauptmenü">{links}</nav>
    <a class="btn btn-hot cta" href="{base}index.html#versprechen">Protestversprechen</a>
    <button type="button" class="menu-btn" aria-label="Menü" aria-expanded="false" aria-controls="navlinks">{MENU_ICON}<span>Menü</span></button>
  </div>
</header>'''


def footer(base):
    return f'''<footer>
  <div class="wrap">
    <span>© 2026 Wir stehen zusammen · <span class="sel" id="foot-mail">{KONTAKT_MAIL}</span> <button type="button" class="copy" data-copy="foot-mail" style="color:#fff;border-color:rgba(255,255,255,.35)">Kopieren</button> {PH("Adresse Platzhalter", True)}</span>
    <nav aria-label="Weitere Seiten"><a href="{base}material.html">Material</a><a href="{base}presse.html">Presse</a><a href="{base}impressum.html">Impressum</a><a href="{base}datenschutz.html">Datenschutz</a><button type="button" class="linkbtn" data-consent-open>Video-Einstellungen</button></nav>
  </div>
</footer>'''


def cta_band(base, text='Bist du dabei?', btn='Protestversprechen abgeben'):
    return f'''<section class="cta-band"><div class="wrap"><p>{text}</p><a class="btn btn-white" href="{base}index.html#versprechen">{btn}</a></div></section>'''


def page_head(tag, title, lead='', crumbs=''):
    return f'''<section class="page-head">
  <div class="wrap">
    {crumbs}
    {f'<span class="tag">{tag}</span>' if tag else ''}
    <h1{' class="first"' if not tag else ''}>{title}</h1>
    {f'<p class="lead">{lead}</p>' if lead else ''}
  </div>
</section>'''


def shell(title, body, base='', active='', desc='', artifact_main=False, path='index.html', og='og/start.jpg', og_title=None):
    og_title = og_title or title
    site = SITE_URL + ('entwurf/' if DRAFT else '')
    page_url = site + ('' if path == 'index.html' else path)
    head = f'''<title>{title}</title>
<meta name="description" content="{desc}">
<meta name="theme-color" content="#26326b">{chr(10) + '<meta name="robots" content="noindex, nofollow">' if DRAFT else ''}
<meta property="og:type" content="website">
<meta property="og:site_name" content="Wir stehen zusammen">
<meta property="og:locale" content="de_DE">
<meta property="og:title" content="{og_title}">
<meta property="og:description" content="{desc}">
<meta property="og:url" content="{page_url}">
<meta property="og:image" content="{site}{og}">
<meta property="og:image:type" content="image/jpeg">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="{og_title} – #WirStehenZusammen">
<meta name="twitter:card" content="summary_large_image">
<link rel="canonical" href="{page_url}">
<link rel="stylesheet" href="{base}css/wsz.css">
<link rel="icon" href="{base}img/logo.webp">'''
    bar = (f'<aside class="draftbar" aria-label="Hinweis">Entwurf für das Team: Platzhalter und Beispieldaten sind sichtbar. '
           f'<a href="{SITE_URL}{"" if path == "index.html" else path}">Öffentliche Version</a></aside>\n') if DRAFT else ''
    content = f'''{header(base, active).replace('</a>' + chr(10), '</a>' + chr(10) + bar, 1)}
<main id="start">
{body}
</main>
{footer(base)}
<div class="consent" id="consent" hidden>
  <div class="box" role="dialog" aria-labelledby="consent-h" aria-describedby="consent-p">
    <h2 id="consent-h">Videos von Vimeo laden?</h2>
    <p id="consent-p">Unser Teaser liegt bei Vimeo (USA). Wenn du zustimmst, wird er geladen und Vimeo sieht deine IP-Adresse. Ohne Zustimmung startest du das Video später selbst per Klick. <a href="{base}datenschutz.html#videos">Mehr dazu</a></p>
    <div class="acts"><button type="button" class="yes" data-consent="yes">Videos erlauben</button><button type="button" class="no" data-consent="no">Ablehnen</button></div>
  </div>
</div>
<script src="{base}js/staedte.js"></script>
<script src="{base}js/wsz.js"></script>'''
    if artifact_main:
        # Artifact-Hauptseite: Gerüst kommt vom Viewer, Basis-Pfad per Script setzen
        return (f'<title>Wir stehen zusammen</title>\n<meta name="claude:viewport-fit-sides" content="cover">\n'
                + head.split('\n', 1)[1].replace(f'<title>{title}</title>\n', '')
                + f'\n<script>document.documentElement.setAttribute("data-base","{base}");document.documentElement.lang="de";</script>\n'
                + content)
    return f'''<!doctype html>
<html lang="de" data-base="{base}"{" data-entwurf" if DRAFT else ""}>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
{head}
</head>
<body>
{content}
</body>
</html>
'''

# ---------- Seiten ----------

def p_index(base=''):
    body = f'''<section class="hero">
  <div class="photo" style="background-image:url('{base}img/demo-blockade.jpg')">
    <div class="bgslot" data-vimeo-bg="909677587" aria-hidden="true"></div>
    <a class="vid-cta" href="{base}worum-es-geht.html#teaser">{PLAY}Teaser mit Ton</a>
    {PH("Übergangs-Video", True).replace('class="ph dark"', 'class="ph dark vid-ph"')}
  </div>
  <div class="bars">
    <div class="bar bar-1"><div class="wrap"><h1>Wir stehen zusammen.</h1></div></div>
    <div class="bar bar-2"><div class="wrap"><span class="big">SOZIALSTAAT<br>VERTEIDIGEN.</span></div></div>
  </div>
  <div class="wrap below on-dark">
    <div class="logo"><img src="{base}img/logo.webp" alt="Logo Wir stehen zusammen" width="220" height="220" fetchpriority="high"></div>
    <div><p class="lead">Die Angriffe auf den Sozialstaat spitzen sich zu. Wir bringen Aktivist*innen und Kolleg*innen bundesweit zusammen und verbinden Streiks mit Protest.</p></div>
  </div>
</section>

<section class="pledge" id="versprechen">
  <div class="wrap">
    <div class="p-head">
      <div>
        <span class="tag hot">Protestversprechen</span>
        <h2 style="margin-top:14px">Wo bist du dabei?</h2>
        <p class="p-intro">Such deine Stadt und sag zu. Die Zahlen sind für alle sichtbar, Namen nie.</p>
      </div>
      <div class="total" data-zero-hide{" hidden" if TOTAL == 0 else ""}>
        <b data-count="total">{fmt(TOTAL)}</b>
        <span>Versprechen<br>bundesweit</span>
        {PH("Beispielzahlen", True)}
      </div>
    </div>
    <div class="p-grid">
      <div class="mapcol">
        <svg class="demap" id="map" viewBox="0 0 520 680" role="group" aria-label="Deutschlandkarte mit allen Städten, in denen wir aktiv sind"></svg>
        <div class="maplegend">
          <span><i class="sq own"></i>Städte, in denen wir aktiv sind</span>
          {PH("Orte symbolisch", True)}
        </div>
      </div>
      <div class="listcol">
        <label class="search" for="city-search">
          <svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="11" cy="11" r="7"/><path d="M20 20l-4-4"/></svg>
          <input id="city-search" type="search" placeholder="Stadt oder Treffpunkt suchen…" autocomplete="off">
        </label>
        <p class="rank-head">Sortiert nach Zusagen.</p>
        <ol class="cities" id="cities"></ol>
        <button type="button" class="more" id="more">Alle Städte anzeigen</button>
        <p class="missing">Deine Stadt fehlt? <a href="{base}mitmachen.html#gruenden">Dann gründe eine Gruppe.</a></p>
      </div>
    </div>
    <p class="p-quote">„Wenn der Sozialstaat angegriffen wird, gehe ich mit auf die Straße. Wir stehen zusammen.“ {PH("Wortlaut Platzhalter", True)}</p>
  </div>
</section>

<section class="section">
  <div class="wrap">
    <div class="sec-head"><h2>Mehr zur Kampagne</h2></div>
    <div class="guide">
      <a href="{base}worum-es-geht.html"><h3>Worum es geht</h3><p>Milliarden sollen gekürzt werden. Warum Protest allein nicht reicht und was unser Plan ist.</p></a>
      <a href="{base}mitmachen.html"><h3>Mitmachen</h3><p>Komm zum ersten Treffen oder gründe eine Gruppe in deiner Stadt.</p></a>
      <a href="{base}material.html"><h3>Material</h3><p>Flyer, Logo und Sharepics zum Ausdrucken und Teilen.</p></a>
    </div>
  </div>
</section>

<section class="closer" style="background-image:url('{base}img/demo-verdi.jpg')">
  <div class="band"><div class="wrap"><span class="hash" translate="no">#WirStehenZusammen</span><a class="btn btn-hot" href="#versprechen">Werde Teil der Protestbewegung</a></div></div>
</section>'''
    return body


def p_worum(base=''):
    return f'''{page_head("", "Worum es geht", "Warum wir uns organisieren und wie wir Druck machen wollen.")}

<section class="situation" aria-labelledby="es-reicht">
  <div class="wrap stack">
    <div class="box">
      <p>Milliarden sollen gekürzt werden. Gleichzeitig sollen wir länger arbeiten und noch mehr Kosten selbst tragen.</p>
      <p>Wer den Sozialstaat abbaut, schafft Unsicherheit und stärkt den Nährboden für die Hetze von Faschist*innen. Die Antwort der AfD auf den Sozialabbau ist Spaltung.</p>
    </div>
    <h2 class="head" id="es-reicht">ES REICHT!</h2>
    <div class="box">
      <p>In vielen Städten sind wir schon mit Tausenden gegen Sozialabbau auf die Straße gegangen. Dieser Widerstand wächst.</p>
      <p><span class="hl">Aber Protest allein reicht nicht.</span> Wir müssen raus aus der Bubble, rein in Kieze und Betriebe. Die Beschäftigten haben den entscheidenden Hebel: Mit Streiks können sie ganze Bereiche lahmlegen.</p>
    </div>
  </div>
</section>

<section class="plan" id="plan">
  <div class="wrap">
    <div class="head">
      <div><span class="tag hot">Unser Plan</span><h2 style="margin-top:14px">STREIKS mit Protest verbinden.</h2></div>
      <p>Gute Daseinsvorsorge und faire Arbeitsbedingungen gehen uns alle an. Unter dem Motto #WirStehenZusammen bauen wir eine Protestkaskade auf, die in die Tarifrunden mündet.</p>
    </div>
    <div class="steps">
      <article class="step"><span class="when">Herbst 2026</span><h3>Protestkaskade</h3><p>Demos und Aktionen in vielen Städten, eine nach der anderen. {PH("Termine folgen")}</p></article>
      <article class="step"><span class="when">Laufend</span><h3>Tarifrunde Charité</h3><p>Kolleg*innen kämpfen dort für bessere Löhne <strong>und</strong> gegen Kürzungen im Gesundheitswesen. Der Ausgang prägt die Krankenhäuser bundesweit.</p></article>
      <article class="step"><span class="when">2027</span><h3>Tarifrunde öffentlicher Dienst</h3><p><strong>2,5 Millionen Beschäftigte.</strong> Wenn wir ihre Streiks mit Protest gegen Sozialabbau verbinden, entsteht richtig Druck.</p></article>
    </div>
  </div>
</section>

<section class="teaser" id="teaser" aria-labelledby="teaser-h" style="padding-bottom:72px">
  <div class="wrap">
    <div class="t-head"><h2 id="teaser-h">Teaser</h2></div>
    <div class="player" data-vimeo="909677587" style="background-image:url('{base}img/demo-verdi.jpg')"><button type="button" class="vplay"><span class="pbtn"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 4l14 8-14 8z" fill="#fff"/></svg></span><b>Video abspielen</b><small>Mit dem Klick lädst du das Video von Vimeo. Dabei werden Daten an Vimeo (USA) übertragen.</small></button></div>
    <p class="t-note">{PH("Übergangs-Video")} Bis unser eigener Teaser fertig ist, zeigen wir hier „Wir fahren zusammen – Wir streiken zusammen“. Video über <a href="https://vimeo.com/909677587">Vimeo</a>.</p>
  </div>
</section>

{cta_band(base)}'''


def meet_html(base):
    cards = []
    if DRAFT:
        cards.append(f'''<div class="card on-dark">
        <span class="tag" style="justify-self:start">Erstes Treffen</span>
        <p class="when">[Datum, Zeit, Ort]</p>
        <p>Komm zum ersten Treffen, Sozialratschlag oder Stammtisch in deiner Stadt. Die Termine stehen auf den <a href="{base}staedte.html" style="color:#fff">Stadtseiten</a>.</p>
        {PH("Platzhalter", True).replace('">', '" style="justify-self:start">', 1)}
      </div>''')
    if DRAFT or TELEGRAM_URL:
        cards.append(f'''<div class="card berry on-dark" id="telegram">
        <span class="tag navy" style="justify-self:start">Telegram</span>
        <p class="when">Bundesweiter Kanal</p>
        <p>Termine und Aufrufe direkt aufs Handy.</p>
        <a class="btn btn-navy" href="{TELEGRAM_URL or '#telegram'}" style="justify-self:start">Kanal beitreten</a>
        {PH("Link aus QR-Code eintragen", True).replace('">', '" style="justify-self:start">', 1)}
      </div>''')
    return f'<div class="meet">{"".join(cards)}</div>' if cards else ''


def p_mitmachen(base=''):
    return f'''{page_head("", "Dafür braucht es DICH!", "Ein breites Bündnis aus Gewerkschaften, Linkspartei und zivilgesellschaftlichen Initiativen entsteht nicht von allein. Pack mit an.")}

<section class="you" style="background:var(--bg)">
  <div class="wrap">
    <h2 class="sr-only">So machst du mit</h2>
    <div class="ways" style="margin-top:0">
      <div class="way"><span class="kicker">Im Betrieb</span><h3>Mit Kolleg*innen reden</h3><p>Im Krankenhaus, in der Stadtreinigung, in der Kita: Gespräche sind der erste Schritt zum Streik.</p></div>
      <div class="way"><span class="kicker">Im Kiez</span><h3>Nachbarschaft mobilisieren</h3><p>Flyer verteilen, Infostände machen, Leute zu den Aktionen holen. <a href="{base}material.html">Material gibt's hier.</a></p></div>
      <div class="way"><span class="kicker">In der Stadt</span><h3>Bündnis aufbauen</h3><p>Gewerkschaften, Initiativen und Vereine vor Ort an einen Tisch holen.</p></div>
    </div>
    {meet_html(base)}
  </div>
</section>

<section class="section" id="gruenden" style="padding-top:0">
  <div class="wrap">
    <div class="sec-head"><h2>Deine Stadt fehlt noch?</h2><p>So kommt sie auf die Karte:</p></div>
    <ol class="steps3">
      <li><h3>Schreib uns</h3><p>Kurze Mail an <span class="sel" id="grp-mail">{KONTAKT_MAIL}</span> mit Stadt und wie wir dich erreichen. <button type="button" class="copy" data-copy="grp-mail">Kopieren</button></p></li>
      <li><h3>Wir vernetzen euch</h3><p>Wir bringen dich mit Leuten aus deiner Stadt zusammen, die schon zugesagt haben, und mit Gewerkschafter*innen vor Ort.</p></li>
      <li><h3>Erstes Treffen</h3><p>Ihr ladet zum ersten Treffen ein. Eure Stadt bekommt eine eigene Seite mit Treffpunkt, Terminen und Kanälen.</p></li>
    </ol>
    <p style="margin-top:14px">{PH("Ablauf mit Team abstimmen")}</p>
  </div>
</section>

{cta_band(base)}'''


def p_staedte(base=''):
    cards = ''.join(
        f'<a href="{base}staedte/{c["id"]}.html"><b>{c["n"]}</b><span class="n" data-zero-hide{" hidden" if not c["c"] else ""}><span data-count="{c["id"]}">{fmt(c["c"])}</span><span>Zusagen</span></span><small>{c["tp"]}</small></a>'
        for c in ALPHA)
    return f'''{page_head("", "Städte", f"In {len(CUR)} {'Stadt' if len(CUR) == 1 else 'Städten'} gibt es schon Gruppen. Jede hat eine eigene Seite.")}

<section class="section">
  <div class="wrap overview">
    <div class="mapcard on-dark">
      <svg class="demap" data-map="all" viewBox="0 0 520 680" role="group" aria-label="Deutschlandkarte, Städte führen zur jeweiligen Stadtseite"></svg>
      <div class="maplegend"><span><i class="sq own"></i>Tipp auf eine Stadt, um ihre Seite zu öffnen</span>{PH("Orte symbolisch", True)}</div>
    </div>
    <div style="display:grid;gap:16px;min-width:0">
      <div class="city-cards">{cards}</div>
      <p class="missing" style="color:var(--muted)">Deine Stadt fehlt? <a href="{base}mitmachen.html#gruenden" style="color:var(--ink)">Gründe eine Gruppe.</a></p>
    </div>
  </div>
</section>

{cta_band(base)}'''


def city_rows(c):
    rows = []
    def row(dt, dd): rows.append(f'<div><dt>{dt}</dt><dd>{dd}</dd></div>')
    if c['aktion']: row('Nächste Aktion', c['aktion'])
    elif DRAFT: row('Nächste Aktion', f'[Datum, Zeit] {PH("Platzhalter")}')
    if c['tp']: row('Treffpunkt', c['tp'])
    if c['treffen']: row('Offenes Treffen', c['treffen'])
    elif DRAFT: row('Offenes Treffen', f'[Wochentag, Uhrzeit, Ort] {PH("Platzhalter")}')
    links = []
    if c['instagram']: links.append(f'<a href="https://instagram.com/{c["instagram"].lstrip("@")}">Instagram {c["instagram"]}</a>')
    if c['telegram']: links.append(f'<a href="{c["telegram"]}">Telegram</a>')
    if links: row('Kanäle', f'<span class="chips-l">{"".join(links)}</span>')
    elif DRAFT: row('Kanäle', f'<span class="chips-l"><a href="#kanal">Instagram @wsz_{c["id"]}</a><a href="#kanal">Telegram</a></span> {PH("Links folgen")}')
    row('Teilen', f'<div class="share" data-share-city="{c["id"]}"></div>')
    mail = c['presse'] or (f'presse-{c["id"]}@wirstehenzusammen.de' if DRAFT else '')
    if mail: row('Presse', f'<span class="sel" id="press-{c["id"]}">{mail}</span> <button type="button" class="copy" data-copy="press-{c["id"]}">Kopieren</button> {"" if c["presse"] else PH("Beispieladresse")}')
    return '\n        '.join(rows)


def p_city(c, base='../'):
    crumbs = f'<p class="crumbs"><a href="{base}staedte.html">Städte</a><span aria-hidden="true">/</span><span>{c["n"]}</span></p>'
    others = ''.join(f'<a href="{o["id"]}.html">{o["n"]}</a>' for o in ALPHA if o['id'] != c['id'])
    return f'''<section class="page-head">
  <div class="wrap">
    {crumbs}
    <h1 class="first">{c["n"]}</h1>
    <div class="city-stats" data-zero-hide{" hidden" if not c["c"] else ""}>
      <div><div class="big" data-count="{c["id"]}">{fmt(c["c"])}</div></div>
      <div class="lbl">Zusagen<br>aus {c["n"]}</div>
      {PH("Beispielzahl", True)}
    </div>
  </div>
</section>

<section class="section">
  <div class="wrap city-main">
    <div style="min-width:0">
      <dl class="infolist" style="margin:0">
        {city_rows(c)}
      </dl>
      <div class="minimap"><svg class="demap" data-map="focus" data-focus="{c["id"]}" viewBox="0 0 520 680" role="img" aria-label="Lage von {c["n"]} auf der Deutschlandkarte"></svg></div>
    </div>
    <div class="pledge-card on-dark">
      <span class="tag hot" style="justify-self:start">Protestversprechen</span>
      <h2>Bist du in {c["n"]} dabei?</h2>
      <div id="city-pledge" data-city="{c["id"]}"></div>
    </div>
  </div>
</section>

<section class="section">
  <div class="wrap">
    <div class="sec-head"><h2 style="font-size:clamp(22px,2.6vw,28px)">Andere Städte</h2></div>
    <div class="other-cities">{others}</div>
  </div>
</section>'''


def mat_if(fn):
    return '' if (DRAFT or os.path.exists(os.path.join(REPO, 'material', fn))) else '<!--weg-->'

def mat_end():
    return '<!--/weg-->'


def p_material(base=''):
    return f'''{page_head("", "Material", "Zum Ausdrucken und Teilen. Nehmt euch, was ihr braucht.")}

<section class="section">
  <div class="wrap">
    <h2 class="sr-only">Downloads</h2>
    <div class="mats" style="margin-top:0">
      {mat_if("WSZ_Flyer.pdf")}<article class="mat">
        <div class="thumb">#WirStehen&shy;Zusammen</div>
        <div>
          <h3>Kampagnen-Flyer</h3>
          <p>A4, Vorder- und Rückseite. Kopiervorlage mit Feld für euren lokalen Termin und QR-Code zum Telegram-Kanal.</p>
          <div class="acts"><a class="btn btn-navy" href="{"../" if DRAFT else ""}{base}material/WSZ_Flyer.pdf">PDF öffnen</a>{PH("Datei auf Server ablegen")}</div>
        </div>
      </article>{mat_end()}
      {mat_if("WSZ_Logo_Sharepics.zip")}<article class="mat">
        <div class="thumb berry logo-thumb"><img src="{base}img/logo.webp" alt="" width="150" height="150" loading="lazy"></div>
        <div>
          <h3>Logo &amp; Sharepics</h3>
          <p>Das Kampagnenlogo als PNG und Vorlagen für Instagram-Posts und Storys. Einfach euren Ort und Termin eintragen und teilen.</p>
          <div class="acts"><a class="btn btn-navy" href="{"../" if DRAFT else ""}{base}material/WSZ_Logo_Sharepics.zip">Paket öffnen</a>{PH("Sharepics folgen")}</div>
        </div>
      </article>{mat_end()}
      <article class="mat">
        <div class="thumb" style="background:var(--hot)">Teaser</div>
        <div>
          <h3>Teaser-Video</h3>
          <p>Der Kampagnen-Teaser zum Teilen, im Querformat und als Hochkant-Schnitt für Reels und Storys.</p>
          <div class="acts"><a class="btn btn-navy" href="{base}worum-es-geht.html#teaser">Ansehen</a>{PH("Download folgt")}</div>
        </div>
      </article>
    </div>
  </div>
</section>

{cta_band(base)}'''


def p_presse(base=''):
    rows = ''.join(
        f'<tr><td><a href="{base}staedte/{c["id"]}.html">{c["n"]}</a></td><td><span class="sel">{c["presse"] or "presse-" + c["id"] + "@wirstehenzusammen.de"}</span></td></tr>'
        for c in ALPHA if c['presse'] or DRAFT)
    return f'''{page_head("", "Presse", "Anfragen bitte per E-Mail." + (" Für Berichte aus einer bestimmten Stadt meldet euch direkt bei der Gruppe dort." if rows else ""))}

<section class="section">
  <div class="wrap">
    <h2 class="sr-only">Kontakt</h2>
    <div class="press-grid">
      <div class="pcard">
        <h3>Bundesweit</h3>
        {"<p>[Name, Funktion] " + PH("Platzhalter") + "</p>" if DRAFT else ""}
        <p><span class="sel" id="press-main">{PRESSE_MAIL}</span> <button type="button" class="copy" data-copy="press-main">Kopieren</button></p>
        {"<p>Telefon: [Nummer] " + PH("Platzhalter") + "</p>" if DRAFT else ""}
      </div>
      <!--entwurf--><div class="pcard">
        <h3>Pressemitteilungen und Fotos</h3>
        <p>Fotos von unseren Aktionen sind honorarfrei, mit Bildnachweis.</p>
        <p>{PH("Folgt")}</p>
      </div><!--/entwurf-->
    </div>
  </div>
</section>

{"" if rows else "<!--weg-->"}<section class="section">
  <div class="wrap">
    <div class="sec-head"><h2>Pressekontakte vor Ort</h2><p>{PH("Beispieladressen")}</p></div>
    <div class="tbl-wrap"><table class="contacts"><thead><tr><th>Stadt</th><th>E-Mail</th></tr></thead><tbody>{rows}</tbody></table></div>
  </div>
</section>{"" if rows else "<!--/weg-->"}'''


def p_impressum(base=''):
    return f'''{page_head("", "Impressum")}
<section class="section"><div class="wrap prose">
  <!--entwurf--><div class="todo"><p><strong>Platzhalter.</strong> Wird ausgefüllt, sobald die rechtliche Trägerschaft geklärt ist (Katja klärt mit Pascal, IGM).</p></div><!--/entwurf-->
  <h2>Angaben gemäß § 5 DDG</h2>
  <p>[Name der Organisation bzw. verantwortlichen Person]<br>[Straße, Hausnummer]<br>[PLZ, Ort]</p>
  <h3>Vertreten durch</h3><p>[Name]</p>
  <h3>Kontakt</h3><p>E-Mail: {KONTAKT_MAIL}<br>Telefon: [Nummer]</p>
  <h2>Verantwortlich für den Inhalt nach § 18 Abs. 2 MStV</h2>
  <p>[Name, Anschrift]</p>
  <h2>Haftung für Links</h2>
  <p>Unsere Seiten verlinken auf Angebote lokaler Gruppen und Dritter. Für deren Inhalte sind die jeweiligen Anbieter verantwortlich. {PH("Text prüfen lassen")}</p>
</div></section>'''


def p_datenschutz(base=''):
    return f'''{page_head("", "Datenschutz")}
<section class="section"><div class="wrap prose">
  <!--entwurf--><div class="todo"><p><strong>Platzhalter.</strong> Gliederung der Datenschutzerklärung. Der endgültige Text muss rechtlich geprüft werden, bevor das Versprechen-Formular live geht.</p></div><!--/entwurf-->
  <h2>1. Verantwortliche Stelle</h2><p>[Name, Anschrift, E-Mail]</p>
  <h2>2. Hosting</h2><p>Die Website liegt auf einem eigenen Server bei [Anbieter, Standort Deutschland/EU]. Beim Aufruf werden technisch notwendige Daten (IP-Adresse, Zeitpunkt, aufgerufene Seite) in Server-Logs verarbeitet. [Speicherdauer]</p>
  <h2>3. Schriften</h2><p>Alle Schriften liegen auf unserem eigenen Server. Es wird keine Verbindung zu Google oder anderen Schrift-Anbietern aufgebaut.</p>
  <h2 id="videos">4. Eingebettete Videos (Vimeo)</h2><p>Auf der Startseite und auf „Worum es geht“ zeigen wir ein Video von Vimeo (Vimeo.com Inc., USA). Es wird erst geladen, wenn du im Hinweis „Videos erlauben“ wählst oder auf „Video abspielen“ klickst. Erst dann wird eine Verbindung zu Vimeo hergestellt und deine IP-Adresse übertragen. Wir nutzen den Modus „Do Not Track“. Rechtsgrundlage ist deine Einwilligung (Art. 6 Abs. 1 lit. a DSGVO, § 25 Abs. 1 TDDDG). Deine Auswahl speichern wir nur in deinem Browser. Du kannst sie jederzeit über „Video-Einstellungen“ unten auf jeder Seite ändern. {PH("Rechtlich prüfen")}</p>
  <h2>5. Protestversprechen</h2>
  <p>Wenn du ein Versprechen abgibst, verarbeiten wir:</p>
  <ul><li>Name und E-Mail-Adresse</li><li>gewählte Stadt</li><li>Bereich im öffentlichen Dienst (TVöD) und optional deinen Betrieb</li></ul>
  <p>Zweck: dich zu Aktionen in deiner Stadt und deinem Bereich zu informieren und die Zahl der Zusagen pro Stadt anzuzeigen. Angezeigt wird nur die Anzahl, nie Namen.</p>
  <p>Rechtsgrundlage: deine Einwilligung. Weil die Angaben Rückschlüsse auf politische Haltung und gewerkschaftliches Engagement zulassen können, ist zu prüfen, ob eine ausdrückliche Einwilligung nach Art. 9 Abs. 2 lit. a DSGVO nötig ist. {PH("Rechtlich prüfen")}</p>
  <p>Speicherdauer: [z. B. bis zum Ende der Kampagne oder bis zum Widerruf]</p>
  <p>Weitergabe: keine Weitergabe an Dritte. [Ggf. an die lokale Gruppe deiner Stadt – klären]</p>
  <h2>6. Kontakt per E-Mail</h2><p>[Zweck, Rechtsgrundlage, Speicherdauer]</p>
  <h2>7. Deine Rechte</h2><p>Auskunft, Berichtigung, Löschung, Einschränkung, Datenübertragbarkeit, Widerruf der Einwilligung und Beschwerde bei einer Aufsichtsbehörde. Schreib dafür an [E-Mail].</p>
</div></section>'''

# ---------- Build ----------

REPO = DIST

def clean(html):
    """Öffentlich: nur-Entwurf-Blöcke und weggelassene Abschnitte entfernen."""
    if DRAFT:
        return html.replace('<!--entwurf-->', '').replace('<!--/entwurf-->', '').replace('<!--weg-->', '').replace('<!--/weg-->', '')
    html = re.sub(r'<!--entwurf-->.*?<!--/entwurf-->', '', html, flags=re.S)
    html = re.sub(r'<!--weg-->.*?<!--/weg-->', '', html, flags=re.S)
    return html


def build_one(dest, draft):
    set_mode(draft)
    for sub in ('staedte', 'og'):
        shutil.rmtree(os.path.join(dest, sub), ignore_errors=True)
    for sub in ('staedte', 'css', 'js', 'img', 'fonts', 'og'):
        os.makedirs(os.path.join(dest, sub), exist_ok=True)
    for fn in os.listdir(os.path.join(SRC, 'fonts')):
        if fn.endswith('.woff2'):
            shutil.copy(os.path.join(SRC, 'fonts', fn), os.path.join(dest, 'fonts', fn))
    css = open(os.path.join(SRC, 'base.css')).read() + open(os.path.join(SRC, 'pages.css')).read()
    js = open(os.path.join(SRC, 'wsz.js')).read()
    if not draft:
        js = re.sub(r"\n *else if\(DRAFT\)h\+=[^\n]*", '', js)   # Entwurfs-Zweig raus
    note = 'Entwurf: alle Städte mit Beispieldaten.' if draft else 'Öffentlich: nur echte Städte (ECHT in _quellen/build.py), Zahlen ab 0.'
    data = f'/* Städte – {note} */\nwindow.WSZ_CITIES=' + json.dumps(CUR, ensure_ascii=False) + ';\n'
    imgs = {'logo.webp': 'logo.webp', 'demo-blockade.jpg': 'crowd2.jpg', 'demo-verdi.jpg': 'crowd1.jpg'}
    pages = [
        ('index.html', 'Wir stehen zusammen', 'index.html', p_index, 'Bundesweite Kampagne: Streiks mit Protest gegen Sozialabbau verbinden. Gib dein Protestversprechen ab.'),
        ('worum-es-geht.html', 'Worum es geht · Wir stehen zusammen', 'worum-es-geht.html', p_worum, 'Warum wir uns organisieren und wie wir Druck gegen Sozialabbau aufbauen.'),
        ('mitmachen.html', 'Mitmachen · Wir stehen zusammen', 'mitmachen.html', p_mitmachen, 'Im Betrieb, im Kiez, im Bündnis: So machst du bei Wir stehen zusammen mit.'),
        ('staedte.html', 'Städte · Wir stehen zusammen', 'staedte.html', p_staedte, 'Alle Städte, in denen Wir stehen zusammen aktiv ist.'),
        ('material.html', 'Material · Wir stehen zusammen', 'material.html', p_material, 'Flyer, Logo, Sharepics und Teaser zum Weitergeben.'),
        ('presse.html', 'Presse · Wir stehen zusammen', 'presse.html', p_presse, 'Pressekontakte bundesweit und vor Ort.'),
        ('impressum.html', 'Impressum · Wir stehen zusammen', '', p_impressum, 'Impressum'),
        ('datenschutz.html', 'Datenschutz · Wir stehen zusammen', '', p_datenschutz, 'Datenschutzerklärung'),
    ]
    open(os.path.join(dest, 'css', 'wsz.css'), 'w').write(css)
    open(os.path.join(dest, 'js', 'wsz.js'), 'w').write(js)
    open(os.path.join(dest, 'js', 'staedte.js'), 'w').write(data)
    for dst, srcname in imgs.items():
        shutil.copy(os.path.join(IMG, srcname), os.path.join(dest, 'img', dst))
    make_og(os.path.join(dest, 'og', 'start.jpg'), 'Wir stehen zusammen.', 'SOZIALSTAAT VERTEIDIGEN.', 'Gib dein Protestversprechen ab')
    for fn, title, active, fnc, desc in pages:
        open(os.path.join(dest, fn), 'w').write(clean(shell(title, fnc(''), '', active, desc, path=fn)))
    for c in CUR:
        make_og(os.path.join(dest, 'og', c['id'] + '.jpg'), f'{c["n"]} steht zusammen.', 'BIST DU DABEI?', 'Jetzt zusagen')
        out = shell(f'{c["n"]} · Wir stehen zusammen', p_city(c, '../'), '../', 'staedte.html',
                    f'Wir stehen zusammen in {c["n"]}: Treffpunkt, Termine und Protestversprechen. Bist du dabei?',
                    path=f'staedte/{c["id"]}.html', og=f'og/{c["id"]}.jpg', og_title=f'{c["n"]} steht zusammen. Bist du dabei?')
        open(os.path.join(dest, 'staedte', c['id'] + '.html'), 'w').write(clean(out))
    print('Entwurf ' if draft else 'Öffentlich', '->', os.path.relpath(dest, DIST) if dest != DIST else '.', '|', len(CUR), 'Städte')


def build():
    build_one(DIST, False)
    build_one(os.path.join(DIST, 'entwurf'), True)

if __name__ == '__main__':
    build()
