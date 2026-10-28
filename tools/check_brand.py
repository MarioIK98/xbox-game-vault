#!/usr/bin/env python3
"""Publish the consistent GAME VAULT display name; leave URLs and catalogue facts alone."""
from __future__ import annotations
import argparse, re, subprocess, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PUBLIC=ROOT/'oeffentlich'
PAGES=[ROOT/'index.html',*sorted(PUBLIC.rglob('*.html'))]
FILES=[*PAGES,PUBLIC/'site.webmanifest']
GENERATOR=ROOT/'tools/prepare_security_release.py'
PROTECTED={
 'catalogue':re.compile(r'<article\b[^>]*data-public-card.*?</article>',re.S),
 'partner':re.compile(r'<section class="section" id="partner".*?</section>',re.S),
 'embedded_images':re.compile(r'data:image/[^"\s]+',re.S)
}
def norm(value:str)->str:
 value=value.replace('Game Vault','GAME VAULT')
 value=value.replace('Marios privater Sammlung','privater Spielesammlung')
 value=value.replace('Marios privater Katalog','ein privater Katalog')
 value=value.replace('Marios privater Spielekatalog','privater Spielekatalog')
 return value

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--apply',action='store_true');args=ap.parse_args()
 errors=[];changes=[];edits={}
 for file in [*FILES,GENERATOR]:
  before=file.read_text(encoding='utf-8');after=norm(before)
  if file==GENERATOR:after=after.replace('2026-10-28-sharing-ui-v1','2026-10-28-brand-v1')
  if file==PUBLIC/'index.html':
   for name,pattern in PROTECTED.items():
    if pattern.findall(before)!=pattern.findall(after):errors.append('Protected '+name+' changed')
  if before!=after:
   changes.append(file.relative_to(ROOT).as_posix());edits[file]=after
 if errors:raise SystemExit('STOP: '+', '.join(errors))
 if args.apply:
  for file,after in edits.items():file.write_text(after,encoding='utf-8')
  subprocess.run([sys.executable,str(GENERATOR)],cwd=ROOT,check=True)
  print('GAME VAULT branding updated. Changes:',', '.join(changes));return
 for file in [*FILES,*sorted((PUBLIC/'reichweite').glob('*'))]:
  if 'Game Vault' in file.read_text(encoding='utf-8'):errors.append('Unnormalized brand: '+file.relative_to(ROOT).as_posix())
 if '2026-10-28-brand-v1' not in (PUBLIC/'sw.js').read_text(encoding='utf-8'):errors.append('Service-worker cache version not bumped')
 if changes:errors.append('Source brand drift: '+', '.join(changes))
 if errors:raise SystemExit('FAIL: '+', '.join(errors))
 print('PASS: GAME VAULT branding consistent on current public pages and data')
if __name__=='__main__':main()
