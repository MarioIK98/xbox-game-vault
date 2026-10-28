#!/usr/bin/env python3
"""Read-only verification of this repository's fixed public URL; no active attacks."""
from __future__ import annotations
import argparse, hashlib, json, time
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
ROOT=Path(__file__).resolve().parents[1]
BASE='https://marioik98.github.io/xbox-game-vault/'
def main():
 p=argparse.ArgumentParser();p.add_argument('--out',default='verification/live-security.json');a=p.parse_args();checks=[];headers={}
 paths=[ROOT/'index.html',*sorted((ROOT/'oeffentlich').rglob('*.html')),*sorted((ROOT/'oeffentlich/reichweite').glob('*')),ROOT/'oeffentlich/sw.js']
 def check(name,ok,detail=''):checks.append({'name':name,'status':'PASS' if ok else 'FAIL','detail':detail})
 def get(rel):
  with urlopen(Request(BASE+rel,headers={'User-Agent':'GameVault-Security-ReadOnly-Verification/1.0','Cache-Control':'no-cache'}),timeout=20) as r:
   if not r.url.startswith(BASE):raise ValueError('Unexpected redirect outside project')
   return r.status,r.read(2_000_001),{k.lower():v for k,v in r.headers.items()}
 try:
  ready=False
  for n in range(12):
   code,body,h=get('oeffentlich/index.html')
   if code==200 and body==(ROOT/'oeffentlich/index.html').read_bytes():ready=True;break
   time.sleep(10)
  if not ready:raise RuntimeError('Expected public version not served; no success claim')
  for path in paths:
   rel=path.relative_to(ROOT).as_posix();code,body,h=get(rel)
   check('Exact deployed file '+rel,code==200 and body==path.read_bytes(),'HTTP '+str(code))
   if path.suffix=='.html':
    check('CSP marker served '+rel,b'GV_SECURITY_START' in body)
    headers[rel]={k:h.get(k) for k in ('content-security-policy','x-frame-options','strict-transport-security','x-content-type-options','referrer-policy')}
 except Exception as e:check('Live verification execution',False,repr(e))
 report={'scope':'READ_ONLY_PUBLIC_HTTP_NO_ATTACKS','checked_at_utc':datetime.now(timezone.utc).isoformat(),'passed':sum(c['status']=='PASS' for c in checks),'failed':sum(c['status']=='FAIL' for c in checks),'checks':checks,'observed_headers':headers,'does_not_prove':['WAF configuration','DDoS resistance','Account security','Branch protection','Complete absence of vulnerabilities']}
 out=Path(a.out);out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(report,ensure_ascii=False,indent=2));print(json.dumps({k:v for k,v in report.items() if k not in ('checks','observed_headers')},ensure_ascii=False,indent=2));return int(report['failed']>0)
if __name__=='__main__':raise SystemExit(main())
