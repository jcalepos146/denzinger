/* Offline support for the Sources of Catholic Dogma reader.
   The reader page holds the whole collection, so caching it makes every entry readable offline.
   Entry pages are cached as they are visited; an uncached one opens the reader at that entry. */
const VERSION = '__VERSION__';
const CACHE = 'denz-' + VERSION;
const FONTS = 'denz-fonts';
const CORE = ['./', 'assets/entry.css', 'manifest.webmanifest', 'icons/icon-192.png', 'icons/icon-512.png', 'icons/icon-180.png'];

self.addEventListener('install', ev => {
  ev.waitUntil(caches.open(CACHE).then(c => c.addAll(CORE)).then(() => self.skipWaiting()));
});

self.addEventListener('activate', ev => {
  ev.waitUntil(caches.keys()
    .then(keys => Promise.all(keys.filter(k => k.startsWith('denz-') && k !== CACHE && k !== FONTS).map(k => caches.delete(k))))
    .then(() => self.clients.claim()));
});

self.addEventListener('fetch', ev => {
  const req = ev.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);
  const scope = new URL(self.registration.scope);

  // Google Fonts: keep a copy once loaded
  if (url.hostname === 'fonts.googleapis.com' || url.hostname === 'fonts.gstatic.com') {
    ev.respondWith(caches.open(FONTS).then(async c => {
      const hit = await c.match(req);
      if (hit) return hit;
      try { const res = await fetch(req); if (res.ok || res.type === 'opaque') c.put(req, res.clone()); return res; }
      catch (_) { return new Response('', { status: 503 }); }
    }));
    return;
  }
  if (url.origin !== scope.origin || !url.pathname.startsWith(scope.pathname)) return;

  // Pages: the network first, so corrections arrive; the cache when offline
  if (req.mode === 'navigate') {
    ev.respondWith((async () => {
      const c = await caches.open(CACHE);
      try {
        const res = await fetch(req);
        if (res.ok) c.put(req, res.clone());
        return res;
      } catch (_) {
        const hit = await c.match(req, { ignoreSearch: true });
        if (hit) return hit;
        const m = url.pathname.slice(scope.pathname.length).match(/^n\/([^/]+)\/?$/);
        if (m) return Response.redirect(scope.href + '#n' + decodeURIComponent(m[1]).replace(/_s/g, '*'), 302);
        return (await c.match('./')) || new Response('Offline', { status: 503, headers: { 'Content-Type': 'text/plain' } });
      }
    })());
    return;
  }

  // Everything else: the cache first, refreshed in the background
  ev.respondWith(caches.open(CACHE).then(async c => {
    const hit = await c.match(req);
    const net = fetch(req).then(res => { if (res.ok) c.put(req, res.clone()); return res; }).catch(() => null);
    return hit || (await net) || new Response('', { status: 504 });
  }));
});
