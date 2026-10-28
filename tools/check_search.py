#!/usr/bin/env python3
"""Validate published metadata, site scope and optional IndexNow receipt. No ranking claims."""
from __future__ import annotations
import argparse, hashlib, html, json, re, subprocess, sys, time
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlsplit, unquote
from urllib.request import Request, urlopen
from urllib.robotparser import RobotFileParser
from xml.etree import ElementTree as ET
ROOT=Path(__file__).resolve().parents[1]
BASE='https://marioik98.github.io/xbox-game-vault/'
PUBLIC=BASE+'oeffentlich/'
MARK='search-2026-10-28'
NS={'s':'http://www.sitemaps.org/schemas/sitemap/0.9'}
class Page(HTMLParser):
 def __init__(self,text:str):
  super().__init__(convert_charrefs=True);self.titles=[];self.meta={};self.canonical=[];self.links=[];self.jsonld=[];self.h1=0;self.lang='';self._title=None;self._json=None;self.feed(text)
 def handle_starttag(self,tag,attrs):
  a=dict(attrs)
  if tag=='html':self.lang=a.get('lang','')
  if tag=='h1':self.h1+=1
  if tag=='title':self._title=[]
  if tag=='meta':self.meta.setdefault(a.get('name',a.get('property','')),[]).append(a.get('content',''))
  if tag=='link' and a.get('rel')=='canonical':self.canonical.append(a.get('href'))
  if tag=='a' and a.get('href'):self.links.append(a['href'])
  if tag=='script' and a.get('type')=='application/ld+json':self._json=[]
 def handle_data(self,data):
  if self._title is not None:self._title.append(data)
  if self._json is not None:self._json.append(data)
 def handle_endtag(self,tag):
  if tag=='title' and self._title is not None:self.titles.append(''.join(self._title));self._title=None
  if tag=='script' and self._json is not None:self.jsonld.append(json.loads(''.join(self._json)));self._json=None
 def one(self,name):
  values=self.meta.get(name,[]);return values[0] if len(values)==1 else None

def disk_path(url:str)->Path:
 if not url.startswith(BASE):raise ValueError('Outside project: '+url)
 rel=unquote(urlsplit(url).path[len(urlsplit(BASE).path):]);p=ROOT/rel
 return p/'index.html' if urlsplit(url).path.endswith('/') else p

def get(url:str, attempts:int=1)->tuple[int,str,dict]:
 for n in range(attempts):
  try:
   with urlopen(Request(url,headers={'User-Agent':'GameVault-Release-Verification/1.0','Cache-Control':'no-cache'}),timeout=20) as r:
    return r.status,r.read().decode('utf-8'),dict(r.headers)
  except HTTPError as e:return e.code,e.read().decode('utf-8',errors='replace'),dict(e.headers)
  except (URLError,TimeoutError):
   if n+1==attempts:raise
   time.sleep(3)
 raise RuntimeError('Unreachable')

def all_nodes(value):
 if isinstance(value,dict):
  yield value
  for x in value.values():yield from all_nodes(x)
 elif isinstance(value,list):
  for x in value:yield from all_nodes(x)

def main()->int:
 ap=argparse.ArgumentParser();ap.add_argument('--out',default='verification/search.json');ap.add_argument('--live',action='store_true');ap.add_argument('--notify-indexnow',action='store_true');ap.add_argument('--reference');ap.add_argument('--changed-only',action='store_true');args=ap.parse_args()
 if args.notify_indexnow and not args.live:ap.error('IndexNow requires successful live verification')
 checks=[];receipt={'state':'NOT_REQUESTED'}
 def check(name,ok,detail=''):
  checks.append({'name':name,'status':'PASS' if ok else 'FAIL','detail':detail})
  if not ok:print('FAIL',name,detail,flush=True)
 try:
  sitemap=(ROOT/'sitemap.xml').read_text(encoding='utf-8');urls=[x.text for x in ET.fromstring(sitemap).findall('s:url/s:loc',NS)]
  check('Ten canonical pages in sitemap',len(urls)==10 and len(set(urls))==10)
  check('Public and root sitemap agree',sitemap==(ROOT/'oeffentlich/sitemap.xml').read_text(encoding='utf-8'))
  check('Only approved public paths',all(u.startswith(PUBLIC) and not urlsplit(u).query and not urlsplit(u).fragment for u in urls))
  titles=[];descriptions=[];content={}
  for url in urls:
   text=disk_path(url).read_text(encoding='utf-8');content[url]=text;p=Page(text);short=url.removeprefix(PUBLIC) or 'catalogue'
   check('Single descriptive title: '+short,len(p.titles)==1 and len(p.titles[0])>12)
   check('Single description: '+short,bool(p.one('description')))
   check('Self canonical: '+short,p.canonical==[url])
   check('No indexing exclusion: '+short,'noindex' not in (p.one('robots') or '').lower())
   check('German and one main heading: '+short,p.lang=='de' and p.h1==1)
   check('Release marker: '+short,p.one('gv-release')==MARK)
   check('Social title and description: '+short,p.one('og:title')==p.titles[0] and p.one('og:description')==p.one('description'))
   titles+=p.titles;descriptions.append(p.one('description'))
   broken=[]
   for href in p.links:
    target=urljoin(url,href)
    if target.startswith(BASE) and not disk_path(target).exists():broken.append(href)
   check('Internal links exist: '+short,not broken,repr(broken))
   for data in p.jsonld:
    nodes=list(all_nodes(data))
    check('Structured list counts: '+short,all(n.get('numberOfItems')==len(n.get('itemListElement',[])) for n in nodes if n.get('@type')=='ItemList'))
    check('No invented offers or ratings: '+short,not any(n.get('@type') in ('Offer','AggregateOffer','AggregateRating') for n in nodes))
  check('Ten different titles',len(set(titles))==10)
  check('Ten different descriptions',len(set(descriptions))==10)
  root=Page((ROOT/'index.html').read_text());check('Entry canonical and crawlable',root.canonical==[PUBLIC] and 'noindex' not in (root.one('robots') or ''))
  overview=Page(content[PUBLIC+'uebersicht.html']);check('Overview links to all eight platforms',sum('plattform/' in u for u in overview.links)==8)
  current=content[PUBLIC];cards=re.findall(r'<article\b[^>]*data-public-card.*?</article>',current,re.S)
  check('144 catalogue records preserved in page',len(cards)==144)
  check('Advertisements remain disabled',json.loads((ROOT/'oeffentlich/partnerbereiche.json').read_text())['status']=='INACTIVE_PENDING_APPROVAL')
  if args.reference:
   previous=subprocess.check_output(['git','show',args.reference+':oeffentlich/index.html'],cwd=ROOT).decode()
   for label,pattern in [('Catalogue',r'<article\b[^>]*data-public-card.*?</article>'),('Images',r'data:image/[^"\s]+'),('Partner section',r'<section class="section" id="partner".*?</section>')]:
    a=re.findall(pattern,previous,re.S);b=re.findall(pattern,current,re.S);check(label+' bytewise unchanged',bool(a) and a==b)
  keys=[p for p in ROOT.glob('*.txt') if re.fullmatch(r'[0-9a-f]{32}\.txt',p.name)]
  check('One project-scoped IndexNow key file',len(keys)==1)
  key=keys[0].stem;check('IndexNow key contents match',keys[0].read_text().strip()==key)
  if args.live:
   ready=False
   for attempt in range(12):
    status,text,headers=get(PUBLIC)
    if status==200 and text==content[PUBLIC]:ready=True;break
    time.sleep(10)
   check('Exact release reached public host',ready)
   if not ready:raise RuntimeError('Expected public release not yet served; no IndexNow notification')
   for url,expected in content.items():
    status,text,headers=get(url);check('LIVE HTTP 200: '+url,status==200,str(status))
    check('LIVE exact content: '+url,text==expected)
    check('LIVE no X-Robots-Tag noindex: '+url,'noindex' not in next((v.lower() for k,v in headers.items() if k.lower()=='x-robots-tag'),'') )
   for rel in ('sitemap.xml','oeffentlich/sitemap.xml','index.html','oeffentlich/sw.js',key+'.txt'):
    status,text,_=get(BASE+rel);check('LIVE exact asset: '+rel,status==200 and text==(ROOT/rel).read_text(encoding='utf-8'))
   robots_url=urljoin(BASE,'/robots.txt');status,text,_=get(robots_url)
   robots=RobotFileParser();robots.set_url(robots_url)
   if status==200:robots.parse(text.splitlines())
   elif status in (404,410):robots.allow_all=True
   else:robots.disallow_all=True
   check('Host robots permit public Googlebot crawling',all(robots.can_fetch('Googlebot',u) for u in urls),'robots HTTP '+str(status))
   check('Host robots permit public Bingbot crawling',all(robots.can_fetch('bingbot',u) for u in urls),'robots HTTP '+str(status))
   if args.notify_indexnow:
    if any(c['status']=='FAIL' for c in checks):raise RuntimeError('No notification: verification failed')
    notify=list(urls)
    if args.changed_only:
     changed=set(subprocess.check_output(['git','diff','--name-only','HEAD^','HEAD'],cwd=ROOT,text=True).splitlines())
     notify=[u for u in urls if disk_path(u).relative_to(ROOT).as_posix() in changed]
    if not notify:receipt={'state':'SKIPPED_NO_CANONICAL_PAGE_CHANGED'}
    else:
     payload={'host':urlsplit(BASE).hostname,'key':key,'keyLocation':BASE+key+'.txt','urlList':notify}
     request=Request('https://api.indexnow.org/indexnow',data=json.dumps(payload).encode(),headers={'Content-Type':'application/json; charset=utf-8','User-Agent':'GameVault-Release-Verification/1.0'},method='POST')
     try:
      with urlopen(request,timeout=30) as resp:code=resp.status;body=resp.read().decode('utf-8',errors='replace')[:2000]
     except HTTPError as err:code=err.code;body=err.read().decode('utf-8',errors='replace')[:2000]
     receipt={'state':'RECEIVED' if code==200 else 'RECEIVED_KEY_CHECK_PENDING' if code==202 else 'REJECTED','http_status':code,'urls':notify,'response':body,'indexed':False,'google_submitted':False}
     check('IndexNow delivery receipt',code in (200,202),'HTTP '+str(code)+'; receipt is not evidence of indexing')
 except Exception as exc:check('Verification execution',False,repr(exc))
 result={'checked_at_utc':datetime.now(timezone.utc).isoformat(),'mode':'LIVE' if args.live else 'LOCAL_STATIC','passed':sum(c['status']=='PASS' for c in checks),'failed':sum(c['status']=='FAIL' for c in checks),'indexnow':receipt,'checks':checks}
 out=Path(args.out);out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps({k:v for k,v in result.items() if k!='checks'},ensure_ascii=False,indent=2));return int(result['failed']>0)
if __name__=='__main__':sys.exit(main())
