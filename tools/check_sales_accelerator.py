#!/usr/bin/env python3
"""Verify sales/discovery expansion without changing catalogue truth."""
from __future__ import annotations
import argparse, json, re, subprocess, sys
from pathlib import Path
from urllib.parse import urlsplit
from xml.etree import ElementTree as ET
ROOT=Path(__file__).resolve().parents[1];PUBLIC=ROOT/'oeffentlich';NS={'s':'http://www.sitemaps.org/schemas/sitemap/0.9'}
CARD=r'<article class="game" id="spiel-[\s\S]*?</article>'
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--reference',default='549e13cc3d273373d445cf6e6489f14d6c817ebb');ap.add_argument('--out',default='verification/sales-discovery.json');a=ap.parse_args()
 checks=[]
 def ck(name,ok,detail=''):checks.append({'name':name,'status':'PASS' if ok else 'FAIL','detail':detail});print('FAIL',name,detail,flush=True) if not ok else None
 current=(PUBLIC/'index.html').read_text();previous=subprocess.check_output(['git','show',a.reference+':oeffentlich/index.html'],cwd=ROOT,text=True)
 cards=re.findall(CARD,current,re.S);old=re.findall(CARD,previous,re.S)
 ck('144 catalogue cards retained',len(cards)==len(old)==144)
 ck('Catalogue card HTML unchanged',cards==old)
 ck('Partner area unchanged',re.findall(r'<section class="section" id="partner"[\s\S]*?</section>',current)==re.findall(r'<section class="section" id="partner"[\s\S]*?</section>',previous))
 ck('Embedded inventory images unchanged',re.findall(r'data:image/[^"\s]+',current)==re.findall(r'data:image/[^"\s]+',previous))
 details=sorted((PUBLIC/'spiele').glob('*.html'));ck('144 static game detail pages',len(details)==144,str(len(details)))
 uids=re.findall(r'data-uid="([^"]+)"',current);ck('144 unique inventory UIDs',len(uids)==len(set(uids))==144)
 seen=[]
 for p in details:
  s=p.read_text();m=re.search(r'Kennung ([A-Z0-9-]+)',s);uid=m.group(1) if m else ''
  seen.append(uid);ck('Detail indexable '+p.name,'noindex' not in s and '<link rel="canonical"' in s)
  ck('Detail honest status '+p.name,'Preis auf Anfrage' in s and '"@type":"Offer"' not in s)
  ck('Detail buyer path '+p.name,'?auswahl='+uid in s and '?spiel='+uid in s)
 ck('Every UID has one detail page',set(seen)==set(uids) and len(seen)==len(set(seen)))
 sm=ET.fromstring((ROOT/'sitemap.xml').read_text());urls=[n.text for n in sm.findall('s:url/s:loc',NS)]
 ck('155 canonical discovery URLs',len(urls)==len(set(urls))==155,str(len(urls)))
 ck('144 detail URLs in sitemap',sum('/oeffentlich/spiele/' in x for x in urls)==144)
 ck('Collection landing page in sitemap',any(x.endswith('/oeffentlich/spiele-sammlung.html') for x in urls))
 collection=(PUBLIC/'spiele-sammlung.html').read_text();ck('Collection page exposes full 144-game bundle',collection.count('Gesamten Bestand vormerken')==1 and '144 gebrauchte Videospiele' in collection)
 ck('Home exposes search intent and collection path','55 Xbox-360-Spiele' in current and '39 PS2-Spiele' in current and '37 PSP-Spiele' in current and 'spiele-sammlung.html' in current)
 for name,phrase,count in [('xbox-360.html','Xbox 360 Spiele gebraucht',55),('playstation-2.html','PS2 Spiele gebraucht',39),('psp.html','PSP Spiele gebraucht',37)]:
  s=(PUBLIC/'plattform'/name).read_text();ck('High-intent platform title '+name,phrase in s.split('</title>',1)[0]);ck('Platform detail links '+name,s.count('../spiele/')==count,str(s.count('../spiele/')))
 result={'scope':'CATALOGUE_PRESERVING_SALES_DISCOVERY','passed':sum(x['status']=='PASS' for x in checks),'failed':sum(x['status']=='FAIL' for x in checks),'checks':checks}
 out=Path(a.out);out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(result,ensure_ascii=False,indent=2));print(json.dumps({k:v for k,v in result.items() if k!='checks'},ensure_ascii=False,indent=2));return int(result['failed']>0)
if __name__=='__main__':sys.exit(main())
