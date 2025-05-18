// PWA Service Worker Registration
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/static/js/service-worker.js')
      .then(registration => {
        console.log('ServiceWorker registration successful with scope: ', registration.scope);
      })
      .catch(err => {
        console.log('ServiceWorker registration failed: ', err);
      });
  });

  // Listen for controllerchange events (when the service worker is updated)
  navigator.serviceWorker.addEventListener('controllerchange', () => {
    console.log('Service worker controller changed');
  });

  // Check for updates to the service worker
  setInterval(() => {
    if (navigator.serviceWorker.controller) {
      navigator.serviceWorker.controller.postMessage({ type: 'CHECK_FOR_UPDATES' });
    }
  }, 60 * 60 * 1000); // Check every hour
}