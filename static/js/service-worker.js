// Service Worker for GloriaMundo PWA
const CACHE_NAME = 'glorimundo-pwa-v2'; // Updated cache version
const ASSETS_TO_CACHE = [
  '/',
  '/static/css/style.css',
  '/static/js/script.js',
  '/static/img/logo.svg',
  '/static/img/favicon.ico',
  '/static/img/favicon.svg',
  '/static/img/favicon-96x96.png',
  '/static/img/apple-touch-icon.png',
  '/static/img/web-app-manifest-192x192.png',
  '/static/img/web-app-manifest-512x512.png',
  '/static/img/splash_screens/icon.png',
  '/static/manifest/manifest.json',  // Added manifest.json
  '/static/img/icon-192.png',        // Added additional icon sizes
  '/static/img/icon-512.png'
];

// Install event - cache critical assets with detailed error diagnostics
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => {
        console.log('[Service Worker] Installing - Caching critical assets');
        
        // Track successful and failed cache attempts
        const results = {
          success: [],
          failed: []
        };
        
        // Use individual fetch and put operations with enhanced error tracking
        const cachePromises = ASSETS_TO_CACHE.map(url => {
          return fetch(url, { cache: 'no-store' }) // Bypass browser cache to ensure fresh content
            .then(response => {
              if (!response.ok) {
                const errorMsg = `Failed to cache: ${url} - Status: ${response.status} ${response.statusText}`;
                console.error(`[Service Worker] ${errorMsg}`);
                results.failed.push({ url, status: response.status, statusText: response.statusText });
                return Promise.resolve(); // Don't reject - continue with other assets
              }
              
              console.log(`[Service Worker] Successfully cached: ${url}`);
              results.success.push(url);
              return cache.put(url, response.clone()); // Clone response before using it
            })
            .catch(error => {
              // More detailed error reporting
              const errorMsg = `Error caching ${url}: ${error.message || error}`;
              console.error(`[Service Worker] ${errorMsg}`);
              results.failed.push({ url, error: error.message || error });
              return Promise.resolve(); // Don't let failures stop other caching
            });
        });
        
        return Promise.all(cachePromises).then(() => {
          // Log overall caching results for diagnostics
          console.log(`[Service Worker] Caching complete - Success: ${results.success.length}, Failed: ${results.failed.length}`);
          if (results.failed.length > 0) {
            console.warn('[Service Worker] Failed to cache the following resources:', results.failed);
          }
          return results;
        });
      })
      .then(() => {
        console.log('Service worker installation complete');
        return self.skipWaiting();
      })
      .catch(error => {
        console.error('Service worker installation failed:', error);
        // Allow service worker to activate despite cache failures
        return self.skipWaiting();
      })
  );
});

// Activate event - clean up old caches
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.map(cacheName => {
          if (cacheName !== CACHE_NAME) {
            console.log('Service worker: clearing old cache', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    }).then(() => self.clients.claim())
  );
});

// Fetch event - serve from cache if available, otherwise fetch from network
self.addEventListener('fetch', event => {
  event.respondWith(
    caches.match(event.request)
      .then(response => {
        // Cache hit - return response
        if (response) {
          return response;
        }

        // Clone the request - request can only be used once
        const fetchRequest = event.request.clone();

        // For non-GET requests, go to network
        if (event.request.method !== 'GET') {
          return fetch(fetchRequest);
        }

        // For HTML pages, always fetch fresh from network
        if (event.request.headers.get('accept').includes('text/html')) {
          return fetch(fetchRequest).then(
            response => {
              // Return the network response
              return response;
            }
          ).catch(error => {
            console.log('Fetch failed; returning offline page instead.', error);
            // You could return a custom offline page here
          });
        }

        // For other requests, try network first, then fall back to cache
        return fetch(fetchRequest).then(
          response => {
            // Check if we received a valid response
            if (!response || response.status !== 200 || response.type !== 'basic') {
              return response;
            }

            // Clone the response - response can only be used once
            const responseToCache = response.clone();

            caches.open(CACHE_NAME)
              .then(cache => {
                cache.put(event.request, responseToCache);
              });

            return response;
          }
        );
      })
  );
});

// Background sync for offline actions
self.addEventListener('sync', event => {
  if (event.tag === 'sync-messages') {
    event.waitUntil(syncMessages());
  }
});

// Sample function for syncing messages when back online
async function syncMessages() {
  // Implementation would go here for sending queued messages
  console.log('Syncing messages...');
}