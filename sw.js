/* Service worker: офлайн-кэш приложения.
   ВАЖНО: при любом изменении index.html / style.css / app.js / cards.js
   поднимай номер версии (ниже и в ?v=... у тегов в index.html),
   иначе телефон покажет старую копию. */

const VERSION = 'wc-v21';

const ASSETS = [
  './',
  'index.html',
  'style.css?v=19',
  'app.js?v=21',
  'cards.js?v=19',
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
  'img/backs/gorod_logo.svg',
  'img/backs/zima_logo.png',
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
  'img/zima/01_elochny_naryadchik.webp',
  'img/zima/02_termos_sogrevatel.webp',
  'img/zima/03_elochny_verholaz.webp',
  'img/zima/04_pled_kokon.webp',
  'img/zima/05_pervy_led.webp',
  'img/zima/06_podarkonosets.webp',
  'img/zima/07_sharik_zateynik.webp',
  'img/zima/08_podarok_fonarik.webp',
  'img/zima/09_elkonosets.webp',
  'img/zima/10_snegovikov_drug.webp',
  'img/zima/11_figurist_lis.webp',
  'img/zima/12_snegouborshchik.webp',
  'img/zima/13_snezhny_kurier.webp',
  'img/zima/14_chitatel_u_fonarya.webp',
  'img/zima/15_snezhny_plyasun.webp',
  'img/zima/16_pryanichny_stol.webp',
  'img/zima/17_drovonos.webp',
  'img/zima/18_hozyain_kresla.webp',
  'img/zima/19_drug_batarei.webp',
  'img/zima/20_lyzhnik_lis.webp',
  'img/zima/21_lovets_snezhinok.webp',
  'img/zima/22_snezhny_angel.webp',
  'img/zima/23_nablyudatel_u_okna.webp',
  'img/zima/24_passazhir_s_kakao.webp',
  'img/kot/01_domashniy_abazhur.webp',
  'img/kot/02_razbivatel_servizov.webp',
  'img/kot/03_kot_v_korobke.webp',
  'img/kot/04_shtornyy_pirat.webp',
  'img/kot/05_inspektor_akvariuma.webp',
  'img/kot/06_master_puhovyh_bur.webp',
  'img/kot/07_schastlivyy_rybolov.webp',
  'img/kot/08_pobeditel_podushek.webp',
  'img/kot/09_gurman_iz_vedra.webp',
  'img/kot/10_mumiya_nevidimka.webp',
  'img/kot/11_uznik_klubka.webp',
  'img/kot/12_zhertva_banana.webp',
  'img/kot/13_domashnyaya_girlyanda.webp',
  'img/kot/14_sadovnik_pod_gorshkom.webp',
  'img/kot/15_korol_pylesosov.webp',
  'img/kot/16_otpusk_v_tazu.webp',
  'img/kot/17_banochnyy_perepoloh.webp',
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
