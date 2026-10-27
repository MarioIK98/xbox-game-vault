#!/usr/bin/env python3
"""Apply a bounded Game Vault repair; never change inventory, photos or pricing."""
from pathlib import Path
import hashlib,re,sys
root=Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).resolve().parents[1]
p=root/'oeffentlich/index.html'
original=p.read_text(encoding='utf-8')
marker='/* Game Vault buyer-flow repair 2026-10-27 */'
if marker in original:
 if "function list(){\n $('manualCopy')?.remove();" not in original:
  assert original.count('function list(){')==1
  p.write_text(original.replace('function list(){',"function list(){\n $('manualCopy')?.remove();",1),encoding='utf-8')
  print('Removed stale manual-copy data after wishlist edits.')
 else:print('Buyer-flow repair already present; no rewrite.')
 sys.exit(0)
blob=hashlib.sha1(b'blob '+str(len(original.encode())).encode()+b'\0'+original.encode()).hexdigest()
if blob!='40aa4952f1afa79668891ad147ad0239a4e124b2':
 raise SystemExit('STOP: source file differs from the inspected snapshot. Review before applying.')
s=original
assert s.count('function list(){')==1
s=s.replace('function list(){',"function list(){\n $('manualCopy')?.remove();",1)
old="$('wishlistDialog').addEventListener('click',e=>{if(e.target===$('wishlistDialog'))$('wishlistDialog').close();});"
new="""/* Game Vault buyer-flow repair 2026-10-27 */
$('wishlistDialog').addEventListener('click',e=>{
 const dialog=$('wishlistDialog');if(e.target!==dialog)return;
 const r=dialog.getBoundingClientRect();
 if(e.clientX<r.left||e.clientX>r.right||e.clientY<r.top||e.clientY>r.bottom)dialog.close();
});"""
assert s.count(old)==1;s=s.replace(old,new)
start=s.index('async function copyText(value)')
end=s.index("$('copyWishlist').addEventListener",start)
s=s[:start]+"""async function copyText(value){
 const previous=document.activeElement;
 const obsolete=$('manualCopy');if(obsolete)obsolete.remove();
 if(navigator.clipboard&&window.isSecureContext){
  try{await navigator.clipboard.writeText(value);return true;}catch(_){}
 }
 // A modal dialog makes the rest of the document inert. Copy inside the dialog.
 const parent=$('wishlistDialog').open?$('wishlistDialog'):document.body;
 const field=document.createElement('textarea');field.value=value;
 field.setAttribute('readonly','');field.setAttribute('aria-label','Text zum manuellen Kopieren');
 field.style.cssText='position:fixed;top:-1000px;left:0';parent.append(field);
 field.focus();field.select();field.setSelectionRange(0,value.length);
 let ok=false;try{ok=document.execCommand('copy')}catch(_){}
 if(ok){field.remove();if(previous&&previous.isConnected)previous.focus();return true;}
 // Never claim success when clipboard access is denied. Keep the complete text available.
 field.id='manualCopy';field.rows=8;
 field.style.cssText='display:block;width:100%;box-sizing:border-box;margin:12px 0;padding:12px;color:inherit;background:#111a2f;border:1px solid #b5c5df;border-radius:8px';
 if(parent===document.body)$('shareStatus').insertAdjacentElement('afterend',field);
 field.focus();field.select();return false;
}
"""+s[end:]
old="const u=new URL(location.href);u.searchParams.delete('spiel');u.searchParams.delete('plattform');"
new="const u=new URL(location.href);u.search='';"
assert s.count(old)==1;s=s.replace(old,new)
old="const url=/^https?:$/.test(location.protocol)?location.href.split('#')[0]:'';"
new="const siteUrl=/^https?:$/.test(location.protocol)?new URL(location.href):null;if(siteUrl){siteUrl.search='';siteUrl.hash='';}const url=siteUrl?siteUrl.toString():'';"
assert s.count(old)==1;s=s.replace(old,new)
old='<div class="footer-links"><a href="./datenschutz.html">'
new='<div class="footer-links"><a href="./uebersicht.html">Alle Seiten</a><a href="./datenschutz.html">'
assert s.count(old)==1;s=s.replace(old,new)
for pattern in [r'<article\b[^>]*data-public-card.*?</article>',r'data:image/[^"\s]+']:
 before=re.findall(pattern,original,re.S);after=re.findall(pattern,s,re.S)
 assert before and before==after,'Protected catalogue/image content changed'
p.write_text(s,encoding='utf-8')
print('Applied buyer-flow repair. Catalogue, prices and images unchanged.')
