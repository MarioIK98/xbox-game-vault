#!/usr/bin/env python3
"""Bounded, idempotent SEO migration. No inventory, pricing or advertising changes."""
from pathlib import Path
import hashlib, html, json, re, sys
from xml.etree import ElementTree as ET
ROOT = Path(__file__).resolve().parents[1]
BASE = 'https://marioik98.github.io/xbox-game-vault/'
PUBLIC = BASE + 'oeffentlich/'
MARK = '<meta name="gv-release" content="search-2026-10-28">'
KEY = '2ff40315ae4ecce926bea36e1a26e5d9'
PLATFORMS = {
 'xbox-360': ('Xbox 360', 'Gebrauchte Xbox-360-Spiele entdecken | Game Vault', 55),
 'original-xbox': ('Original Xbox', 'Original Xbox: gebrauchte Spiele | Game Vault', 7),
 'playstation-2': ('PlayStation 2 (PS2)', 'PS2-Spiele aus privater Sammlung | Game Vault', 39),
 'psp': ('PlayStation Portable (PSP)', 'Gebrauchte PSP-Spiele entdecken | Game Vault', 37),
 'playstation-4': ('PlayStation 4 (PS4)', 'Gebrauchte PS4-Spiele im Katalog | Game Vault', 3),
 'playstation-5': ('PlayStation 5 (PS5)', 'PS5-Spiel aus privater Sammlung | Game Vault', 1),
 'nintendo-ds': ('Nintendo DS', 'Nintendo-DS-Spiel im privaten Katalog | Game Vault', 1),
 'pc': ('PC', 'PC-Spiel aus privater Sammlung | Game Vault', 1),
}
EXPECTED = {
 'index.html':'1beb436ffa1a962cc1a6583387a85375b535240c',
 'oeffentlich/index.html':'331756263ec8337339e52f88f204d74a578d652e',
 'oeffentlich/uebersicht.html':'ddeb57dc19124acf365e0cc2733dc49013a01fc1',
 'oeffentlich/sitemap.xml':'27f931f47cc2889683ab298d1f61b2701e432ce1',
 'oeffentlich/robots.txt':'4e7c13c697695b393fc7385b13f46a2fb4ea118e',
 'oeffentlich/sw.js':'966a64329d40cd8494ffecaa072974eb818c039e',
 'oeffentlich/plattform/xbox-360.html':'2d6426375e4720be453a8aeba623ccc5f273596f',
 'oeffentlich/plattform/original-xbox.html':'bf0af51d23266b9575cd955aff13b2cf9803d0c3',
 'oeffentlich/plattform/playstation-2.html':'dfe9e8bdc1f1dbe7030bac5a4f5e4b0009fd860c',
 'oeffentlich/plattform/psp.html':'a355a9ba291d7b59bf6d226bb73252582453c653',
 'oeffentlich/plattform/playstation-4.html':'d5a8a26d58df0828b0950f2ccc95ebf234916d83',
 'oeffentlich/plattform/playstation-5.html':'b360f4e986945f0d1b8b4d8d398b4a7a4c18132a',
 'oeffentlich/plattform/nintendo-ds.html':'cea1bdde7bc680d4356b643c904c36d0e49e9e8c',
 'oeffentlich/plattform/pc.html':'b1dd5e58aba35b6a4c38595156afe5d1d88d663d',
}
def git_hash(data):
 return hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
def metadata(text, title, description):
 text, n = re.subn(r'<title>.*?</title>', '<title>'+html.escape(title)+'</title>', text, count=1, flags=re.S)
 assert n == 1
 for attr, value, content in [('name','description',description),('property','og:title',title),('property','og:description',description)]:
  tag='<meta '+attr+'="'+value+'" content="'+html.escape(content,quote=True)+'">'
  text,n=re.subn(r'<meta\s+'+attr+'="'+re.escape(value)+r'"\s+content="[^"]*"\s*/?>',lambda _:tag,text,count=1)
  if n==0:text=text.replace('</head>',tag+'\n</head>',1)
 text=text.replace('</head>',MARK+'\n</head>',1)
 return text
main=ROOT/'oeffentlich/index.html'
if MARK in main.read_text(encoding='utf-8'):
 print('SEO migration already applied. Verification is a separate step.');sys.exit(0)
before={p:(ROOT/p).read_bytes() for p in EXPECTED}
for p,data in before.items():
 if git_hash(data)!=EXPECTED[p]:raise SystemExit('STOP: source changed: '+p)
for p in ['sitemap.xml',KEY+'.txt']:
 if (ROOT/p).exists():raise SystemExit('STOP: would overwrite existing '+p)
changed={}
text=before['oeffentlich/index.html'].decode()
text=metadata(text,'Game Vault – gebrauchte Videospiele für Xbox, PlayStation & PSP',
 'Gebrauchte Videospiele aus Marios privater Sammlung: Xbox 360, PS2, PSP und weitere Plattformen. Titel entdecken, Merkliste erstellen und unverbindlich anfragen.')
def fix_main_json(match):
 data=json.loads(match.group(1));collection=data['@graph'][0]
 collection['mainEntity']['numberOfItems']=len(collection['mainEntity']['itemListElement'])
 collection['mainEntity']['name']='Spieleplattformen im Game Vault'
 for node in data['@graph']:
  if node.get('@type')=='BreadcrumbList':node['itemListElement'][0]['item']=PUBLIC
 return '<script type="application/ld+json">'+json.dumps(data,ensure_ascii=False,separators=(',',':'))+'</script>'
text,n=re.subn(r'<script type="application/ld\+json">(.*?)</script>',fix_main_json,text,count=1,flags=re.S);assert n==1
text=text.replace('<a href="./uebersicht.html">Alle Seiten</a>', '<a href="./uebersicht.html">Alle Seiten</a><a href="./sitemap.xml">Sitemap</a>',1)
changed['oeffentlich/index.html']=text
for slug,(name,title,count) in PLATFORMS.items():
 p='oeffentlich/plattform/'+slug+'.html';text=before[p].decode()
 desc=f'{name} aus privater Sammlung: '+(f'{count} Katalogpositionen' if count!=1 else 'eine Katalogposition')+'. Titel und Ausgaben ansehen, Auswahl merken und Preis nach Einzelprüfung anfragen.'
 text=metadata(text,title,desc)
 def fix_platform_json(match):
  data=json.loads(match.group(1));data['@graph'][0]['description']=desc
  raw=json.dumps(data,ensure_ascii=False,separators=(',',':')).replace(PUBLIC+'index.html',PUBLIC)
  return '<script type="application/ld+json">'+raw+'</script>'
 text,n=re.subn(r'<script type="application/ld\+json">(.*?)</script>',fix_platform_json,text,count=1,flags=re.S);assert n==1
 text=text.replace('href="../index.html','href="../')
 text=text.replace('<div class="footer-links">','<div class="footer-links"><a href="../uebersicht.html">Alle Plattformen</a>',1)
 changed[p]=text
text=before['oeffentlich/uebersicht.html'].decode()
text=text.replace('content="noindex,follow"','content="index,follow,max-image-preview:large"',1)
text=metadata(text,'Game Vault – Spiele, Plattformen und Partner im Überblick',
 'Marios privater Spielekatalog: Xbox, PlayStation, PSP, Nintendo DS und PC. Alle Plattformen, Merkliste, Partnerbereich und Hinweise direkt erreichen.')
text=text.replace('</head>',f'<link rel="canonical" href="{PUBLIC}uebersicht.html">\n</head>',1)
text=text.replace('<h2>Nach Plattform stöbern</h2>',
 '<section aria-labelledby="about-title"><h2 id="about-title">Was ist Game Vault?</h2><p>Game Vault ist Marios privater Katalog für gebrauchte Videospiele. Du kannst Titel und Ausgaben vergleichen, deine Merkliste zusammenstellen und die Auswahl unverbindlich anfragen. Preise, Zustand und Verfügbarkeit werden vor einer Einigung geprüft.</p><p>Weitere eigene Angebote und Kooperationen können später ergänzt werden. Noch nicht freigegebene Leistungen oder Partner werden nicht als verfügbare Angebote ausgegeben.</p><p><a href="./#partner">Zum Partner- und Empfehlungsbereich →</a></p></section><h2>Nach Plattform stöbern</h2>',1)
text=text.replace('</nav>\n<p class="footer">','</nav>\n<p><a href="./sitemap.xml">Technisches Seitenverzeichnis (XML)</a></p>\n<p class="footer">',1)
changed['oeffentlich/uebersicht.html']=text
changed['index.html']=before['index.html'].decode().replace('content="noindex,follow"','content="index,follow"',1)
urls=[PUBLIC,PUBLIC+'uebersicht.html']+[PUBLIC+'plattform/'+s+'.html' for s in sorted(PLATFORMS)]
ns='http://www.sitemaps.org/schemas/sitemap/0.9';ET.register_namespace('',ns)
xml=ET.Element('{'+ns+'}urlset')
for url in urls:
 node=ET.SubElement(xml,'{'+ns+'}url');ET.SubElement(node,'{'+ns+'}loc').text=url
 ET.SubElement(node,'{'+ns+'}lastmod').text='2026-10-28'
ET.indent(xml,space='  ');sitemap=ET.tostring(xml,encoding='unicode',xml_declaration=True)+'\n'
changed['sitemap.xml']=sitemap;changed['oeffentlich/sitemap.xml']=sitemap
changed['oeffentlich/robots.txt']=('# Informational copy only. This subdirectory is NOT the host root.\n'
 '# Crawlers use https://marioik98.github.io/robots.txt instead.\n'
 '# This file does not submit a sitemap or grant privacy protection.\n'+before['oeffentlich/robots.txt'].decode())
changed['oeffentlich/sw.js']=before['oeffentlich/sw.js'].decode().replace("PREFIX+'2026-10-27-v5.1'","PREFIX+'2026-10-28-search'")
changed[KEY+'.txt']=KEY+'\n'
for pattern in [r'<article\b[^>]*data-public-card.*?</article>',r'data:image/[^"\s]+']:
 old=re.findall(pattern,before['oeffentlich/index.html'].decode(),re.S)
 new=re.findall(pattern,changed['oeffentlich/index.html'],re.S)
 assert old and old==new,'Protected catalogue/media changed'
for path,text in changed.items():(ROOT/path).write_text(text,encoding='utf-8')
print(json.dumps({'changed':list(changed),'sitemap_urls':len(urls),'catalogue_preserved':True},ensure_ascii=False))
