#!/usr/bin/env python3
"""Exercise the real sharing UI without sending messages or contacting third parties."""
from __future__ import annotations
import argparse,json,mimetypes,shutil,sys
from pathlib import Path
from urllib.parse import unquote,urlsplit
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
BASE='https://marioik98.github.io/xbox-game-vault/'
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--out',default='verification/sharing-ui');args=ap.parse_args()
 out=Path(args.out);out.mkdir(parents=True,exist_ok=True);checks=[];errors=[];outside=[];popups=[]
 def check(name,ok,detail=''):
  checks.append({'name':name,'status':'PASS' if ok else 'FAIL','detail':detail})
  if not ok:print('FAIL',name,detail,flush=True)
 records=json.loads((ROOT/'oeffentlich/reichweite/links.json').read_text())['items']
 with sync_playwright() as pw:
  exe=shutil.which('chromium') or shutil.which('google-chrome')
  browser=pw.chromium.launch(headless=True,args=['--no-sandbox'],**({'executable_path':exe} if exe else {}));version=browser.version
  ctx=browser.new_context(service_workers='block',viewport={'width':1440,'height':1100})
  def route(r):
   u=urlsplit(r.request.url)
   if u.hostname!='marioik98.github.io' or not u.path.startswith('/xbox-game-vault/'):
    outside.append(r.request.url);r.abort();return
   p=(ROOT/unquote(u.path.removeprefix('/xbox-game-vault/'))).resolve()
   if not p.is_relative_to(ROOT):r.fulfill(status=403,body='Forbidden');return
   if p.is_dir():p=p/'index.html'
   if not p.is_file():r.fulfill(status=404,body='Missing');return
   r.fulfill(status=200,body=p.read_bytes(),content_type=mimetypes.guess_type(p.name)[0] or 'application/octet-stream')
  ctx.route('**/*',route);page=ctx.new_page();page.set_default_timeout(8000)
  page.on('pageerror',lambda e:errors.append(str(e)));page.on('popup',lambda p:popups.append(p))
  try:
   page.goto(BASE+'oeffentlich/teilen.html',wait_until='networkidle')
   check('Controls initialized under CSP',page.locator('#copyPost').is_enabled())
   check('Eleven actual catalogue destinations',page.locator('#pageChoice option').count()==len(records)==11)
   check('Preview image actually decoded',page.locator('.preview img').evaluate('(x)=>x.complete&&x.naturalWidth>0'))
   check('Downloads initially secondary',not page.locator('.advanced').evaluate('(x)=>x.open'))
   for i,r in enumerate(records):
    page.locator('#pageChoice').select_option(str(i))
    check('Preview title '+str(i),page.locator('#previewTitle').inner_text()==r['title'])
    check('Preview description '+str(i),page.locator('#previewDescription').inner_text()==r['description'])
    check('Exact target URL '+str(i),page.locator('#publicLink').input_value()==r['url'] and page.locator('#openTarget').get_attribute('href')==r['url'])
    check('Generated post '+str(i),page.locator('#postText').input_value()==r['title']+'\n\n'+r['description']+'\n\n'+r['url'])
   page.locator('#pageChoice').select_option('0');original=page.locator('#postText').input_value()
   page.evaluate("Object.defineProperty(navigator,'clipboard',{configurable:true,value:{writeText:async text=>{window.copied=text}}})")
   page.locator('#copyLink').click();page.wait_for_timeout(60)
   check('Copy URL button',page.evaluate('window.copied')==records[0]['url'])
   page.locator('#postText').fill(original+'\nMein Hinweis.');edited=page.locator('#postText').input_value()
   page.locator('#copyPost').click();page.wait_for_timeout(60)
   check('Copy preserves user-edited text',page.evaluate('window.copied')==edited)
   check('Character count updated',page.locator('#textCount').inner_text()==str(len(edited))+' / 4000 Zeichen')
   page.once('dialog',lambda d:d.dismiss());page.locator('#pageChoice').select_option('1')
   check('Cancelled change preserves user draft',page.locator('#postText').input_value()==edited and page.locator('#pageChoice').input_value()=='0')
   page.once('dialog',lambda d:d.accept());page.locator('#pageChoice').select_option('1')
   check('Confirmed change loads correct template',page.locator('#postText').input_value().startswith(records[1]['title']))
   page.locator('#postText').fill('Mein Entwurf');page.once('dialog',lambda d:d.dismiss());page.locator('#resetPost').click()
   check('Cancelled reset keeps draft',page.locator('#postText').input_value()=='Mein Entwurf')
   page.once('dialog',lambda d:d.accept());page.locator('#resetPost').click()
   check('Confirmed reset restores selected template',page.locator('#postText').input_value().startswith(records[1]['title']))
   page.evaluate("Object.defineProperty(navigator,'clipboard',{configurable:true,value:{writeText:async()=>{throw new Error('Denied')}}});document.execCommand=()=>false")
   page.locator('#copyLink').click();page.wait_for_timeout(60)
   check('Denied clipboard gives honest manual fallback','markiert' in page.locator('#shareStatus').inner_text() and 'kopiert.' not in page.locator('#shareStatus').inner_text())
   check('Fallback selects complete URL',page.locator('#publicLink').evaluate('(x)=>document.activeElement===x&&x.selectionStart===0&&x.selectionEnd===x.value.length'))
   page.locator('#copyPost').click();page.wait_for_timeout(60)
   check('Fallback selects complete post',page.locator('#postText').evaluate('(x)=>document.activeElement===x&&x.selectionStart===0&&x.selectionEnd===x.value.length'))
   page.evaluate("document.execCommand=()=>{window.legacyCopied=document.activeElement.value;return true};Object.defineProperty(navigator,'share',{configurable:true,value:undefined})")
   page.locator('#sharePost').click();page.wait_for_timeout(60)
   check('Unsupported native share uses copy',page.evaluate('window.legacyCopied')==page.locator('#postText').input_value() and 'kopiert' in page.locator('#shareStatus').inner_text())
   page.evaluate("Object.defineProperty(navigator,'share',{configurable:true,value:async data=>{window.shared=data}})")
   page.locator('#sharePost').click();page.wait_for_timeout(60)
   check('Native share receives visible edited text',page.evaluate('window.shared.text')==page.locator('#postText').input_value())
   check('Native sharing is not claimed as delivery','nicht prüfen' in page.locator('#shareStatus').inner_text())
   page.evaluate("Object.defineProperty(navigator,'share',{configurable:true,value:async()=>{throw new DOMException('Cancel','AbortError')}})")
   page.locator('#sharePost').click();page.wait_for_timeout(60)
   check('Share cancellation is handled','abgebrochen' in page.locator('#shareStatus').inner_text() and page.locator('#sharePost').is_enabled())
   page.evaluate("Object.defineProperty(navigator,'share',{configurable:true,value:async()=>{throw new Error('Denied')}})")
   page.locator('#sharePost').click();page.wait_for_timeout(60)
   check('Share denial offers copy action','nicht verfügbar' in page.locator('#shareStatus').inner_text() and page.locator('#copyPost').is_enabled())
   page.locator('#postText').fill(' ');page.locator('#sharePost').click()
   check('Empty draft not sent to share API','leer' in page.locator('#shareStatus').inner_text())
   page.locator('#postText').fill('<img src=x onerror=alert(1)>')
   check('Edited markup remains text',page.locator('#postText img').count()==0)
   page.reload(wait_until='networkidle')
   check('No undisclosed draft persistence',page.locator('#postText').input_value()==original)
   check('No storage or cookies created',page.evaluate('localStorage.length===0&&sessionStorage.length===0') and not ctx.cookies())
   for width in (320,360,390,768,1024,1440):
    page.set_viewport_size({'width':width,'height':1000})
    check('No horizontal overflow '+str(width),page.evaluate('document.documentElement.scrollWidth<=innerWidth'))
    check('Buttons fit '+str(width),page.locator('#copyPost').evaluate('(x)=>x.getBoundingClientRect().width<=innerWidth'))
   page.screenshot(path=str(out/'desktop.png'),full_page=True)
   page.set_viewport_size({'width':390,'height':844});page.screenshot(path=str(out/'mobile.png'),full_page=True)
   page.locator('summary').click();check('Advanced files expand',page.locator('.advanced').evaluate('(x)=>x.open'))
   check('Original three downloads preserved',page.locator('a[href*="reichweite/"]').count()==3)
   page.locator('#pageChoice').focus();page.keyboard.press('Tab')
   check('Keyboard reaches editable draft',page.locator('#postText').evaluate('(x)=>document.activeElement===x'))
   check('No JS exceptions',not errors,repr(errors));check('No automatic outside requests or popups',not outside and not popups,repr(outside))
   nojs=browser.new_context(java_script_enabled=False,service_workers='block');nojs.route('**/*',route);p=nojs.new_page();p.goto(BASE+'oeffentlich/teilen.html')
   check('No-JS fallback remains usable',p.locator('noscript').is_visible() and p.locator('#postText').input_value()==original and p.locator('#openTarget').get_attribute('href')==records[0]['url'])
   nojs.close()
  except Exception as exc:check('Test execution',False,repr(exc))
  finally:ctx.close();browser.close()
 result={'scope':'ISOLATED_ROUTED_BROWSER_NO_POSTING','browser':version,'passed':sum(c['status']=='PASS' for c in checks),'failed':sum(c['status']=='FAIL' for c in checks),'checks':checks,'limits':['Clipboard success and native share are mocked; actual phone apps are not tested.','No posts, ads, emails or automatic distribution were sent.']}
 (out/'results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps({k:v for k,v in result.items() if k!='checks'},ensure_ascii=False,indent=2));return int(result['failed']>0)
if __name__=='__main__':sys.exit(main())
