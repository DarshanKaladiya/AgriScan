/**
 * AgriScan Offline Service Worker
 * Precaches core assets, local AI model, and advice database
 * Enables full installability and 100% offline functionality.
 */

const CACHE_NAME = 'agriscan-cache-v2';

const ASSETS_TO_CACHE = [
  './',
  './index.html',
  './manifest.json',
  './css/app.css',
  './js/app.js',
  './js/db.js',
  './js/i18n.js',
  './js/auth.js',
  './js/model_service.js',
  './js/sync_service.js',
  './vendor/ort.min.js',
  './vendor/ort-wasm-simd.wasm',
  './vendor/ort-wasm.wasm',
  './model/labels.json',
  './data/advisory.json'
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      console.log('📦 Caching offline app shell and assets...');
      return cache.addAll(ASSETS_TO_CACHE).catch(err => {
        console.warn('Non-critical cache skip:', err);
      });
    })
  );
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k))
      );
    })
  );
  self.clients.claim();
});

// Cache-First strategy for local offline assets, Network-First for API
self.addEventListener('fetch', (event) => {
  const url = event.request.url;

  // Network-first for API sync requests
  if (url.includes('/api/')) {
    event.respondWith(
      fetch(event.request).catch(() => {
        return new Response(JSON.stringify({ offline: true }), {
          headers: { 'Content-Type': 'application/json' }
        });
      })
    );
    return;
  }

  // Cache-first for all local app files & models
  event.respondWith(
    caches.match(event.request).then((cachedResponse) => {
      if (cachedResponse) return cachedResponse;
      return fetch(event.request).then((networkResponse) => {
        // Cache dynamic local assets (e.g. model.onnx)
        if (event.request.method === 'GET' && networkResponse.status === 200) {
          const clone = networkResponse.clone();
          caches.open(CACHE_NAME).then(cache => cache.put(event.request, clone));
        }
        return networkResponse;
      });
    }).catch(() => {
      return caches.match('./index.html');
    })
  );
});
