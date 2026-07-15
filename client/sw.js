const CACHE_NAME = 'GrabBlitz-cache-v1';
const urlsToCache = [
  '/',
  '/index.html',
  '/manifest.json',
  '/assets/css/theme.css',
  '/assets/css/components.css',
  '/assets/css/animations.css',
  '/assets/js/app.js',
  '/assets/js/downloader.js',
  '/assets/js/history.js',
  '/assets/js/theme.js',
  '/assets/js/ui.js',
  '/assets/js/utils.js',
  '/assets/images/logo.png',
  'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css'
];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => {
        return cache.addAll(urlsToCache);
      })
  );
});

self.addEventListener('fetch', event => {
  // We only want to cache GET requests for assets, not API calls
  if (event.request.url.includes('/api/')) return;
  if (event.request.method !== 'GET') return;

  event.respondWith(
    caches.match(event.request)
      .then(response => {
        if (response) {
          return response;
        }
        return fetch(event.request);
      })
  );
});
