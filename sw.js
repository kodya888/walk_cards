/* Service worker: офлайн-кэш приложения.
   ВАЖНО: при любом изменении index.html / style.css / app.js / cards.js
   поднимай номер версии ниже (v1 -> v2), иначе телефон покажет старую копию. */

const VERSION = 'wc-v5';

const ASSETS = [
  './',
  'index.html',
  'style.css',
  'app.js',
  'cards.js',
  'manifest.json',
  'vendor/leaflet/leaflet.css',
  'vendor/leaflet/leaflet.js',
  'vendor/leaflet/images/marker-icon.png',
  'vendor/leaflet/images/marker-icon-2x.png',
  'vendor/leaflet/images/marker-shadow.png',
  'vendor/leaflet/images/layers.png',
  'vendor/leaflet/images/layers-2x.png',
  'img/1_letopisets_dvora.svg',
  'img/2-nochnoy_smotritel_fonarey.svg',
  'img/3_inspektor_pirozhkov.svg',
  'img/lisa/01_borovik.webp',
  'img/lisa/02_shapka_lisichka.webp',
  'img/lisa/03_lisa_ryaninushka.webp',
  'img/lisa/04_progulshchitsa.webp',
  'img/lisa/05_zheludekhranitelnitsa.webp',
  'img/lisa/06_kruzhka_dlya_dvoih.webp',
  'img/lisa/07_tykolub.webp',
  'img/lisa/08_sbortsitca_nalivnyh.webp',
  'img/lisa/09_hodoka_pod_goroshek.webp',
  'img/lisa/10_sviter_domik.webp',
  'img/lisa/11_tykvenny_vsadnik.webp',
  'img/lisa/12_zont_v_goroshek.webp',
  'img/lisa/13_buketodarka.webp',
  'img/lisa/14_chitatel_pod_pledom.webp',
  'img/lisa/15_fonarshchitsa_s_ryabinoi.webp',
  'img/lisa/16_gerbarii.webp',
  'img/lisa/17_gurman_degustator.webp',
  'img/lisa/18_sapogi_poprygunyi.webp',
  'img/lisa/19_kokon_so_vkusom.webp',
  'img/lisa/20_luzheprohodets.webp',
  'img/lisa/21_ryabinovyi_adres.webp',
  'img/lisa/22_kudryavaya_tykva.webp',
  'img/lisa/23_gribnaya_kurerka.webp',
  'img/lisa/24_sviter_obnimashka.webp',
  'img/lisa/25_masteritsa.webp',
  'icons/icon-192.png',
  'icons/icon-512.png'
];

self.addEventListener('install', e => {
  e.waitUntil(
    caches.open(VERSION).then(c => c.addAll(ASSETS)).then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys()
      .then(keys => Promise.all(keys.filter(k => k !== VERSION).map(k => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', e => {
  const req = e.request;

  // тайлы карты не кэшируем (политика OSM) — идём в сеть
  if (req.url.includes('tile.openstreetmap.org')) return;

  if (req.method !== 'GET') return;

  e.respondWith(
    caches.match(req).then(cached => {
      if (cached) return cached;
      return fetch(req).then(res => {
        // кэшируем только свои файлы
        if (res.ok && new URL(req.url).origin === location.origin) {
          const copy = res.clone();
          caches.open(VERSION).then(c => c.put(req, copy));
        }
        return res;
      }).catch(() => {
        if (req.mode === 'navigate') return caches.match('index.html');
        throw new Error('offline');
      });
    })
  );
});
