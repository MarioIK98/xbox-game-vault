#!/usr/bin/env python3
"""Build high-value GAME VAULT discovery pages from the verified public catalogue."""
from __future__ import annotations
import argparse, html, json, re, unicodedata
from pathlib import Path
from urllib.parse import quote
from xml.etree import ElementTree as ET
ROOT=Path(__file__).resolve().parents[1]
PUBLIC=ROOT/'oeffentlich'
BASE='https://marioik98.github.io/xbox-game-vault/oeffentlich/'
DATE='2026-10-28'
CARD_RE=re.compile(r'<article class="game" id="spiel-([^"]+)" data-public-card="" data-uid="([^"]+)" data-platform="([^"]+)" data-title="([^"]+)" data-edition="([^"]*)" data-photo="([^"]*)">([\s\S]*?)</article>')
PLATFORM_FILE={'Xbox 360':'xbox-360.html','Original Xbox':'original-xbox.html','PS2':'playstation-2.html','PSP':'psp.html','PS4':'playstation-4.html','PS5':'playstation-5.html','Nintendo DS':'nintendo-ds.html','PC':'pc.html'}
PLATFORM_NAME={'Xbox 360':'Xbox 360','Original Xbox':'Original Xbox','PS2':'PlayStation 2 (PS2)','PSP':'PlayStation Portable (PSP)','PS4':'PlayStation 4 (PS4)','PS5':'PlayStation 5 (PS5)','Nintendo DS':'Nintendo DS','PC':'PC'}
SEARCH_NAME={'Xbox 360':'Xbox 360','Original Xbox':'Original Xbox','PS2':'PS2','PSP':'PSP','PS4':'PS4','PS5':'PS5','Nintendo DS':'Nintendo DS','PC':'PC'}
def slugify(s:str)->str:
 s=unicodedata.normalize('NFKD',html.unescape(s)).encode('ascii','ignore').decode().lower()
 s=re.sub(r'[^a-z0-9]+','-',s).strip('-')
 return s[:72].rstrip('-') or 'spiel'
def strip_tags(s:str)->str:
 return re.sub(r'\s+',' ',html.unescape(re.sub(r'<[^>]+>',' ',s))).strip()
def replace_meta(text:str,name:str,value:str,prop=False)->str:
 attr='property' if prop else 'name'
 p=re.compile(r'(<meta\s+'+attr+r'="'+re.escape(name)+r'"\s+content=")[^"]*(">)',re.I)
 text,n=p.subn(lambda m:m.group(1)+html.escape(value,quote=True)+m.group(2),text,count=1)
 if n!=1:raise ValueError('Missing meta '+name)
 return text
def replace_title(text:str,value:str)->str:
 text,n=re.subn(r'<title>.*?</title>','<title>'+html.escape(value)+'</title>',text,count=1,flags=re.S)
 if n!=1:raise ValueError('Missing title')
 return text
def cards():
 source=(PUBLIC/'index.html').read_text(encoding='utf-8')
 out=[]
 for m in CARD_RE.finditer(source):
  body=m.group(7); uid=m.group(2); title=html.unescape(m.group(4)); edition=html.unescape(m.group(5)); platform=html.unescape(m.group(3))
  market=''
  mm=re.search(r'<div class="market-compare">([\s\S]*?)</div>',body)
  if mm:market=strip_tags(mm.group(1))
  source_url=''
  if mm:
   am=re.search(r'<a href="([^"]+)"',mm.group(1))
   if am:source_url=html.unescape(am.group(1))
  image=''
  im=re.search(r'<img\b[^>]*src="(data:image/[^"]+)"',body)
  if im:image=im.group(1)
  out.append({'uid':uid,'platform':platform,'title':title,'edition':edition or 'Ausgabe zu prüfen','market':market,'source':source_url,'image':image,'card':m.group(0)})
 if len(out)!=144:raise ValueError('Expected 144 public cards, got '+str(len(out)))
 return out,source
def detail_rel(g):
 return 'spiele/'+g['uid'].lower()+'-'+slugify(g['title'])+'.html'
def detail_url(g):return BASE+detail_rel(g)
def detail_page(g,related):
 title=f"{g['title']} gebraucht – {SEARCH_NAME[g['platform']]} | GAME VAULT"
 desc=f"{g['title']} für {PLATFORM_NAME[g['platform']]} aus privater Spielesammlung. {g['edition']}. Preis auf Anfrage; Zustand und Verfügbarkeit werden vor Einigung geprüft."
 desc=desc[:190]
 image=('<img class="cover" src="'+g['image']+'" alt="Bestandsfoto: '+html.escape(g['title'],quote=True)+'">' if g['image'] else '<div class="symbol" aria-hidden="true">🎮</div>')
 market=''
 if g['market']:
  link=(' <a href="'+html.escape(g['source'],quote=True)+'" rel="noopener noreferrer" target="_blank">Marktquelle prüfen ↗</a>' if g['source'] else '')
  market='<section class="note"><h2>Marktreferenz</h2><p>'+html.escape(g['market'])+link+'</p><p><strong>Wichtig:</strong> Diese Referenz ist nicht automatisch der Verkaufspreis dieses Exemplars.</p></section>'
 rels=''.join('<li><a href="'+html.escape('../'+detail_rel(x),quote=True)+'">'+html.escape(x['title'])+'</a></li>' for x in related)
 canonical=detail_url(g); platform_page='../plattform/'+PLATFORM_FILE[g['platform']]
 schema=json.dumps({"@context":"https://schema.org","@graph":[{"@type":"WebPage","url":canonical,"name":title,"inLanguage":"de-DE","about":{"@type":"VideoGame","name":g['title'],"gamePlatform":PLATFORM_NAME[g['platform']]}},{"@type":"BreadcrumbList","itemListElement":[{"@type":"ListItem","position":1,"name":"GAME VAULT","item":BASE},{"@type":"ListItem","position":2,"name":PLATFORM_NAME[g['platform']],"item":BASE+'plattform/'+PLATFORM_FILE[g['platform']]},{"@type":"ListItem","position":3,"name":g['title'],"item":canonical}]}]},ensure_ascii=False,separators=(',',':'))
 return f'''<!doctype html>
<html lang="de"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"><meta name="theme-color" content="#111a2f">
<title>{html.escape(title)}</title><meta name="description" content="{html.escape(desc,quote=True)}"><meta name="robots" content="index,follow,max-image-preview:large">
<link rel="canonical" href="{canonical}"><meta property="og:type" content="website"><meta property="og:locale" content="de_DE"><meta property="og:site_name" content="GAME VAULT">
<meta property="og:title" content="{html.escape(title,quote=True)}"><meta property="og:description" content="{html.escape(desc,quote=True)}"><meta property="og:url" content="{canonical}"><meta property="og:image" content="{BASE}og-game-vault.jpg">
<meta name="twitter:card" content="summary_large_image"><meta name="gv-release" content="search-2026-10-28">
<script type="application/ld+json">{schema}</script>
<style>:root{{color-scheme:dark;font-family:system-ui,-apple-system,"Segoe UI",sans-serif;--bg:#111a2f;--panel:#202d49;--text:#f7faff;--muted:#cedcf0;--mint:#7af5d9;--lime:#d8ff9d}}*{{box-sizing:border-box}}body{{margin:0;background:radial-gradient(ellipse at 90% 0%,#7139c944,transparent 46%),var(--bg);color:var(--text);line-height:1.65}}main{{width:min(980px,calc(100% - 32px));margin:auto;padding:28px 0 70px}}a{{color:#b9f8e7}}.crumbs{{font-size:13px;color:var(--muted);margin-bottom:28px}}.hero{{display:grid;grid-template-columns:minmax(0,1.25fr) minmax(220px,.75fr);gap:28px;align-items:center;background:linear-gradient(135deg,#263b61,#223153 55%,#173f46);border:1px solid #85e6ce55;border-radius:26px;padding:34px}}h1{{font-size:clamp(34px,6vw,58px);line-height:1.05;letter-spacing:-.045em;margin:8px 0 14px}}.kicker{{font-size:11px;letter-spacing:.16em;color:var(--mint);font-weight:900;text-transform:uppercase}}.meta{{color:var(--muted);font-size:14px}}.cover{{max-width:100%;max-height:310px;margin:auto;display:block;object-fit:contain;border-radius:12px;filter:drop-shadow(14px 18px 20px #0008)}}.symbol{{width:180px;height:220px;margin:auto;display:grid;place-items:center;font-size:72px;border-radius:24px;background:linear-gradient(145deg,#6239a1,#237d88);border:1px solid #fff4}}.actions{{display:flex;flex-wrap:wrap;gap:10px;margin-top:22px}}.btn{{display:inline-flex;align-items:center;justify-content:center;min-height:48px;padding:12px 16px;border-radius:12px;text-decoration:none;font-weight:850;border:1px solid #8fe8d177}}.primary{{background:linear-gradient(110deg,var(--lime),var(--mint));color:#10271f;border:0}}section.note{{margin-top:22px;padding:22px 24px;border-radius:18px;background:var(--panel);border:1px solid #b9d9ff2d}}h2{{margin:0 0 8px;font-size:21px}}.related{{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:8px;padding:0;list-style:none}}.related a{{display:block;padding:11px 13px;background:#182641;border-radius:10px;text-decoration:none}}footer{{margin-top:30px;color:var(--muted);font-size:12px}}@media(max-width:700px){{.hero{{grid-template-columns:1fr;padding:24px}}.actions{{display:grid}}}}</style></head><body><main>
<nav class="crumbs"><a href="../">GAME VAULT</a> · <a href="{platform_page}">{html.escape(PLATFORM_NAME[g['platform']])}</a> · {html.escape(g['uid'])}</nav>
<section class="hero"><div><span class="kicker">Gebrauchtes Spiel · {html.escape(PLATFORM_NAME[g['platform']])}</span><h1>{html.escape(g['title'])}</h1><p class="meta"><strong>{html.escape(g['edition'])}</strong> · Kennung {html.escape(g['uid'])} · <strong>Preis auf Anfrage</strong></p>
<p>Dieses Exemplar gehört zur privaten GAME VAULT-Spielesammlung. Datenträger, genaue Ausgabe, Vollständigkeit, Zustand, Altersfreigabe und Verfügbarkeit werden vor einer Einigung geprüft.</p>
<div class="actions"><a class="btn primary" href="../?auswahl={quote(g['uid'])}#spiele">Dieses Spiel vormerken</a><a class="btn" href="../?spiel={quote(g['uid'])}#spiele">Im Gesamtkatalog ansehen</a><a class="btn" href="{platform_page}">Alle {html.escape(SEARCH_NAME[g['platform']])}-Spiele</a></div></div><div>{image}</div></section>
{market}
<section class="note"><h2>Ähnliche Spiele derselben Plattform</h2><ul class="related">{rels}</ul></section>
<footer>Privatverkauf aus eigener Sammlung. Keine automatische Bestellung oder Reservierung. Preis und Übergabe erst nach Einzelfallprüfung.</footer>
</main></body></html>'''
def collection_page(games):
 groups={p:[g for g in games if g['platform']==p] for p in PLATFORM_FILE}
 cards=[]
 for p,items in groups.items():
  ids=','.join(x['uid'] for x in items)
  cards.append(f'<article class="bundle"><span>{len(items)} Positionen</span><h2>{html.escape(PLATFORM_NAME[p])}</h2><p>Einzeln auswählen oder das komplette Plattformpaket vormerken.</p><div><a href="./plattform/{PLATFORM_FILE[p]}">Titel ansehen</a><a class="pick" href="./?auswahl={quote(ids,safe=",")}#spiele">Alle {len(items)} vormerken</a></div></article>')
 allids=','.join(g['uid'] for g in games)
 desc='144 gebrauchte Videospiele aus privater Sammlung: Xbox 360, PS2, PSP, Original Xbox, PS4, PS5, Nintendo DS und PC. Einzelne Spiele oder ganze Pakete unverbindlich anfragen.'
 return f'''<!doctype html><html lang="de"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"><meta name="theme-color" content="#111a2f">
<title>Videospiele-Sammlung: 144 Spiele für Xbox, PS2, PSP & mehr | GAME VAULT</title><meta name="description" content="{html.escape(desc,quote=True)}"><meta name="robots" content="index,follow,max-image-preview:large"><link rel="canonical" href="{BASE}spiele-sammlung.html">
<meta property="og:type" content="website"><meta property="og:site_name" content="GAME VAULT"><meta property="og:title" content="Videospiele-Sammlung: 144 Spiele für Xbox, PS2, PSP &amp; mehr | GAME VAULT"><meta property="og:description" content="{html.escape(desc,quote=True)}"><meta property="og:url" content="{BASE}spiele-sammlung.html"><meta property="og:image" content="{BASE}og-game-vault.jpg"><meta name="gv-release" content="search-2026-10-28">
<style>:root{{color-scheme:dark;font-family:system-ui,-apple-system,"Segoe UI",sans-serif;--bg:#111a2f;--panel:#202d49;--text:#f7faff;--muted:#cedcf0;--mint:#7af5d9;--lime:#d8ff9d}}*{{box-sizing:border-box}}body{{margin:0;background:radial-gradient(ellipse at 90% 0%,#7139c944,transparent 50%),var(--bg);color:var(--text);line-height:1.6}}main{{width:min(1100px,calc(100% - 32px));margin:auto;padding:30px 0 70px}}a{{color:#baf8e5}}h1{{font-size:clamp(38px,7vw,68px);line-height:1.03;letter-spacing:-.05em;margin:20px 0 16px}}.lead{{max-width:800px;color:var(--muted);font-size:17px}}.hero{{padding:34px;border:1px solid #83e7cb55;border-radius:26px;background:linear-gradient(135deg,#2d3a70,#1d555b)}}.hero strong{{color:var(--lime)}}.actions{{display:flex;flex-wrap:wrap;gap:10px;margin-top:22px}}.btn{{display:inline-flex;min-height:48px;align-items:center;padding:12px 17px;border-radius:12px;text-decoration:none;font-weight:850;border:1px solid #a4f3db66}}.primary{{background:linear-gradient(110deg,var(--lime),var(--mint));color:#10271f;border:0}}.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:13px;margin-top:24px}}.bundle{{padding:22px;border:1px solid #aacdf02d;border-radius:18px;background:var(--panel)}}.bundle span{{font-size:11px;color:var(--mint);font-weight:850;letter-spacing:.08em;text-transform:uppercase}}.bundle h2{{margin:7px 0 8px}}.bundle p{{color:var(--muted);font-size:13px}}.bundle div{{display:flex;gap:10px;flex-wrap:wrap}}.bundle a{{font-size:13px}}.bundle .pick{{font-weight:800}}.note{{margin-top:28px;padding:22px;border-radius:18px;background:#17233c;color:var(--muted)}}@media(max-width:600px){{.hero{{padding:24px}}.actions{{display:grid}}}}</style></head><body><main><p><a href="./">← GAME VAULT Spielekatalog</a></p><section class="hero"><span>PRIVATE SPIELESAMMLUNG · 8 PLATTFORMEN</span><h1>144 gebrauchte Videospiele.<br><strong>Einzeln oder als Paket anfragen.</strong></h1><p class="lead">Die größten Bereiche sind 55 Xbox-360-Spiele, 39 PS2-Spiele und 37 PSP-Spiele. Mehrere Titel, komplette Plattformen oder der gesamte anfragbare Bestand können in einer Merkliste zusammengefasst werden.</p><div class="actions"><a class="btn primary" href="./?auswahl={quote(allids,safe=",")}#spiele">Gesamten Bestand vormerken</a><a class="btn" href="./#spiele">Einzelne Spiele auswählen</a></div></section>
<div class="grid">{''.join(cards)}</div><section class="note" id="verkaufskanaele"><h2>PS1-Konsole separat auf eBay und Kleinanzeigen</h2><p><strong>Eigenständige Konsolenangebote:</strong> Die Sony PlayStation 1 (SCPH-9002) ist außerdem auf eBay und Kleinanzeigen eingestellt. Beide Angebote betreffen die Konsole; die 144 Spiele im GAME VAULT bleiben davon unabhängig einzeln oder als Paket auswählbar. Preis und Verfügbarkeit bitte jeweils auf der Verkaufsplattform prüfen.</p><p class="actions"><a class="btn primary" href="https://www.ebay.de/itm/820268079932" target="_blank" rel="noopener noreferrer">PS1 auf eBay ansehen ↗</a><a class="btn" href="https://www.kleinanzeigen.de/s-anzeige/3548893324" target="_blank" rel="noopener noreferrer">PS1 auf Kleinanzeigen ansehen ↗</a></p></section><section class="note"><h2>So läuft eine Paket-Anfrage</h2><p>Die Auswahl ist unverbindlich und reserviert nichts. Vor einer Einigung werden Verfügbarkeit, Datenträger, Edition, Vollständigkeit, Zustand, Altersfreigabe sowie Einzel- oder Paketpreis geprüft. Dadurch können auch größere Sammlungsanfragen vorbereitet werden, ohne ungeprüfte Festpreise zu erfinden.</p></section></main></body></html>'''
def patch_main(source):
 source=replace_title(source,'Gebrauchte Videospiele: Xbox 360, PS2, PSP & mehr | GAME VAULT')
 source=replace_meta(source,'description','144 gebrauchte Videospiele aus privater Sammlung: 55 Xbox 360, 39 PS2, 37 PSP und weitere Plattformen. Einzelne Spiele oder ganze Pakete unverbindlich anfragen.')
 source=replace_meta(source,'og:title','Gebrauchte Videospiele: Xbox 360, PS2, PSP & mehr | GAME VAULT',True)
 source=replace_meta(source,'og:description','144 gebrauchte Videospiele aus privater Sammlung: 55 Xbox 360, 39 PS2, 37 PSP und weitere Plattformen. Einzelne Spiele oder ganze Pakete unverbindlich anfragen.',True)
 source,n=re.subn(r'<h1 id="hero-title">.*?</h1>','<h1 id="hero-title">Gebrauchte Videospiele für Xbox 360, PS2, PSP &amp; mehr. <em>Einzeln oder als Paket anfragen.</em></h1>',source,count=1,flags=re.S)
 if n!=1:raise ValueError('Hero H1 not found')
 source,n=re.subn(r'<p class="hero-lead">.*?</p>','<p class="hero-lead">144 anfragbare Positionen aus acht Plattformen. Schwerpunkte: 55 Xbox-360-Spiele, 39 PS2-Spiele und 37 PSP-Spiele. Suche einzelne Titel oder stelle komplette Plattformpakete zusammen.</p>',source,count=1,flags=re.S)
 if n!=1:raise ValueError('Hero lead not found')
 if 'id="verkaufsfokus"' not in source:
  block='''<section class="section" id="verkaufsfokus" aria-labelledby="verkaufsfokus-title"><div class="section-head"><div><span class="kicker">SCHNELL ZUR PASSENDEN AUSWAHL</span><h2 id="verkaufsfokus-title">Einzelspiel, Plattformpaket oder ganze Sammlung.</h2><p class="section-desc">Für Käufer, die gezielt gebrauchte Xbox-360-, PS2- oder PSP-Spiele suchen, gibt es eigene Plattformseiten. Größere Anfragen lassen sich direkt als Paket vorbereiten.</p></div></div><div class="steps"><article class="step"><span class="step-number">55</span><h3>Xbox 360 Spiele</h3><p><a href="./plattform/xbox-360.html">Gebrauchte Xbox-360-Spiele ansehen →</a></p></article><article class="step"><span class="step-number">39</span><h3>PS2 Spiele</h3><p><a href="./plattform/playstation-2.html">Gebrauchte PS2-Spiele ansehen →</a></p></article><article class="step"><span class="step-number">37</span><h3>PSP Spiele</h3><p><a href="./plattform/psp.html">Gebrauchte PSP-Spiele ansehen →</a></p></article></div><p><a class="btn btn-primary" href="./spiele-sammlung.html">Alle 144 Spiele als Sammlung ansehen ↗</a></p></section>\n'''
  marker='<section class="section" id="plattformen"'
  if marker not in source:raise ValueError('Platform section marker missing')
  source=source.replace(marker,block+marker,1)
 return source
def patch_overview(text):
 if 'href="./spiele-sammlung.html"' not in text:
  needle='<a class="card primary" href="./"><strong>Gesamten Spielekatalog öffnen →</strong><span>Suchen, filtern, Plattformen kombinieren und Wunschliste teilen.</span></a>'
  add=needle+'<a class="card primary" href="./spiele-sammlung.html"><strong>144 Spiele als Sammlung ansehen →</strong><span>Einzelne Titel, ganze Plattformen oder den kompletten anfragbaren Bestand vormerken.</span></a>'
  if needle not in text:raise ValueError('Overview insertion point missing')
  text=text.replace(needle,add,1)
 return text
def patch_platform(text,p,items):
 title=f"{SEARCH_NAME[p]} Spiele gebraucht – {len(items)} Titel | GAME VAULT" if len(items)>1 else f"{SEARCH_NAME[p]} Spiel gebraucht | GAME VAULT"
 desc=(f"{len(items)} gebrauchte {SEARCH_NAME[p]}-Spiele aus privater Sammlung. Titel einzeln ansehen oder das komplette Plattformpaket vormerken; Preis und Zustand werden vor Einigung geprüft." if len(items)>1 else f"Gebrauchtes {SEARCH_NAME[p]}-Spiel aus privater Sammlung. Titel ansehen und unverbindlich vormerken; Preis und Zustand werden vor Einigung geprüft.")
 text=replace_title(text,title);text=replace_meta(text,'description',desc);text=replace_meta(text,'og:title',title,True);text=replace_meta(text,'og:description',desc,True)
 ids=','.join(x['uid'] for x in items)
 intro=f'''<section class="platform-intro"><span class="kicker">GAME VAULT / GEBRAUCHTE {html.escape(SEARCH_NAME[p].upper())}-SPIELE</span><h1>{html.escape(SEARCH_NAME[p])} Spiele gebraucht aus privater Sammlung</h1><p>Aktuell sind {len(items)} Katalogpositionen für {html.escape(PLATFORM_NAME[p])} unverbindlich anfragbar. Einzelne Spiele lassen sich gezielt öffnen; für einen schnelleren Paketkauf kann die komplette Plattformauswahl auf einmal vorgemerkt werden.</p><p>Preis, konkreter Datenträger, Ausgabe, Vollständigkeit, Zustand, Altersfreigabe und Verfügbarkeit werden vor einer Einigung geprüft.</p><a class="btn btn-primary" href="../?plattform={quote(p)}#spiele">Alle {len(items)} im Katalog ansehen ↗</a> <a class="btn btn-ghost" href="../?auswahl={quote(ids,safe=",")}#spiele">Komplettes {html.escape(SEARCH_NAME[p])}-Paket vormerken</a></section>'''
 text,n=re.subn(r'<section class="platform-intro">[\s\S]*?</section>',intro,text,count=1)
 if n!=1:raise ValueError('Platform intro missing '+p)
 lis=''.join(f'<li><a href="../{detail_rel(g)}">{html.escape(g["title"])}<small>{html.escape(g["edition"])} · Preis auf Anfrage</small></a></li>' for g in items)
 text,n=re.subn(r'(<ul class="platform-titles">)[\s\S]*?(</ul>)',lambda m:m.group(1)+lis+m.group(2),text,count=1)
 if n!=1:raise ValueError('Platform list missing '+p)
 for g in items:
  text=text.replace(BASE+'?spiel='+g['uid'],detail_url(g))
 return text
def sitemap(games):
 ns='http://www.sitemaps.org/schemas/sitemap/0.9'
 urls=[BASE,BASE+'uebersicht.html',BASE+'spiele-sammlung.html']+[BASE+'plattform/'+PLATFORM_FILE[p] for p in PLATFORM_FILE]+[detail_url(g) for g in games]
 root=ET.Element('urlset',xmlns=ns)
 for u in urls:
  x=ET.SubElement(root,'url');ET.SubElement(x,'loc').text=u;ET.SubElement(x,'lastmod').text=DATE
 ET.indent(root)
 return '<?xml version="1.0" encoding="UTF-8"?>\n'+ET.tostring(root,encoding='unicode')+'\n'
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--apply',action='store_true');args=ap.parse_args()
 games,source=cards();groups={p:[g for g in games if g['platform']==p] for p in PLATFORM_FILE}
 changes={}
 changes[PUBLIC/'index.html']=patch_main(source)
 changes[PUBLIC/'uebersicht.html']=patch_overview((PUBLIC/'uebersicht.html').read_text(encoding='utf-8'))
 changes[PUBLIC/'spiele-sammlung.html']=collection_page(games)
 for p,items in groups.items():
  file=PUBLIC/'plattform'/PLATFORM_FILE[p];changes[file]=patch_platform(file.read_text(encoding='utf-8'),p,items)
 for p,items in groups.items():
  for idx,g in enumerate(items):
   related=[x for x in items if x['uid']!=g['uid']][:5]
   changes[PUBLIC/detail_rel(g)]=detail_page(g,related)
 sm=sitemap(games);changes[ROOT/'sitemap.xml']=sm;changes[PUBLIC/'sitemap.xml']=sm
 drift=[str(p.relative_to(ROOT)) for p,v in changes.items() if not p.exists() or p.read_text(encoding='utf-8')!=v]
 if args.apply:
  for p,v in changes.items():p.parent.mkdir(parents=True,exist_ok=True);p.write_text(v,encoding='utf-8')
  print('Generated/updated',len(drift),'files');return
 if drift:raise SystemExit('Generated sales/discovery files are stale: '+', '.join(drift[:20])+(' …' if len(drift)>20 else ''))
 print('PASS: generated sales/discovery pages are current')
if __name__=='__main__':main()
