# Game Vault — sichere alternative Auslieferung (28.10.2026)

Status: VORBEREITETE, GEPRÜFTE HOSTING-PREVIEW, KEIN GEWERBLICHER LIVE-UMZUG.

## Zweck
Das bestehende Projekt behält GitHub als Quellcode- und Testbasis. Ein separater statischer Host kann mit dem vorhandenen Render-Blueprint später eine nicht indexierte Vorschau der bestehenden Website bereitstellen. Bestand, Bilder, Preise, Partnerfreigaben und Veröffentlichung auf GitHub Pages werden durch diese Vorbereitung nicht verändert.

## Technisch umgesetzt
- tools/build_hosted_release.py baut die gleiche Webseite nur aus ausdrücklich freigegebenen öffentlichen Dateien in dist/.
- Alte HTML-Sicherungen, Forschungsentwürfe, Werkzeuge, Projektanweisungen und interne Werbefreigaben werden nicht in das Hosting-Paket kopiert.
- Vorschau-Ausgabe setzt noindex,nofollow als HTML-Metadaten und in den geplanten Host-HTTP-Headern; robots.txt verbietet in der Vorschau Suchmaschinenzugriff.
- Im Render-Blueprint werden HTTP-Sicherheitsheader für Einbettungs-, MIME-, Referrer- und Berechtigungsbegrenzung vorbereitet. Browser-CSP mit exakten Skripthashes wird nach einem späteren erlaubten Domainwechsel erneut gebildet.
- Produktionsmodus verlangt eine geprüfte HTTPS-Zieladresse und sämtliche Belege aus release/hosting_policy.json. Aktueller Stand commercial_launch_ready: false muss bewusst so bleiben. Keine Kosten, keine Kontoerstellung, keine Werbung.
- tools/test_hosted_release.py überprüft Dateifreigaben, Links, 144 identische Spielkarten, Bilder, Metadaten, Vorschaumodus und Produktionsstopp.
- Das vorhandene Testsystem und die weiteren Sicherheitsprüfungen bleiben in Kraft.

## Vor einem tatsächlichen späteren Umzug nötig
1. Zugänglichen geeigneten Hosting-Account, Betreiberbedingungen, Gebühren und Veröffentlichungsregeln verifizieren.
2. Explizite Zustimmung zu Umzug, öffentlicher Zieladresse, eventuell entstehenden Kosten und späteren Werbeformen einholen.
3. Domain/Zieladresse in Canonicals, Sitemaps, SEO-Daten und Skript-CSP übernehmen und neu testen.
4. Den tatsächlichen HTTP-Header-Empfang, Firewall-/DDoS-Schutz beim Host, Kontoschutz, Datenschutz und Gerätefunktion separat prüfen.
5. Suchmaschinen erst nach bestätigter Freigabe auf die endgültige Adresse führen und alte URLs kontrolliert weiterleiten.

Keine Zusage über 100 Prozent Sicherheit, eine bereits verbundene Render-App oder eine abgeschlossene Google-Indexierung.

Quellen (28.10.2026):
- https://render.com/docs/static-sites
- https://render.com/docs/blueprint-spec
- https://render.com/docs/static-site-headers
- https://render.com/docs/free
- https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits
