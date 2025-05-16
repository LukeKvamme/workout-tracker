// In a separate service-worker.js file
self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open('workout-v1').then((cache) => {
            return cache.addAll([
                '/',
                '/static/css/style.css',
                '/static/js/app.js'
            ]);
        })
    );
});

// Basic offline functionality
self.addEventListener('fetch', (event) => {
    event.respondWith(
        caches.match(event.request).then((response) => {
            return response || fetch(event.request);
        })
    );
});