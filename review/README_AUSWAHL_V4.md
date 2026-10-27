# 🎮 GAME VAULT – Selection V4 (Review only)

## Zweck
Stellt die vollständig freie Wunschauswahl aus dem ursprünglichen Game-Vault-Konfigurator wieder her, unter Schutz der allgemeinen öffentlichen Preisregel und der optionalen, rechtlich blockierten Werbedemo.

## Funktionen
- 144/144 anfragbare Spiele, 8 vollständige Plattformen.
- Ganze Plattform mit einem Klick hinzufügen / bei vollständiger Auswahl entfernen.
- Beliebig viele Plattformen kombinieren, einzelne Titel unabhängig hinzugefügt/entfernen.
- Alle anfragbaren Positionen auf einmal auswählen oder gesamte Auswahl nach Bestätigung löschen.
- Auch alle *Suchtreffer* unabhängig von Katalogpaginierung gemeinsam hinzufügen/entfernen.
- Wunschliste nach Plattform gruppiert, Artikel einzeln oder Plattform entfernen, Kopieren/Teilen möglich.
- Getrennte Anzeige-Filter für Katalog ohne Löschung gespeicherter Auswahl.
- Eigene LocalStorage-Schlüssel für normale öffentliche Seite und Werbe-Demo; keine Serverübertragung/Tracking.
- **Alle Preise auf Anfrage**, datierte Marktvergleiche sind ausdrücklich keine Verkaufspreise.
- Externes Casino-Referral bleibt deaktiviert; drei Werbestationen in der Demo sind neutral, abkürzbar und nicht auf Main veröffentlicht.

## Audit
- `QA_SELECTION_V4.json`: 102 von 102 Tests bestanden (inkl. mobile Responsive/Interaktion).
- `QA_WERBEDEMO.json`: 28 von 28 Demo-Funktionstests bestanden.
- Lokal programmatischer Browser-Test verwendet `page.set_content` und simuliert Session-/LocalStorage; echte Android-Zurück-Taste bleibt DEVICE_TEST_OPEN.
- Live-Host-Prüfung bleibt bis zur Genehmigung offen. Kein Update an `main` und keine öffentliche Indexierung der Demo.

## Geschützte Entwicklungsdateien
- `verkauf.html`: allgemeine V3-Verkaufsseite mit wiederhergestellter Gesamtauswahl.
- `werbe-ablauf-demo.html` plus `werbe-ziel-01-demo.html`, `werbe-ziel-02-demo.html`: V4-Demo mit Gesamtauswahl.
- `RECHTS_UND_WERBEPRUEFUNG_2026-10-25.md`: recherchierte Werbegates.
- `test_selection.py`, `test_demo.py`: reproduzierbare lokale Tests.

Veröffentlichung nur nach bestätigter rechtlicher Klärung, Prüfung konkreter Daten und ausdrücklicher Freigabe durch Mario.