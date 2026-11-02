# „Kommt bald“-Seite

Eine einzige Datei (`index.html`), Logo und Schriften stecken drin, keine Verbindung nach außen.
Vor dem Einsatz unten in der Datei Impressum und Kontaktadresse eintragen.

## Als Startseite, solange die Seite noch nicht live ist (nginx)

```nginx
server {
    server_name wirstehenzusammen.org www.wirstehenzusammen.org;
    root /var/www/wsz/_wartung;
    location / { try_files /index.html =404; }
}
```

## Als Wartungsseite bei laufendem Betrieb

Mit Status 503, damit Suchmaschinen wissen, dass es nur kurz ist:

```nginx
# im server-Block der Seite
error_page 503 /_wartung/index.html;
location = /_wartung/index.html { internal; root /var/www/wsz; }
location / {
    if (-f /var/www/wsz/WARTUNG) { return 503; }
    try_files $uri $uri/ =404;
}
```

Wartung an: `touch /var/www/wsz/WARTUNG` · aus: `rm /var/www/wsz/WARTUNG`
