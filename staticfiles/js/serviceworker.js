// Service Worker Version
const CACHE_NAME = 'v1';

// Files to cache
const CACHE_ASSETS = [
  '/',
  '/static/css/styles.css',
  '/static/js/script.js',
  // Add other static files here, e.g., images, fonts
];

// Install event
self.addEventListener('install', function(event) {
  event.waitUntil(
    caches.open(CACHE_NAME).then(function(cache) {
      return cache.addAll(CACHE_ASSETS);
    })
  );
});

// Activate event
self.addEventListener('activate', function(event) {
  event.waitUntil(
    caches.keys().then(function(cacheNames) {
      return Promise.all(
        cacheNames.map(function(name) {
          // Delete old caches
          if (name !== CACHE_NAME) {
            return caches.delete(name);
          }
        })
      );
    })
  );
});

// Fetch event
self.addEventListener('fetch', function(event) {
  event.respondWith(
    caches.match(event.request).then(function(response) {
      // Return cached response if found, otherwise fetch from network
      return response || fetch(event.request).then(function(networkResponse) {
        // Optional: cache the fetched response for future use
        return caches.open(CACHE_NAME).then(function(cache) {
          cache.put(event.request, networkResponse.clone());
          return networkResponse;
        });
      });
    })
  );
});
