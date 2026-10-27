#!/usr/bin/env python3
"""Regression checks for the existing public catalogue. No sales/contact data is invented."""
import argparse,functools,http.server,json,os,re,shutil,sys,tempfile,threading
from pathlib import Path
from urllib.parse import urlsplit,parse_qs,unquote
from playwright.sync_api import sync_playwright
p=argparse.ArgumentParser();p.add_argument('--root',default='.');p.add_argument('--out',default='verification');p.add_argument('--dom-only',action='store_true');a=p.parse_args()
root=Path(a.root).resolve();out=Path(a.out).resolve();out.mkdir(parents=True,exist_ok=True)
html=(root/'oeffentlich/index.html').read_text();results=[];errors=[]
def check(name,condition,detail=''):
 results.append({'name':name,'status':'PASS' if condition else 'FAIL','detail':detail})
 if not condition:print('FAIL:',name,detail,flush=True)
def skip(name,reason):results.append({'name':name,'status':'NOT_TESTED','detail':reason})
counts={'Xbox 360':55,'Original Xbox':7,'PS2':39,'PSP':37,'PS4':3,'PS5':1,'Nintendo DS':1,'PC':1}
server=None;temp=None
if not a.dom_only:
 temp=tempfile.TemporaryDirectory();os.symlink(root,Path(temp.name)/'xbox-game-vault',target_is_directory=True)
 class Handler(http.server.SimpleHTTPRequestHandler):
  def log_message(self,*args):pass
 server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Handler,directory=temp.name))
 threading.Thread(target=server.serve_forever,daemon=True).start()
 base=f'http://127.0.0.1:{server.server_port}/xbox-game-vault/oeffentlich/'
else:base='about:blank'
with sync_playwright() as pw:
 exe=shutil.which('chromium') or shutil.which('google-chrome')
 browser=pw.chromium.launch(headless=True,**({'executable_path':exe} if exe else {}),args=['--no-sandbox'])
 browser_version=browser.version;ctx=browser.new_context(viewport={'width':1440,'height':1000},accept_downloads=True)
 page=ctx.new_page();page.set_default_timeout(10000);page.on('pageerror',lambda e:errors.append(str(e)))
 def load(query=''):
  if a.dom_only:page.set_content(html)
  else:page.goto(base+query,wait_until='networkidle')
 def number():return int(page.locator('#stickyCount').inner_text())
 try:
  load();check('144 catalogue records',page.locator('[data-public-card]').count()==144)
  ids=page.locator('[data-public-card]').evaluate_all('(xs)=>xs.map(x=>x.dataset.uid)')
  check('Stable unique inventory IDs',len(set(ids))==144)
  for platform,total in counts.items():
   page.locator(f'#platformFilters [data-platform="{platform}"]').click()
   check('Filter '+platform,page.locator('[data-public-card]').count()==total)
  page.locator('#platformFilters [data-platform="Alle"]').click()
  for width in (320,360,390,768,1024,1440):
   page.set_viewport_size({'width':width,'height':900})
   check('No horizontal overflow '+str(width),page.evaluate('document.documentElement.scrollWidth<=innerWidth'))
  page.set_viewport_size({'width':390,'height':844});page.screenshot(path=str(out/'mobile.png'))
  page.set_viewport_size({'width':1440,'height':1000});page.screenshot(path=str(out/'desktop.png'))
  check('Initial pagination 12',page.locator('[data-public-card]:visible').count()==12)
  page.locator('#showMore').click();check('Pagination grows to 36',page.locator('[data-public-card]:visible').count()==36)
  page.locator('#gameSearch').fill('NO_MATCH_928372');check('No-result search',page.locator('[data-public-card]').count()==0)
  check('No-result bulk selection disabled',page.locator('#toggleFilteredGames').is_disabled())
  page.locator('#gameSearch').fill('Resident');check('Search returns matches',page.locator('[data-public-card]').count()>0)
  page.locator('#gameSearch').fill('');page.locator('#sortGames').select_option('title')
  check('Title sort',page.locator('[data-public-card]').evaluate_all('(xs)=>xs.every((x,i)=>!i||xs[i-1].dataset.title.localeCompare(x.dataset.title,"de")<=0)'))
  page.locator('#bundlePlatformGrid [data-bundle-platform="Xbox 360"]').click();check('Select whole Xbox 360 platform',number()==55)
  page.locator('#bundlePlatformGrid [data-bundle-platform="PS2"]').click();check('Combine Xbox 360 and PS2',number()==94)
  page.locator('#bundlePlatformGrid [data-bundle-platform="Xbox 360"]').click();check('Remove a platform',number()==39)
  page.locator('#selectAllGames').click();check('Select all 144',number()==144)
  page.locator('[data-public-card]:visible [data-add]').first.click();check('Remove one title',number()==143)
  page.locator('#selectAllGames').click();page.locator('#openWishlistBuilder').click()
  check('Modal contains all 144 items',page.locator('#wishlistItems [data-remove]').count()==144)
  box=page.locator('#wishlistDialog').bounding_box();page.mouse.click(box['x']+5,box['y']+5)
  check('Click inside modal padding keeps it open',page.locator('#wishlistDialog').evaluate('(d)=>d.open'))
  page.locator('#wishlistDialog').evaluate('(d)=>d.showModal()')
  page.evaluate("Object.defineProperty(navigator,'clipboard',{configurable:true,value:{writeText:async()=>{throw new Error('test denial')}}});document.execCommand=()=>{window.copyProbe={value:document.activeElement.value,inside:!!document.activeElement.closest('#wishlistDialog')};return true}")
  page.locator('#copyWishlist').click();page.wait_for_timeout(50);probe=page.evaluate('window.copyProbe')
  check('Clipboard fallback runs inside modal',probe.get('inside') is True)
  check('Clipboard fallback selects full request',len(probe.get('value',''))>1000 and '144 von 144' in probe['value'])
  page.evaluate('document.execCommand=()=>false');page.locator('#copyWishlist').click();page.wait_for_timeout(50)
  check('Copy denial exposes a usable textarea',page.locator('#manualCopy').is_visible())
  check('Manual copy preserves complete request',page.locator('#manualCopy').input_value()==probe['value'])
  with page.expect_download() as info:page.locator('#downloadWishlist').click()
  info.value.save_as(str(out/'wishlist-test.txt'));export=(out/'wishlist-test.txt').read_text()
  check('TXT export contains all selected inventory IDs',all('['+uid+']' in export for uid in ids))
  check('TXT export remains nonbinding','keine Bestellung oder Reservierung' in export)
  page.once('dialog',lambda d:d.dismiss());page.locator('#clearWishlist').click();check('Cancelled deletion preserves all items',number()==144)
  page.once('dialog',lambda d:d.accept());page.locator('#clearWishlist').click();check('Confirmed clear empties wishlist',number()==0)
  check('Empty wishlist export disabled',page.locator('#downloadWishlist').is_disabled())
  page.locator('#closeWishlist').click();page.locator('#bundlePlatformGrid [data-bundle-platform="PS2"]').click()
  page.locator('#openWishlistBuilder').click();page.mouse.click(2,2)
  check('Backdrop click closes modal',not page.locator('#wishlistDialog').evaluate('(d)=>d.open'))
  page.locator('#openWishlistBuilder').click();page.keyboard.press('Escape')
  check('Escape closes modal',not page.locator('#wishlistDialog').evaluate('(d)=>d.open'))
  if a.dom_only:
   for name in ('Browser persistence','URL import and consent','Canonical share versus selection share','Root redirect query preservation','Real service-worker offline navigation'):
    skip(name,'DOM-only sandbox: no hosted HTTP navigation; requires CI/live verification')
  else:
   load();check('Wishlist survives reload',number()==39)
   load('?auswahl='+ids[0]+','+ids[1]+'&utm_source=qa')
   check('Shared selection is not silently imported',number()==39 and page.locator('#sharedSelectionBanner').is_visible())
   page.once('dialog',lambda d:d.dismiss());page.locator('#importSharedWishlist').click();check('Cancel shared import keeps original wishlist',number()==39)
   page.once('dialog',lambda d:d.accept());page.locator('#importSharedWishlist').click();check('Confirmed import replaces wishlist',number()==2)
   check('Imported selection removed from URL','auswahl=' not in page.url)
   page.locator('#closeWishlist').click();load('?auswahl=%3Cscript%3E')
   check('Malformed selection rejected',page.locator('#importSharedWishlist').is_hidden() and number()==2)
   load('?auswahl='+ids[0]+',UNKNOWN_ID')
   check('Unknown selection IDs reported','1 unbekannte' in page.locator('#sharedSelectionDescription').inner_text())
   page.locator('#dismissSharedWishlist').click();check('Dismiss import preserves data',number()==2 and 'auswahl=' not in page.url)
   load('?auswahl='+ids[0]+'&utm_source=qa#spiele')
   page.evaluate("Object.defineProperty(navigator,'share',{configurable:true,value:undefined});Object.defineProperty(navigator,'clipboard',{configurable:true,value:{writeText:async(v)=>{window.copied=v}}})")
   page.locator('#shareLink').click();page.wait_for_timeout(100);shared=page.evaluate('window.copied')
   check('Website share excludes selection and tracking parameters',shared==base)
   page.locator('#openWishlistBuilder').click();page.locator('#copyWishlistLink').click();page.wait_for_timeout(100)
   selection=page.evaluate('window.copied');q=parse_qs(urlsplit(selection).query)
   check('Selection link contains only inventory IDs',set(q)=={'auswahl'} and len(q['auswahl'][0].split(','))==2)
   page.locator('#closeWishlist').click()
   page.goto(base.replace('/oeffentlich/','/')+'?auswahl='+ids[0]+'#spiele');page.wait_for_load_state('networkidle')
   check('Root redirect preserves shared selection',urlsplit(page.url).path.endswith('/oeffentlich/') and 'auswahl=' in page.url)
   page.evaluate("navigator.serviceWorker.register('./sw.js',{scope:'./'}).then(()=>navigator.serviceWorker.ready)")
   page.reload(wait_until='networkidle');page.wait_for_function('navigator.serviceWorker.controller!==null')
   ctx.set_offline(True)
   for route,title in [('datenschutz.html','Datenschutzhinweise'),('hinweise.html','Hinweise zu Spielen'),('uebersicht.html','Alle Seiten auf einen Blick')]:
    page.goto(base+route);check('Offline correct page '+route,title in page.locator('body').inner_text())
   page.goto(base+'not-in-release.html');check('Unknown offline route returns honest error','offline nicht gespeichert' in page.locator('body').inner_text())
   ctx.set_offline(False);load()
  check('No JavaScript exceptions',not errors,'; '.join(errors))
  for f in sorted((root/'oeffentlich').rglob('*.html')):
   source=f.read_text();page.set_content(source)
   check('German document '+str(f.relative_to(root)),page.locator('html').get_attribute('lang')=='de')
   broken=[]
   for href in page.locator('a[href]').evaluate_all('(as)=>as.map(a=>a.getAttribute("href"))'):
    u=urlsplit(href)
    if u.scheme or href.startswith('//') or not u.path:continue
    target=(f.parent/unquote(u.path)).resolve()
    if u.path.endswith('/'):target=target/'index.html'
    if not target.exists():broken.append(href)
   check('Local links resolve '+str(f.relative_to(root)),not broken,repr(broken))
  page.set_content((root/'oeffentlich/uebersicht.html').read_text())
  check('Overview has eight platform links',page.locator('a[href*="plattform/"]').count()==8)
  for w in (320,390,1440):
   page.set_viewport_size({'width':w,'height':900});check('Overview layout '+str(w),page.evaluate('document.documentElement.scrollWidth<=innerWidth'))
  page.screenshot(path=str(out/'overview.png'))
 except Exception as e:
  check('Test suite execution',False,repr(e))
 finally:
  ctx.close();browser.close()
  if server:server.shutdown()
  if temp:temp.cleanup()
report={'scope':'LOCAL_DOM_ONLY' if a.dom_only else 'HTTP_BROWSER_AND_SERVICE_WORKER','browser':browser_version,'python':sys.version.split()[0],
 'passed':sum(x['status']=='PASS' for x in results),'failed':sum(x['status']=='FAIL' for x in results),'not_tested':sum(x['status']=='NOT_TESTED' for x in results),'checks':results}
(out/'results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
print(json.dumps({k:v for k,v in report.items() if k!='checks'},ensure_ascii=False,indent=2))
sys.exit(1 if report['failed'] else 0)
