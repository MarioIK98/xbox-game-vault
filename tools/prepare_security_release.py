#!/usr/bin/env python3
"""Bounded Game Vault hardening and opt-in sharing assets. No network, sending or WAF claims."""
from __future__ import annotations
import argparse, base64, hashlib, html, json, re, zipfile
from html.parser import HTMLParser
from pathlib import Path
from xml.etree import ElementTree as ET
ROOT=Path(__file__).resolve().parents[1]
PUBLIC='https://marioik98.github.io/xbox-game-vault/oeffentlich/'
MARK='gv-security-2026-10-28-v1'
BLOCK=re.compile(r'<!-- GV_SECURITY_START -->.*?<!-- GV_SECURITY_END -->\n?',re.S)
SCRIPTS=re.compile(r'<script\b[^>]*>(.*?)</script\s*>',re.S|re.I)
BASE_BLOB='e3c5722989f6fd5d9e29c83ecb34b6bf113518d7'

def digest(s:str)->str:
 return base64.b64encode(hashlib.sha256(s.encode()).digest()).decode()

def csp(text:str)->str:
 hashes=sorted({"'sha256-"+digest(s)+"'" for s in SCRIPTS.findall(text)})
 return "; ".join(["default-src 'none'","base-uri 'none'","object-src 'none'","frame-src 'none'","form-action 'none'","script-src "+(' '.join(hashes) or "'none'"),"script-src-attr 'none'","style-src 'self' 'unsafe-inline'","img-src 'self' data:","font-src 'self'","connect-src 'self'","manifest-src 'self'","worker-src 'self'","media-src 'none'"])

def protected(text:str)->dict:
 return {name:re.findall(p,text,re.S) for name,p in {
  'cards':r'<article\b[^>]*data-public-card.*?</article>',
  'images':r'data:image/[^"\s]+',
  'partners':r'<section class="section" id="partner".*?</section>'}.items()}

def change_inputs(text:str)->str:
 if MARK in text:return text
 raw=text.encode();blob=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
 if blob!=BASE_BLOB:raise ValueError('STOP: catalogue snapshot differs; review instead of overwriting')
 old="try{const raw=JSON.parse(localStorage.getItem(storeKey)||'[]');if(Array.isArray(raw))wanted=new Set(raw.filter(x=>typeof x==='string'&&byId.has(x)).slice(0,cards.length))}catch(_){}"
 new="""// gv-security-2026-10-28-v1: validate untrusted browser storage before parsing.
try{const saved=localStorage.getItem(storeKey)||'[]';if(saved.length<=10000){const raw=JSON.parse(saved);if(Array.isArray(raw)&&raw.length<=500)wanted=new Set(raw.filter(x=>typeof x==='string'&&byId.has(x)).slice(0,cards.length));}}catch(_){}"""
 assert text.count(old)==1;text=text.replace(old,new)
 old="function initSharedSelection(){\n const q=new URLSearchParams(location.search).get('auswahl');if(q===null)return;"
 new="""function initSharedSelection(){
 if(location.search.length>16384){shareBanner.hidden=false;$('sharedSelectionDescription').textContent='Dieser Link ist zu lang. Die vorhandene Merkliste bleibt unverändert.';$('importSharedWishlist').hidden=true;return;}
 const q=new URLSearchParams(location.search).get('auswahl');if(q===null)return;"""
 assert text.count(old)==1;text=text.replace(old,new)
 old="const qs=new URLSearchParams(location.search);const p=qs.get('plattform');"
 new="const qs=new URLSearchParams(location.search.length<=16384?location.search:'');const p=qs.get('plattform');"
 assert text.count(old)==1;text=text.replace(old,new)
 return text

class Meta(HTMLParser):
 def __init__(self,text):
  super().__init__();self.title='';self.description='';self.inside=False;self.feed(text)
 def handle_starttag(self,t,a):
  a=dict(a)
  if t=='title':self.inside=True
  if t=='meta' and a.get('name')=='description':self.description=a.get('content','')
 def handle_endtag(self,t):
  if t=='title':self.inside=False
 def handle_data(self,d):
  if self.inside:self.title+=d

def sharing_files(root:Path)->dict[Path,str]:
 ns={'s':'http://www.sitemaps.org/schemas/sitemap/0.9'}
 urls=[x.text for x in ET.fromstring((root/'sitemap.xml').read_text()).findall('s:url/s:loc',ns)]
 records=[]
 for url in urls:
  if not url.startswith(PUBLIC) or '?' in url or '#' in url:raise ValueError('Unapproved URL')
  rel=url.removeprefix(PUBLIC) or 'index.html'
  path=(root/'oeffentlich'/rel).resolve()
  if not path.is_relative_to((root/'oeffentlich').resolve()):raise ValueError('Outside public directory')
  p=Meta(path.read_text());records.append({'title':p.title,'description':p.description,'url':url})
 payload={'purpose':'Opt-in sharing material, not automatically distributed','automatic_sending':False,'ranking_guarantee':False,'items':records}
 text='GAME VAULT · FREIWILLIG TEILEN\n\nNur selbst veröffentlichen oder an Personen senden, die diese Information wünschen.\nKeine garantierte Verfügbarkeit, keine erfundenen Preise, keine aktiven Partnerangebote.\n\n'
 for r in records:text+=r['title']+'\n'+r['description']+'\n'+r['url']+'\n\n'
 rss=ET.Element('rss',version='2.0');ch=ET.SubElement(rss,'channel')
 for k,v in [('title','Game Vault – öffentliche Katalogseiten'),('link',PUBLIC),('description','Freiwillig abonnierbarer Katalogfeed. Keine Preis- oder Verfügbarkeitsgarantie.'),('language','de-DE')]:ET.SubElement(ch,k).text=v
 for r in records:
  item=ET.SubElement(ch,'item')
  for k,v in [('title',r['title']),('link',r['url']),('description',r['description'])]:ET.SubElement(item,k).text=v
  ET.SubElement(item,'guid',isPermaLink='true').text=r['url']
 ET.indent(rss)
 return {root/'oeffentlich/reichweite/links.json':json.dumps(payload,ensure_ascii=False,indent=2)+'\n',root/'oeffentlich/reichweite/beitraege.txt':text,root/'oeffentlich/reichweite/feed.xml':'<?xml version="1.0" encoding="utf-8"?>\n'+ET.tostring(rss,encoding='unicode')+'\n'}

def share_page()->str:
 return '''<!doctype html><html lang="de"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex,follow"><title>Game Vault teilen – Links und Katalogfeed</title><meta name="description" content="Game Vault freiwillig weiterempfehlen: öffentlicher Kataloglink, Textpaket und abonnierbarer Feed. Kein automatischer Versand."><style>:root{color-scheme:dark;font-family:system-ui,sans-serif;background:#090e20;color:#f5f7ff}*{box-sizing:border-box}body{margin:0;line-height:1.65}main{max-width:1000px;margin:auto;padding:32px 20px 60px}h1{font-size:clamp(2rem,5vw,3rem);line-height:1.15}p{color:#c4d2e7}a{color:#b5f8df}a:focus-visible,textarea:focus-visible{outline:3px solid #d5ff86;outline-offset:4px}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,240px),1fr));gap:16px}.card{padding:22px;border:1px solid #52637b;border-radius:18px;background:#151d36}h2{font-size:1.2rem}.button{display:inline-block;padding:12px 16px;border:1px solid #69f2d4;border-radius:10px;font-weight:750;text-decoration:none}textarea{width:100%;padding:14px;background:#101a2c;color:#f5f7ff;border:1px solid #8397ad;border-radius:12px;font:inherit;resize:vertical}.note{border-left:4px solid #d5ff86;padding:10px 16px;margin-top:24px}</style></head><body><main><a href="./">← Spielekatalog</a><h1>Game Vault weiterempfehlen.</h1><p>Hier findest du vorbereitete Links und Texte für deine eigene Veröffentlichung oder für Menschen, die diese Information erhalten möchten. Diese Seite versendet nichts automatisch.</p><label for="publicLink">Öffentliche Adresse zum Markieren und Kopieren</label><textarea id="publicLink" rows="2" readonly>https://marioik98.github.io/xbox-game-vault/oeffentlich/</textarea><div class="grid"><section class="card"><h2>Textpaket</h2><p>Beschreibungen und Links der zehn bestehenden Katalogseiten. Keine erfundenen Angebote.</p><a class="button" href="./reichweite/beitraege.txt" download>Texte herunterladen</a></section><section class="card"><h2>Katalogfeed</h2><p>Mit einem Feedreader freiwillig abonnieren. Kein Konto und keine Anmeldung auf Game Vault.</p><a class="button" href="./reichweite/feed.xml">Feed öffnen</a></section><section class="card"><h2>Strukturierte Linkliste</h2><p>Für spätere eigene, freigegebene Integrationen. Keine fremden Geräte oder Dienste werden angesteuert.</p><a class="button" href="./reichweite/links.json" download>Linkliste herunterladen</a></section></div><p class="note">Die Dateien werden aus den tatsächlichen Seitentiteln und Beschreibungen erzeugt und bei Codeänderungen geprüft. Downloads und Feedabrufe sind keine Bestellungen, keine Zusage einer Suchmaschinenplatzierung und kein Nachweis realer Besucher.</p><p><a href="./uebersicht.html">Alle Seiten</a> · <a href="./datenschutz.html">Datenschutz</a> · <a href="./hinweise.html">Hinweise</a></p></main></body></html>'''

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--check',action='store_true');ap.add_argument('--bundle-out');args=ap.parse_args()
 if args.bundle_out:
  destination=Path(args.bundle_out);destination.mkdir(parents=True,exist_ok=True)
  with zipfile.ZipFile(destination/'game-vault-teilen.zip','w',compression=zipfile.ZIP_DEFLATED) as z:
   for file,text in sharing_files(ROOT).items():z.writestr(file.name,text)
   z.write(ROOT/'oeffentlich/og-game-vault.jpg','vorschaubild.jpg')
   z.writestr('LESEN.txt','Game Vault – Weiterempfehlungspaket. Nur auf eigenen oder freigegebenen Kanälen einsetzen. Keine automatische Verteilung, kein Tracking-Script, keine garantierten Preise oder Verkäufe. Die JSON-Datei nennt die tatsächlichen Seitenadressen.\n')
  print('Generated sharing archive; nothing sent.');return
 changes={};p=ROOT/'oeffentlich/index.html';before=p.read_text();after=change_inputs(before)
 assert protected(before)==protected(after),'Protected catalogue changed'
 if '<a href="./teilen.html">Weiterempfehlen</a>' not in after:
  after=after.replace('<a href="./uebersicht.html">Alle Seiten</a>','<a href="./uebersicht.html">Alle Seiten</a><a href="./teilen.html">Weiterempfehlen</a>',1)
 assert protected(before)==protected(after)
 changes[p]=after;changes[ROOT/'oeffentlich/teilen.html']=share_page()
 overview=ROOT/'oeffentlich/uebersicht.html';s=overview.read_text()
 if 'href="./teilen.html"' not in s:s=s.replace('</main>','<p><a href="./teilen.html">Game Vault weiterempfehlen – Texte und Katalogfeed</a></p></main>')
 changes[overview]=s
 for path in [ROOT/'index.html',*sorted((ROOT/'oeffentlich').rglob('*.html')),ROOT/'oeffentlich/teilen.html']:
  text=changes.get(path,path.read_text() if path.exists() else '')
  if path.parent.name=='plattform':
   old='onclick="this.closest(\'dialog\').close()"'
   if old in text:
    text=text.replace(old,'id="closePlatformWishlist"')
    text=text.replace("document.getElementById('wishlistDialog').showModal())</script>","document.getElementById('wishlistDialog').showModal());document.getElementById('closePlatformWishlist').addEventListener('click',()=>document.getElementById('wishlistDialog').close());</script>")
  text=BLOCK.sub('',text)
  policy=html.escape(csp(text),quote=True)
  marker='<!-- GV_SECURITY_START --><meta http-equiv="Content-Security-Policy" content="'+policy+'"><meta name="referrer" content="no-referrer"><!-- GV_SECURITY_END -->\n'
  m=re.search(r'<meta\s+charset=[^>]+>',text,re.I)
  if not m:raise ValueError('No charset '+str(path))
  text=text[:m.end()]+marker+text[m.end():]
  if re.search(r'\son[a-z]+\s*=',text,re.I):raise ValueError('Inline handler remains: '+str(path))
  changes[path]=text
 sw=ROOT/'oeffentlich/sw.js';s=sw.read_text()
 s=re.sub(r"const VERSION=PREFIX+'[^']+';","const VERSION=PREFIX+'2026-10-28-security-v1';",s)
 s=s.replace("'./datenschutz.html','./hinweise.html','./uebersicht.html'];","'./datenschutz.html','./hinweise.html','./uebersicht.html','./teilen.html'];")
 # Cache only the requested same-origin response; never cache a redirected response.
 s=s.replace("response.ok&&response.type==='basic'","response.ok&&!response.redirected&&response.type==='basic'&&new URL(response.url).pathname===url.pathname")
 changes[sw]=s
 changes.update(sharing_files(ROOT))
 drift=[str(p.relative_to(ROOT)) for p,t in changes.items() if not p.exists() or p.read_text()!=t]
 if args.check:
  if drift:raise SystemExit('Generated files need review/regeneration: '+', '.join(drift))
  print('PASS: security hashes and sharing bundle are up to date');return
 for p,t in changes.items():p.parent.mkdir(parents=True,exist_ok=True);p.write_text(t,encoding='utf-8')
 print(json.dumps({'changed':drift,'protected_catalogue_unchanged':True,'network_requests':0},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
