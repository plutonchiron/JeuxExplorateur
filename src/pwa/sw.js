// Service worker de l'appli installable : met toutes les pages en cache à l'installation, puis sert le cache d'abord
// (le jeu fonctionne alors sans réseau). La version change à chaque build : l'ancien cache est alors supprimé.
const CACHE = 'explorateurs-/*VERSION*/';
const FILES = /*FILES*/;

self.addEventListener('install', e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(FILES)).then(() => self.skipWaiting()));
});
self.addEventListener('activate', e => {
  e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k.startsWith('explorateurs-') && k !== CACHE).map(k => caches.delete(k)))).then(() => self.clients.claim()));
});
self.addEventListener('fetch', e => {
  const req = e.request;
  if(req.method !== 'GET' || new URL(req.url).origin !== location.origin) return;
  const home = new URL('index.html', self.registration.scope).href;
  e.respondWith(caches.match(req, {ignoreSearch: true}).then(r => r || (req.mode === 'navigate' && new URL(req.url).pathname.endsWith('/') ? caches.match(home) : null) || fetch(req)));
});
