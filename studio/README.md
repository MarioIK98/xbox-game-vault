# 🎮 Game Vault Studio V1.0 – eigenständige Webseiten-Werkstatt

## Öffnen
Die gesamte Anwendung steckt in [studio.html](./studio.html). Im Web-Browser funktioniert der Direktaufruf als Vorschau über den vom Commit fixierten externen HTML-Renderer (raw.githack.com). **Nicht** die alte `index.html` auf `main` verwenden.

## Funktion
- **144 anfragbare Spiele / 8 Plattformen**, gespeist aus dem geschützten öffentlichen Game Vault V4 vom 25.10.2026. 3 gesperrte Inventarpositionen werden nicht zu verkaufbaren Titeln umdeklariert.
- Aussehen, Farben, Texte, Suchmaschineninformationen und öffentlicher Kontaktweg per Formular.
- **Einzelpreis nur nach Datenträger-, Edition-, Zustands- und Quellenprüfung mit ausdrücklicher Freigabe**; bis dahin stets »Preis auf Anfrage«. 58 ältere PAL-Vergleiche bleiben informative Marktvergleiche.
- Drei vorbereitete Partnerflächen, keine Casino-Referral-Links oder automatische Werbeumleitung. Variatec-Unternehmenswerbung nur als noch zu genehmigender Entwurf.
- Vollständige Original-Funktion zur Plattform-Gesamtauswahl, Einzelspielwahl, Mischpaketen und Merkliste bleibt im erzeugten Katalog.
- Browserinterne Live-Vorschau und Prüfbericht.
- Ein Klick exportiert eine ZIP mit **14 Dateien** unter `oeffentlich/`: `index.html`, acht Plattformseiten, JPG-Vorschaubild, Sitemap, robots.txt, LIESMICH und JSON-Prüfprotokoll.
- Projekt-Sicherung als JSON / Wiederherstellung nur nach bestätigtem Import.

## Sicherheit
- Diese Anwendung speichert Entwürfe lokal im Browser; sie ruft keine fremden Daten ab und fragt keine Passwörter/GitHub-Tokens ab.
- **Kein Auto-Deploy:** Das ZIP wird erzeugt, aber keine Datei auf dem öffentlichen GitHub-`main` veröffentlicht oder ersetzt. Live-Schalten, Anbieterkennzeichnung und Jugendschutz werden separat geklärt.
- Der Online-Test des externen Vorschaulinks und die tatsächliche Bedienung auf Marios Android-Gerät stehen noch aus; lokale Chromium-Tests sind kein echter Android-Gerätetest.
- Kein Versprechen auf SEO-Ranking, rechtliche Freigabe oder autonome eBay-Preisrecherche.

## Prüfergebnisse
- 38/38 End-to-End-Tests: Initialisierung, vollständige Auswahl, Freigaben, dynamische Vorschau, ZIP-Erstellung und Wiedereinlesen, 14 Exportdateien, keine alten Thomas-Angebote.
- 31/31 zusätzliche Tests: 320/390/768/1440 px, alle relevanten Ansichten, Freigabeänderungen, URLs und Werbeschalter.
- Testskripte und vollständige Berichte liegen im separaten ZIP-Projektpaket.

## Freigabestatus
**Review-Branch / Draft**. Keine Aktualisierung der bisherigen veröffentlichten `index.html`.
