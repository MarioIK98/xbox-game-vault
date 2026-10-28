#!/usr/bin/env python3
"""Fail-closed regression test for a static hosting release and exact public allowlist."""
from __future__ import annotations
import hashlib, json, re, sys
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit, unquote
from xml.etree import ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
DIST=ROOT/'dist'
sys.path.insert(0,str(ROOT/'tools'))
from build_hosted_release import build, ROOT_FILES, PUBLIC_FILES, validated_origin
checks=[]
def ck(name,ok,detail=''):
 checks.append({'name':name,'pass':bool(ok),'detail':detail})
 if not ok:print('FAIL',name,detail,flush=True)
class Links(HTMLParser):
 def __init__(self):super().__init__();self.links=[]
 def handle_starttag(self,tag,attrs):
  d=dict(attrs)
  if tag in ('a','link','script','img','source'):
   x=d.get('href') if tag in ('a','link') else d.get('src')
   if x:self.links.append(x)

def main():
 # A test on the production build must never implicitly create a real deployment.
 try:build('production','https://gamevault.example/',DIST)
 except ValueError as e:ck('Commercial deployment fails closed without approval','STOP' in str(e))
 else:ck('Commercial deployment fails closed without approval',False)
 for hostile in ('http://example.org/','https://user:pass@example.org/','https://example.org/path','https://example.org/?x=1'):
  try:validated_origin(hostile)
  except ValueError:ck('Invalid production origin rejected '+hostile,True)
  else:ck('Invalid production origin rejected '+hostile,False)
 try:build('preview','https://example.org/',DIST)
 except ValueError:ck('Preview cannot impersonate production origin',True)
 else:ck('Preview cannot impersonate production origin',False)
 # A symlinked output must never cause recursive removal of its external target.
 import tempfile, shutil
 if DIST.is_symlink():raise RuntimeError('Unexpected symlink in test worktree')
 if DIST.exists():shutil.rmtree(DIST)
 with tempfile.TemporaryDirectory() as outside:
  sentinel=Path(outside)/'must-survive';sentinel.write_text('untouched')
  DIST.symlink_to(outside,target_is_directory=True)
  try:build('preview',None,DIST)
  except ValueError:ck('Symlinked output directory rejected',True)
  else:ck('Symlinked output directory rejected',False)
  ck('Symlink target preserved',sentinel.read_text()=='untouched')
  DIST.unlink()
 # A positive production-path fixture verifies portability without publishing or changing approvals.
 from unittest.mock import patch
 with patch('build_hosted_release.approved_production',return_value=None):
  production=build('production','https://gamevault.example/',DIST)
 ck('Test fixture builds production-shaped file set',production['production_ready'] and len(production['files'])==len(ROOT_FILES)+len(PUBLIC_FILES)+1)
 check_pages=('index.html','oeffentlich/index.html','oeffentlich/teilen.html','oeffentlich/spiele-sammlung.html','oeffentlich/spiele/x360-001-minecraft-xbox-360-edition.html','oeffentlich/plattform/xbox-360.html','sitemap.xml','oeffentlich/reichweite/links.json')
 ck('Authorized fixture rewrites all public origins',all('https://marioik98.github.io/xbox-game-vault/' not in (DIST/x).read_text() for x in check_pages))
 ck('Authorized fixture sets the new canonical', '<link rel="canonical" href="https://gamevault.example/oeffentlich/"' in (DIST/'oeffentlich/index.html').read_text())
 ck('Authorized fixture does not add preview noindex', 'content="noindex,nofollow"' not in (DIST/'oeffentlich/index.html').read_text())
 ck('Authorized fixture refreshes CSP hashes', 'GV_SECURITY_START' in (DIST/'oeffentlich/teilen.html').read_text())
 ck('Authorized fixture writes site-root robots', 'Sitemap: https://gamevault.example/sitemap.xml' in (DIST/'robots.txt').read_text())
 report=build('preview',None,DIST)
 ck('Build is explicitly a noindex preview',report['mode']=='preview' and not report['indexable'] and not report['production_ready'])
 expected={*ROOT_FILES,*('oeffentlich/'+name for name in PUBLIC_FILES),'robots.txt','build-manifest.json'}
 actual={str(x.relative_to(DIST)) for x in DIST.rglob('*') if x.is_file()}
 ck('Only allowlisted public files are present',actual==expected,repr(sorted(actual^expected)))
 ck('Build never publishes historical HTML backups',not any('backup' in s or 'market-research' in s for s in actual))
 ck('Build never publishes code, internal approvals, or project notes',not any(s.startswith(('tools/','release/','.github/')) or 'partnerbereiche' in s or s=='AGENTS.md' for s in actual))
 ck('Preview root robots disables crawlers',(DIST/'robots.txt').read_text().strip()=='User-agent: *\nDisallow: /')
 ck('Preview path robots disables crawlers',(DIST/'oeffentlich/robots.txt').read_text()==(DIST/'robots.txt').read_text())
 htmls=list(DIST.rglob('*.html'))
 ck('All current production HTML documents included',len(htmls)==1+sum(1 for name in PUBLIC_FILES if name.endswith('.html')),str(len(htmls)))
 for file in htmls:
  s=file.read_text();rel=file.relative_to(DIST).as_posix()
  ck('Robots noindex '+rel,len(re.findall(r'<meta\s+name=["\']robots["\']\s+content=["\']noindex,nofollow["\']\s*>',s,re.I))==1)
  ck('CSP present once '+rel,s.count('GV_SECURITY_START')==1 and 'script-src-attr &#x27;none&#x27;' in s)
  ck('No inline event handler '+rel,not re.search(r'\son[a-z]+\s*=',s,re.I))
  parser=Links();parser.feed(s)
  broken=[]
  for href in parser.links:
   if href.startswith(('http:','https:','mailto:','tel:','data:','javascript:','#','//')):continue
   path=urlsplit(href).path
   if not path:continue
   target=(file.parent/unquote(path)).resolve()
   if not target.is_relative_to(DIST):broken.append('outside:'+href);continue
   if path.endswith('/'):target=target/'index.html'
   if not target.exists():broken.append(href)
  ck('Internal static links '+rel,not broken,repr(broken))
 contents=(DIST/'oeffentlich/index.html').read_text()
 source=(ROOT/'oeffentlich/index.html').read_text()
 cards=r'<article\b[^>]*data-public-card.*?</article>'
 ck('144 existing game entries preserved',len(re.findall(cards,contents,re.S))==144)
 ck('Game card HTML byte-identical',re.findall(cards,contents,re.S)==re.findall(cards,source,re.S))
 images=r'data:image/[^"\s]+'
 ck('Embedded game images retained',re.findall(images,contents,re.S)==re.findall(images,source,re.S))
 ck('Partner HTML unchanged',re.findall(r'<section class="section" id="partner".*?</section>',contents,re.S)==re.findall(r'<section class="section" id="partner".*?</section>',source,re.S))
 ck('All 8 platform pages retained',len(list((DIST/'oeffentlich/plattform').glob('*.html')))==8)
 ck('All 144 game detail pages retained',len(list((DIST/'oeffentlich/spiele').glob('*.html')))==144)
 ck('RSS retained',(DIST/'oeffentlich/reichweite/feed.xml').is_file())
 ck('Sitemap retains 155 approved canonical pages',len(ET.fromstring((DIST/'sitemap.xml').read_text()).findall('{http://www.sitemaps.org/schemas/sitemap/0.9}url'))==155)
 manifest=json.loads((DIST/'build-manifest.json').read_text())
 ck('Manifest records all distributable files',len(manifest['files'])==len(actual)-1)
 ck('Manifest SHA256 digest matches output',all(hashlib.sha256((DIST/r['path']).read_bytes()).hexdigest()==r['sha256'] for r in manifest['files']))
 yaml=(ROOT/'render.yaml').read_text(encoding='utf-8')
 for needle in ('runtime: static','staticPublishPath: ./dist','--mode preview --dest dist','name: X-Content-Type-Options','name: Content-Security-Policy','frame-ancestors','name: X-Frame-Options','name: X-Robots-Tag','value: "noindex, nofollow"','name: Permissions-Policy'):
  ck('Render Blueprint '+needle,needle in yaml)
 ck('No live domain modified by this build',not (ROOT/'dist/index.html').is_symlink())
 summary={'mode':'OFFLINE_PREVIEW_SECURITY_GATES','passed':sum(x['pass'] for x in checks),'failed':sum(not x['pass'] for x in checks),'checks':checks}
 (DIST/'test-report.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({k:v for k,v in summary.items() if k!='checks'},ensure_ascii=False,indent=2))
 return 1 if summary['failed'] else 0
if __name__=='__main__':sys.exit(main())
