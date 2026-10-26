const VERSION='gv-public-2026-10-26-v2';
const PRECACHE=['./','./index.html','./site.webmanifest','./og-game-vault.jpg',
 './icons/game-vault-192.png','./icons/game-vault-512.png',
 './plattform/xbox-360.html','./plattform/original-xbox.html','./plattform/playstation-2.html',
 './plattform/psp.html','./plattform/playstation-4.html','./plattform/playstation-5.html',
 './plattform/nintendo-ds.html','./plattform/pc.html'];
self.addEventListener('install',e=>e.waitUntil(caches.open(VERSION).then(c=>c.addAll(PRECACHE)).then(()=>self.skipWaiting())));
self.addEventListener('activate',e=>e.waitUntil(caches.keys().then(keys=>Promise.all(keys.filter(x=>x.startsWith('gv-public-')&&x!==VERSION).map(x=>caches.delete(x)))).then(()=>self.clients.claim())));
self.addEventListener('fetch',e=>{
  if(e.request.method!=='GET')return;
  const url=new URL(e.request.url);
  if(url.origin!==self.location.origin||!url.pathname.includes('/oeffentlich/'))return;
  const normalized=new Request(url.origin+url.pathname,{method:'GET'});
  e.respondWith(fetch(e.request).then(response=>{
    if(response.ok&&response.type==='basic'){
      const cloned=response.clone();
      caches.open(VERSION).then(c=>c.put(normalized,cloned)).catch(()=>{});
    }
    return response;
  }).catch(async()=>{
    const cached=await caches.match(normalized);
    if(cached)return cached;
    if(e.request.mode==='navigate')return (await caches.match('./index.html'))||Response.error();
    return Response.error();
  }));
});