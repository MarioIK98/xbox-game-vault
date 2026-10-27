# Game Vault – Suchmaschinenauffindbarkeit und weitere Entwicklung

## Auftrag und Abgrenzung
Mario hat am 28.10.2026 die reale technische Umsetzung der Auffindbarkeit beauftragt. Die bestehende Seite soll hier gemeinsam weiterentwickelt werden; später können konkrete eigene Dienstleistungen sowie freigegebene nicht glücksspielbezogene Partnerangebote für Mario und Freunde hinzukommen. Noch nicht benannte Leistungen werden nicht erfunden. Der Spielekatalog wird nicht ersetzt oder umbenannt. Rex-Infernus und Dokumentenarchiv bleiben unangetastet.

## Ausgangspunkt und Befund
- Repository: MarioIK98/xbox-game-vault; Ausgangscommit: fa0827ee5e05af7e445618a86c1319686e7de88c.
- Tatsächlich hatten alle acht Plattformseiten denselben allgemeinen Titel und dieselbe Beschreibung. Frühere Prüfberichte mit abweichender Aussage sind kein Beleg für diesen aktuellen Quellstand.
- Die Seitenübersicht war mit noindex versehen; die Sitemap enthielt nur neun Seiten.
- Das strukturierte Hauptseiten-Verzeichnis nannte 144 Elemente, listete aber acht Plattformen. Korrigiert wird ausschließlich diese Listenbeschreibung, nicht der Bestand von 144 Katalogpositionen.
- robots.txt im Unterordner ist keine wirksame hostweite robots.txt. Keine gegenteilige Schutz- oder Einreichungsbehauptung.

## Umsetzung und Prüfkriterien
Vorhandenen Workflow und Browsertest wiederverwenden. Neue isolierte Review-Branch, damit ein fehlerhafter Zwischenstand nicht main veröffentlicht. Die einmalige Migration stoppt bei abweichenden Quelldateien und schützt Spielkarten und Bilder bytegenau.

- Zehn verschiedene Seitentitel und Beschreibungen; passende Social-Metadaten.
- Eindeutige kanonische URLs, bereinigte interne Verweise und eine indexierbare Seitenübersicht.
- Sitemap mit Hauptkatalog, Übersicht und acht Plattformseiten. Keine Vorschau-, Auswahl- oder Archiv-URLs einreichen.
- Bestehende Website-Struktur, Preisregeln, Inventar, Bilder, rechtliche Hinweise und Werbeplätze erhalten.
- Öffentliches IndexNow-Nachweisfile ausschließlich im Game-Vault-Pfad. Benachrichtigung erst nach erfolgreichem Abruf und exaktem Inhaltsvergleich der tatsächlich veröffentlichten Dateien; nur geänderte kanonische Seiten melden.
- Keine erfundenen Rabatte, Sternebewertungen, Product-Offers, Kontaktdaten oder Kundenstimmen.
- Keine automatische Aktivierung der sim.de-Vorschau und keine Casino-Werbung.

## Evidenz und Statusgrenzen
`tools/check_search.py` prüft Metadaten, Sitemap, interne Links, strukturierte Listen und optional den Live-Stand. `tools/test_game_vault.py` bleibt der vorhandene Käuferablauf-Test.
Die JSON-Berichte und der getestete Commit werden als GitHub-Actions-Artefakte gespeichert. Ein erfolgreicher Build ist nicht gleich Live-Erreichbarkeit; HTTP 200/202 von IndexNow ist nicht gleich Indexierung oder Ranking. Google wird durch IndexNow nicht als eingereicht ausgegeben.

## Google: noch separat erforderlich
Für kontrollierte Google-Einreichung zuerst Eigentümerschaft in Google Search Console nachweisen. Empfohlene URL-Präfix-Property für den bestehenden Projektpfad:
`https://marioik98.github.io/xbox-game-vault/`
Sitemap:
`https://marioik98.github.io/xbox-game-vault/sitemap.xml`
Eine eventuell erhaltene HTML-Verifizierungsdatei muss exakt mit dem von Google gelieferten Inhalt veröffentlicht werden. Keine Token erfinden, keine fremden Analytics-/Tag-Manager-Konten zur Verifizierung verwenden. Danach Sitemap einreichen und den Katalog über die URL-Prüfung kontrollieren. Kein Konto wurde allein durch diese Dokumentation angelegt oder bestätigt.

## Künftige Dienste und Werbung
Ausbau am bestehenden Projekt, getrennt vom jetzigen SEO-Auftrag: konkrete Leistung, Anbieter, Inhalte und Kontaktweg festlegen; Anzeige als Werbung kennzeichnen; Nutzungsrechte und Bedingungen prüfen; erst danach freigegebene Inhalte veröffentlichen. Keine weitere leere Webseite und keine neue Projektwahrheit.
GitHub Pages erlaubt keine primär auf kommerzielle Transaktionen ausgerichtete Online-Geschäfts-/E-Commerce-Plattform. Vor dem geplanten kommerziellen Ausbau daher einen passenden Hostingweg prüfen; keine kostenpflichtige Buchung oder Domainänderung ohne Mario. Quellcode und Inhalte bleiben wiederverwendbar.

## Wiederherstellung
Ausgangscommit bleibt unverändert erreichbar. Rücknahme durch nachvollziehbaren Revert des zusammenhängenden SEO-Merge-Commits; keine erzwungene History-Umschreibung und keine Löschung von Backups.

## Primärquellen
- https://developers.google.com/search/docs/appearance/title-link
- https://developers.google.com/search/docs/crawling-indexing/sitemaps/build-sitemap
- https://developers.google.com/search/docs/crawling-indexing/consolidate-duplicate-urls
- https://developers.google.com/crawling/docs/robots-txt/create-robots-txt
- https://www.indexnow.org/documentation
- https://www.bing.com/indexnow/getstarted
- https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits
