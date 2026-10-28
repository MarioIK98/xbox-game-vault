# Game Vault — Fortsetzung und wiederverwendbare Fehlerlektionen

Stand: 28.10.2026. Projektspezifischer Arbeitskontext, keine globale Erinnerung und keine neue oberste Instanz. Aktuelle Commits, Tests und Veröffentlichungsstatus immer lesen, nicht aus dieser Datei ableiten.

## Bestätigter Auftrag
Bestehende Webseite real weiterentwickeln, keine Ersatz-App. Bedienbare öffentliche Seiten statt Textdateien als vermeintliche fertige Benutzeroberfläche. Mario plant später eigene Dienstleistungen, Empfehlungen und Partnerwerbung. Diese Zukunft nicht als bereits verfügbare Leistung veröffentlichen. Bestandsdaten, Preise, Bilder und gesperrte Positionen erhalten. Rex-Infernus und Dokumentenarchiv nicht verändern.

## Aktuelle Teilaufgabe
Weiterempfehlungsseite mit tatsächlicher Vorschau, zehn vorhandenen Seiten als Auswahl, editierbarem Beitrag, Kopieren und bewusst ausgelöstem Teilen. Downloads sind nur eine Zusatzfunktion. Keine persistente Speicherung des bearbeiteten Beitrags, kein automatischer Versand. Ein erfolgreicher mock-basierter Teilen-Test ist kein Beweis für alle Smartphone-Apps. Test- und Live-Abschluss stehen getrennt im zugehörigen Pull Request.

## Hosting zuerst prüfen
Vor kommerzieller Erweiterung `release/hosting_policy.json` lesen und `python tools/check_hosting.py` ausführen. GitHub als Codebestand ist nicht GitHub Pages als kostenloser Webhost. Pages ist laut Anbieter nicht für Online-Business/E-Commerce oder primär kommerzielle Transaktionen zugelassen. Vercel Hobby ist ebenfalls kein geeigneter kommerzieller Ersatz. Eine Weiterentwicklung des Codes bleibt möglich; der spätere Betriebsweg muss zum bestätigten Zweck passen.

Der Test berücksichtigt den deklarierten Veröffentlichungszweck. Er ist keine Rechtsprüfung, kein automatischer Inhaltsklassifikator und keine technisch erzwungene Branch-Sperre. Anbieter, Plan, Grenzen, Kosten, Konto-Zugriff und Freigabe müssen belegt sein. Keine kostenpflichtigen Konten, Vertragsabschlüsse, Domainkäufe oder Umzüge ohne Marios ausdrückliche Zustimmung. Bisher kein bestätigter kommerzieller Zielhost.

## Wiederverwendbarer Bestand
- `tools/prepare_security_release.py`: CSP-Hashes und Inhalte aus tatsächlichen Katalogseiten; aktuelles HTML-Design nicht durch eine zweite Webseite ersetzen.
- `tools/test_game_vault.py`: bestehende Käuferfunktionen, HTTP und Offline-Verhalten.
- `tools/test_security.py`: begrenzte isolierte Browser-Sicherheitsproben.
- `tools/test_sharing_ui.py`: tatsächliche Bedienelemente, Auswahl, Kopieren, Abbruch, Fallbacks und Bildschirmbreiten.
- `tools/verify_public_security.py`: lesende Kontrolle der veröffentlichten Dateien; wartet auch auf die neue Teilen-Seite, nicht nur den unveränderten Katalog.
- `tools/check_search.py`: Suchmaschinenmetadaten, URLs und begrenzte IndexNow-Meldungen. Empfang ist keine Indexierung.

## Fehlerlektionen
1. Vorschau, Code im Repository, Tests und öffentliche Veröffentlichung getrennt benennen. Keine Fertigmeldung für einen nur lokal vorhandenen Entwurf.
2. Primär eine benutzbare Webseite liefern. TXT, JSON, RSS und ZIP sind Zusatzartefakte, keine Bedienoberfläche.
3. Ein blockierter Test ist kein bestandener Test. Nicht wiederholt denselben blockierten Weg verwenden; lokal begrenzt prüfen, danach zugelassene CI-Umgebung nutzen.
4. Hostingbedingungen und mögliche Kosten vor einem Ausbau prüfen, nicht erst am Schluss.
5. Neue Tests sollen reale Fehler abfangen. Viele bestandene Prüfungen bedeuten weder Schutz vor allen Bedrohungen noch eine vollständige Geschäftsabnahme.
6. Kein automatischer globaler Wissenstransfer zwischen allen Chats behaupten. Dieses Repository ist der zugängliche Projektkontext für ChatGPT, Codex und spätere Bearbeiter.

## Offen, nicht als erledigt darstellen
Geeigneter kommerzieller Hostingzugang und gegebenenfalls freigegebener Umzug; Google-Search-Console-Eigentumsnachweis; tatsächlich freigegebene Werbepartner und Kontaktwege; echte Kanalverteilung; unabhängige Schutzabnahme. Keine 100-Prozent-Sicherheit. Keine künstlichen Besucher, ungefragte Geräteöffnungen oder selbstverbreitenden Programme.

## Arbeitskommunikation
Mario will Ergebnisse und notwendige Entscheidungen, keine laufenden Denk- oder Arbeitskommentare. Bei unvermeidbaren externen Voraussetzungen diese konkret benennen, nicht durch neue Entwürfe oder unbestätigte Fertigmeldungen verdecken.
