#!/usr/bin/env python3
"""Verify GAME VAULT direct inquiries with an isolated mocked provider; no external email."""
from __future__ import annotations
import argparse, html, json, mimetypes, sys
from pathlib import Path
from urllib.parse import urlsplit, unquote
from playwright.sync_api import sync_playwright
from prepare_security_release import csp, BLOCK

ROOT=Path(__file__).resolve().parents[1]
BASE='https://gamevault.test/xbox-game-vault/oeffentlich/'
FAKE='mabcdef12'

def configured(source):
    page=source.replace('<meta name="gv-inquiry-form" content="">','<meta name="gv-inquiry-form" content="'+FAKE+'">',1)
    assert page!=source
    page=BLOCK.sub('',page,count=1)
    marker='<!-- GV_SECURITY_START --><meta http-equiv="Content-Security-Policy" content="'+html.escape(csp(page),quote=True)+'"><meta name="referrer" content="no-referrer"><!-- GV_SECURITY_END -->\n'
    return page.replace('<meta charset="utf-8">','<meta charset="utf-8">'+marker,1)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--out',default='verification/direct-inquiry.json')
    args=ap.parse_args()
    checks=[]
    def ck(name,ok,detail=''):
        checks.append({'name':name,'status':'PASS' if ok else 'FAIL','detail':detail})
        if not ok:print('FAIL',name,detail,flush=True)
    source=(ROOT/'oeffentlich/index.html').read_text(encoding='utf-8')
    ck('Missing form ID is an intentional off switch','<meta name="gv-inquiry-form" content="">' in source)
    ck('Unconfigured inquiry area is hidden','id="gvInquirySection" hidden' in source)
    ck('Unconfigured CSP does not connect to Formspree','connect-src &#x27;self&#x27;;' in source)
    ck('No public recipient email in catalogue','mailto:' not in source)
    requests=[];other=[];errors=[]
    with sync_playwright() as pw:
        browser=pw.chromium.launch(headless=True,args=['--no-sandbox'])
        ctx=browser.new_context(service_workers='block',viewport={'width':390,'height':844})
        enabled=False
        provider='success'
        def route(rt):
            nonlocal enabled,provider
            r=rt.request
            url=urlsplit(r.url)
            if url.hostname=='formspree.io':
                requests.append({'url':r.url,'method':r.method,'body':r.post_data or ''})
                headers={'Access-Control-Allow-Origin':'*','Content-Type':'application/json'}
                if provider=='success':rt.fulfill(status=200,body='{"ok":true}',headers=headers)
                elif provider=='rate':rt.fulfill(status=429,body='{"error":"rate limit"}',headers=headers)
                elif provider=='invalid':rt.fulfill(status=422,body='{"errors":[{"message":"invalid"}]}',headers=headers)
                else:rt.abort('failed')
                return
            if url.hostname!='gamevault.test' or not url.path.startswith('/xbox-game-vault/'):
                other.append(r.url)
                rt.abort('blockedbyclient')
                return
            p=(ROOT/unquote(url.path.removeprefix('/xbox-game-vault/'))).resolve()
            if not p.is_relative_to(ROOT):rt.fulfill(status=403,body='Forbidden');return
            if p.is_dir():p=p/'index.html'
            if not p.is_file():rt.fulfill(status=404,body='Not found');return
            if enabled and p==ROOT/'oeffentlich/index.html':
                rt.fulfill(status=200,content_type='text/html; charset=utf-8',body=configured(source))
            else:
                rt.fulfill(status=200,body=p.read_bytes(),content_type=mimetypes.guess_type(p.name)[0] or 'application/octet-stream')
        ctx.route('**/*',route)
        page=ctx.new_page()
        page.set_default_timeout(10000)
        page.on('pageerror',lambda e:errors.append(str(e)))
        try:
            page.goto(BASE,wait_until='load')
            page.locator('#openWishlistBuilder').click()
            ck('No form without a verified delivery endpoint',page.locator('#gvInquirySection').is_hidden())
            ck('No delivery during normal browsing',len(requests)==0 and not other)
            page.locator('#closeWishlist').click()
            enabled=True
            page.goto(BASE,wait_until='load')
            page.locator('#openWishlistBuilder').click()
            ck('Valid form ID reveals direct-inquiry form',page.locator('#gvInquirySection').is_visible())
            ck('Empty selection cannot be sent',page.locator('#gvSendInquiry').is_disabled())
            page.locator('#closeWishlist').click()
            page.locator('#selectAllGames').click()
            page.locator('#openWishlistBuilder').click()
            ck('All 144 catalogue items selectable',page.locator('#wishlistItems button[data-remove]').count()==144)
            page.wait_for_function("!document.querySelector('#gvSendInquiry').disabled")
            page.locator('#gvBuyerEmail').fill('not-an-email')
            page.locator('#gvSendInquiry').click()
            ck('Buyer email is validated before sending',len(requests)==0 and not page.locator('#gvBuyerEmail').evaluate('(e)=>e.checkValidity()'))
            page.locator('#gvBuyerName').fill('Test Person')
            page.locator('#gvBuyerEmail').fill('buyer@example.org')
            page.locator('#gvBuyerNote').fill('Bitte einen Paketpreis mitteilen.')
            ck('No personal data transmitted before explicit click',len(requests)==0)
            page.locator('#gvSendInquiry').click()
            page.wait_for_function("document.querySelector('#gvInquiryStatus').textContent.includes('angenommen')")
            ck('Exactly one POST to approved form endpoint',len(requests)==1 and requests[0]['url']=='https://formspree.io/f/'+FAKE and requests[0]['method']=='POST')
            expected=['PS2-001','PSP-031','X360-001','GV-PS5-FOTO-001']
            ck('All platform IDs, response email and free text are submitted',all(uid in requests[0]['body'] for uid in expected) and 'buyer@example.org' in requests[0]['body'] and 'Paketpreis' in requests[0]['body'])
            ck('Duplicate click disabled after accepted selection',page.locator('#gvSendInquiry').is_disabled())
            ck('Successful send leaves existing wishlist intact',page.locator('#wishlistItems button[data-remove]').count()==144)
            page.locator('#gvBuyerNote').fill('Weitere Frage')
            provider='rate'
            page.locator('#gvSendInquiry').click()
            page.wait_for_function("document.querySelector('#gvInquiryStatus').textContent.includes('zu viele Anfragen')")
            ck('429 rate limiting gives no success',len(requests)==2 and page.locator('#gvSendInquiry').is_enabled())
            page.locator('#gvBuyerNote').fill('Nächste Frage')
            provider='invalid'
            page.locator('#gvSendInquiry').click()
            page.wait_for_function("document.querySelector('#gvInquiryStatus').textContent.includes('prüfe')")
            ck('422 validation error gives no success',len(requests)==3 and page.locator('#gvSendInquiry').is_enabled())
            page.locator('#gvBuyerNote').fill('Letzte Frage')
            provider='offline'
            page.locator('#gvSendInquiry').click()
            page.wait_for_function("document.querySelector('#gvInquiryStatus').textContent.includes('nicht bestätigt')")
            ck('Network failure handled without erasing selection',len(requests)==4 and page.locator('#gvSendInquiry').is_enabled() and page.locator('#wishlistItems button[data-remove]').count()==144)
            ck('No browser script errors or other external requests',not errors and not other,repr(errors+other))
        except Exception as exc:
            ck('Browser test execution',False,repr(exc))
        finally:
            ctx.close()
            browser.close()
    report={'scope':'MOCKED_DIRECT_INQUIRY_NO_REAL_EMAIL','passed':sum(x['status']=='PASS' for x in checks),'failed':sum(x['status']=='FAIL' for x in checks),'checks':checks}
    out=Path(args.out);out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k!='checks'},ensure_ascii=False,indent=2))
    return int(report['failed']>0)

if __name__=='__main__':sys.exit(main())
