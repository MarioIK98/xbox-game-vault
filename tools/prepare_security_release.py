#!/usr/bin/env python3
"""Bounded GAME VAULT hardening and opt-in sharing assets. No network, sending or WAF claims."""
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
 return "; ".join(["default-src 'none'","base-uri 'none'","object-src 'none'","frame-src 'none'","form-action 'none'","script-src "+(' '.join(hashes) or "'none'"),"script-src-attr 'none'","style-src 'self' 'unsafe-inline'","img-src 'self' data:","font-src 'self'","connect-src 'self'" + (" https://formspree.io" if re.search(r'<meta name="gv-inquiry-form" content="[a-z0-9]{8,20}"',text) else ""),"manifest-src 'self'","worker-src 'self'","media-src 'none'"])

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
  if '/spiele/' in url:continue
  rel=url.removeprefix(PUBLIC) or 'index.html'
  path=(root/'oeffentlich'/rel).resolve()
  if not path.is_relative_to((root/'oeffentlich').resolve()):raise ValueError('Outside public directory')
  p=Meta(path.read_text());records.append({'title':p.title,'description':p.description,'url':url})
 payload={'purpose':'Opt-in sharing material, not automatically distributed','automatic_sending':False,'ranking_guarantee':False,'items':records}
 text='GAME VAULT · FREIWILLIG TEILEN\n\nNur selbst veröffentlichen oder an Personen senden, die diese Information wünschen.\nKeine garantierte Verfügbarkeit, keine erfundenen Preise, keine aktiven Partnerangebote.\n\n'
 for r in records:text+=r['title']+'\n'+r['description']+'\n'+r['url']+'\n\n'
 rss=ET.Element('rss',version='2.0');ch=ET.SubElement(rss,'channel')
 for k,v in [('title','GAME VAULT – öffentliche Katalogseiten'),('link',PUBLIC),('description','Freiwillig abonnierbarer Katalogfeed. Keine Preis- oder Verfügbarkeitsgarantie.'),('language','de-DE')]:ET.SubElement(ch,k).text=v
 for r in records:
  item=ET.SubElement(ch,'item')
  for k,v in [('title',r['title']),('link',r['url']),('description',r['description'])]:ET.SubElement(item,k).text=v
  ET.SubElement(item,'guid',isPermaLink='true').text=r['url']
 ET.indent(rss)
 return {root/'oeffentlich/reichweite/links.json':json.dumps(payload,ensure_ascii=False,indent=2)+'\n',root/'oeffentlich/reichweite/beitraege.txt':text,root/'oeffentlich/reichweite/feed.xml':'<?xml version="1.0" encoding="utf-8"?>\n'+ET.tostring(rss,encoding='unicode')+'\n'}

def share_page()->str:
 # The existing public HTML is the editable design source, not a second application.
 records=json.loads(sharing_files(ROOT)[ROOT/'oeffentlich/reichweite/links.json'])['items']
 first=records[0]
 labels={'':'Gesamter Spielekatalog','uebersicht.html':'Alle Seiten im Überblick',
  'nintendo-ds.html':'Nintendo DS','original-xbox.html':'Original Xbox',
  'pc.html':'PC','spiele-sammlung.html':'Ganze Spielesammlung','playstation-2.html':'PlayStation 2','playstation-4.html':'PlayStation 4',
  'playstation-5.html':'PlayStation 5','psp.html':'PlayStation Portable (PSP)','xbox-360.html':'Xbox 360'}
 options=''.join('<option value="'+str(i)+'">'+html.escape(labels.get(r['url'].removeprefix(PUBLIC).split('/')[-1],r['title']))+'</option>' for i,r in enumerate(records))
 post=first['title']+'\n\n'+first['description']+'\n\n'+first['url']
 values=[('select','pageChoice',options),('textarea','postText',html.escape(post)),
  ('textarea','publicLink',html.escape(first['url'])),('h2','previewTitle',html.escape(first['title'])),
  ('p','previewDescription',html.escape(first['description'])),
  ('span','textCount',str(len(post))+' / 4000 Zeichen'),
  ('script','shareData',json.dumps(records,ensure_ascii=False).replace('<',r'\u003c'))]
 text=(ROOT/'oeffentlich/teilen.html').read_text(encoding='utf-8')
 for tag,ident,value in values:
  pattern=r'(<'+tag+r'\b[^>]*\bid="'+ident+r'"[^>]*>).*?(</'+tag+r'>)'
  text,count=re.subn(pattern,lambda m:m[1]+value+m[2],text,flags=re.S)
  if count!=1:raise ValueError('Sharing page element missing or duplicated: '+ident)
 text,count=re.subn(r'(<a\b[^>]*\bid="openTarget"[^>]*\bhref=")[^"]*(")',lambda m:m[1]+html.escape(first['url'],quote=True)+m[2],text)
 if count!=1:raise ValueError('Sharing target link missing or duplicated')
 return text


def main():
 ap=argparse.ArgumentParser();ap.add_argument('--check',action='store_true');ap.add_argument('--bundle-out');args=ap.parse_args()
 if args.bundle_out:
  destination=Path(args.bundle_out);destination.mkdir(parents=True,exist_ok=True)
  with zipfile.ZipFile(destination/'game-vault-teilen.zip','w',compression=zipfile.ZIP_DEFLATED) as z:
   for file,text in sharing_files(ROOT).items():z.writestr(file.name,text)
   z.write(ROOT/'oeffentlich/og-game-vault.jpg','vorschaubild.jpg')
   z.writestr('LESEN.txt','GAME VAULT – Weiterempfehlungspaket. Nur auf eigenen oder freigegebenen Kanälen einsetzen. Keine automatische Verteilung, kein Tracking-Script, keine garantierten Preise oder Verkäufe. Die JSON-Datei nennt die tatsächlichen Seitenadressen.\n')
  print('Generated sharing archive; nothing sent.');return
 changes={};p=ROOT/'oeffentlich/index.html';before=p.read_text();after=change_inputs(before)
 assert protected(before)==protected(after),'Protected catalogue changed'
 if '<a href="./teilen.html">Weiterempfehlen</a>' not in after:
  after=after.replace('<a href="./uebersicht.html">Alle Seiten</a>','<a href="./uebersicht.html">Alle Seiten</a><a href="./teilen.html">Weiterempfehlen</a>',1)
 assert protected(before)==protected(after)
 changes[p]=after;changes[ROOT/'oeffentlich/teilen.html']=share_page()
 overview=ROOT/'oeffentlich/uebersicht.html';s=overview.read_text()
 if 'href="./teilen.html"' not in s:s=s.replace('</main>','<p><a href="./teilen.html">GAME VAULT weiterempfehlen – Texte und Katalogfeed</a></p></main>')
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
 s=re.sub(r"const VERSION=PREFIX\+'[^']+';","const VERSION=PREFIX+'2026-10-28-sales-v2';",s)
 s=s.replace("'./datenschutz.html','./hinweise.html','./uebersicht.html'];","'./datenschutz.html','./hinweise.html','./uebersicht.html','./teilen.html'];")
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
