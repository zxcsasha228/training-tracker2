// static/sw.js
const CACHE_NAME = 'fittrack-v4';

// Ресурсы для кэширования (только статика)
const urlsToCache = [
    '/static/manifest.json',
    '/static/icons/icon-72x72.png',
    '/static/icons/icon-96x96.png',
    '/static/icons/icon-128x128.png',
    '/static/icons/icon-144x144.png',
    '/static/icons/icon-152x152.png',
    '/static/icons/icon-192x192.png',
    '/static/icons/icon-384x384.png',
    '/static/icons/icon-512x512.png'
];

// Установка SW
self.addEventListener('install', event => {
    console.log('Service Worker установлен');
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(cache => {
                console.log('Кэширование статики');
                // Кэшируем только те файлы, которые существуют
                return cache.addAll(urlsToCache.filter(url => {
                    // Пропускаем отсутствующие иконки
                    return true;
                }));
            })
            .catch(err => {
                console.log('Ошибка кэширования:', err);
            })
    );
    self.skipWaiting();
});

// Активация SW
self.addEventListener('activate', event => {
    console.log('Service Worker активирован');
    event.waitUntil(
        caches.keys().then(keys => {
            return Promise.all(
                keys.map(key => {
                    if (key !== CACHE_NAME) {
                        console.log('Удалён старый кэш:', key);
                        return caches.delete(key);
                    }
                })
            );
        })
    );
    self.clients.claim();
});

// Обработка запросов - ОТКЛЮЧАЕМ ДЛЯ СТРАНИЦ ТРЕНИРОВОК
self.addEventListener('fetch', event => {
    const url = new URL(event.request.url);
    
    // ПОЛНОСТЬЮ ПРОПУСКАЕМ все страницы тренировок
    if (url.pathname.includes('/workout/')) {
        console.log('⏩ Пропускаем тренировку:', url.pathname);
        return; // Не перехватываем - пусть браузер сам обрабатывает
    }
    
    // Пропускаем API запросы
    if (url.pathname.startsWith('/api/')) {
        return;
    }
    
    // Пропускаем загрузки файлов
    if (url.pathname.startsWith('/uploads/')) {
        return;
    }
    
    // Пропускаем видео
    if (url.pathname.startsWith('/static/videos/')) {
        return;
    }
    
    // Для статических файлов - кэш с fallback
    if (url.pathname.startsWith('/static/')) {
        event.respondWith(
            fetch(event.request)
                .catch(() => {
                    return caches.match(event.request);
                })
        );
        return;
    }
    
    // Для всех остальных страниц - только сеть, без кэша
    // (возвращаем undefined, чтобы браузер сам обработал)
    return;
});