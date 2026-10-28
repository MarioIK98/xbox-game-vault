'use strict';
const SCOPE=new URL('./',self.location.href);
const PREFIX='gv-public-'+encodeURIComponent(SCOPE.pathname)+'-';
const VERSION=PREFIX+'2026-10-28-sharing-ui-v1';
const PRECACHE=['./','./index.html','./site.webmanifest','./og-game-vault.jpg',
 './icons/game-vault-192.png','./icons/game-vault-512.png',
 './plattform/xbox-360.html','./plattform/original-xbox.html','./plattform/playstation-2.html',
 './plattform/psp.html','./plattform/playstation-4.html','./plattform/playstation-5.html',
 './plattform/nintendo-ds.html','./plattform/pc.html',
 './datenschutz.html','./hinweise.html','./uebersicht.html','./teilen.html'];
const ALLOWED=new Set(PRECACHE.map(path=>new URL(path,SCOPE).href));
self.addEventListener('install',event=>event.waitUntil(
 caches.open(VERSION).then(cache=>cache.addAll([...ALLOWED])).then(()=>self.skipWaiting())
));
self.addEventListener('activate',event=>event.waitUntil(
 caches.keys().then(keys=>Promise.all(keys.filter(key=>
  (key.startsWith(PREFIX)&&key!==VERSION)||
  (SCOPE.pathname==='/xbox-game-vault/oeffentlich/'&&key==='gv-public-2026-10-27-v5')
 ).map(key=>caches.delete(key)))).then(()=>self.clients.claim())
));
function offlinePage(){
 return new Response('<!doctype html><html lang="de"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Offline | Game Vault</title><main><h1>Diese Seite ist offline nicht gespeichert.</h1><p>Bitte stelle die Internetverbindung wieder her oder öffne den gespeicherten Katalog.</p><p><a href="'+SCOPE.pathname+'">Zum Spielekatalog</a></p><p>Verfügbarkeit und Preise müssen vor einer Einigung geprüft werden.</p></main></html>',{status:503,headers:{'Content-Type':'text/html; charset=utf-8','Cache-Control':'no-store'}});
}
self.addEventListener('fetch',event=>{
 if(event.request.method!=='GET')return;
 const url=new URL(event.request.url);
 if(url.origin!==SCOPE.origin||!url.pathname.startsWith(SCOPE.pathname))return;
 const key=url.origin+url.pathname;
 event.respondWith((async()=>{
  const cache=await caches.open(VERSION);
  try{
   const response=await fetch(event.request);
   if(ALLOWED.has(key)&&response.ok&&!response.redirected&&response.type==='basic'&&new URL(response.url).pathname===url.pathname){
    try{await cache.put(key,response.clone());}catch(_){}
   }
   return response;
  }catch(_){
   const cached=ALLOWED.has(key)?await cache.match(key):null;
   if(cached)return cached;
   return event.request.mode==='navigate'?offlinePage():Response.error();
  }
 })());
});
