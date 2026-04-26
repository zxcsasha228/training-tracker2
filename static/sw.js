// static/sw.js
const CACHE_NAME = 'fittrack-v2';  // поменяй версию

self.addEventListener('install', event => {
    console.log('Service Worker установлен');
    self.skipWaiting();  // активируем сразу
});

self.addEventListener('activate', event => {
    console.log('Service Worker активирован');
    event.waitUntil(
        caches.keys().then(keys => {
            return Promise.all(
                keys.filter(key => key !== CACHE_NAME)
                    .map(key => caches.delete(key))
            );
        })
    );
    self.clients.claim();
});

self.addEventListener('fetch', event => {
    // Пропускаем запросы к API
    if (event.request.url.includes('/api/')) {
        return;
    }
    
    // Пропускаем запросы к загрузкам
    if (event.request.url.includes('/uploads/')) {
        return;
    }
    
    // Для всего остального - сначала сеть, потом кэш
    event.respondWith(
        fetch(event.request)
            .catch(() => {
                return caches.match(event.request);
            })
    );
});