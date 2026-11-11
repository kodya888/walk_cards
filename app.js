'use strict';

/* =========================================================
   Гуляю-собираю — логика
   ========================================================= */

const CFG = {
  CIRCLE_R: 300,          // радиус «домашнего» круга, м
  POINT_MIN: 300,         // ближе этой дистанции точку ставить нельзя
  POINT_MAX: 700,         // дальше этой — тоже
  HIT_R: 80,              // зона, в которой точка считается найденной
  ACC_MAX: 60,            // замеры с точностью хуже 60 м не засчитываем
  CONFIRM: 2,             // сколько замеров подряд нужно для срабатывания
  TICK_MS: 4000,          // как часто обрабатывать позицию
  ROUTE_LEN: 2,           // точек в маршруте на текущем уровне
  ROUTE_UNLOCK_WALKS: 3,  // после скольких прогулок открывается маршрут
  LIMIT_TIERS: [          // дневной лимит карточек по «прокачке» (всего прогулок)
    { from: 0,  limit: 2 },
    { from: 5,  limit: 3 },
    { from: 15, limit: 4 },
    { from: 30, limit: 5 }
    // анлим — в будущем за купленный пак (снимать лимит через флаг в save)
  ],
  ZOOM: 16,
  DEFAULT_CENTER: [56.3269, 44.0059] // Нижний Новгород
};

const STORE_KEY = 'walk_cards_v1';

/* ---------------- состояние ---------------- */

let state = {
  collection: {},                 // id карточки -> сколько раз попадалась
  order: [],                      // id карточек в порядке получения (для галереи)
  walks: 0,
  walksToday: 0,                  // карточек за сегодня
  day: '',                        // 'ГГГГ-ММ-ДД' — сброс дневного счётчика
  active: null,                   // текущая прогулка
  home: null,                     // {lat,lng} — старт последней прогулки
  unlocked: { circle: true, point: true, route: false }
};

function save() {
  try { localStorage.setItem(STORE_KEY, JSON.stringify(state)); } catch (e) {}
}

function load() {
  try {
    const raw = localStorage.getItem(STORE_KEY);
    if (raw) {
      const data = JSON.parse(raw);
      state = Object.assign(state, data);
    }
  } catch (e) {}
  state.unlocked.route = state.walks >= CFG.ROUTE_UNLOCK_WALKS;
  if (!Array.isArray(state.order)) {          // переход со старой версии
    state.order = CARDS.filter(c => state.collection[c.id] > 0).map(c => c.id);
  }
  state.order = [...new Set(state.order)].filter(id => CARD_BY_ID[id]);
  // собранные, но потерявшие позицию карточки — дописать в конец (страховка)
  Object.keys(state.collection).forEach(id => {
    if (state.collection[id] > 0 && CARD_BY_ID[id] && !state.order.includes(id)) {
      state.order.push(id);
    }
  });
}

/* ---------------- дневной лимит карточек ---------------- */

function todayKey() {
  const d = new Date();
  return d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-' +
         String(d.getDate()).padStart(2, '0');
}

function rollDay() {
  const key = todayKey();
  if (state.day !== key) {
    state.day = key;
    state.walksToday = 0;
  }
}

function dailyLimit() {
  let limit = CFG.LIMIT_TIERS[0].limit;
  CFG.LIMIT_TIERS.forEach(t => { if (state.walks >= t.from) limit = t.limit; });
  return limit;
}

function cardsLeftToday() {
  rollDay();
  return Math.max(0, dailyLimit() - (state.walksToday || 0));
}

/* ---------------- геометрия ---------------- */

const R_EARTH = 6371000;
const rad = d => d * Math.PI / 180;
const deg = r => r * 180 / Math.PI;

function haversine(a, b) {
  const dLat = rad(b.lat - a.lat);
  const dLng = rad(b.lng - a.lng);
  const s = Math.sin(dLat / 2) ** 2 +
            Math.cos(rad(a.lat)) * Math.cos(rad(b.lat)) * Math.sin(dLng / 2) ** 2;
  return 2 * R_EARTH * Math.asin(Math.sqrt(s));
}

function bearing(a, b) {
  const y = Math.sin(rad(b.lng - a.lng)) * Math.cos(rad(b.lat));
  const x = Math.cos(rad(a.lat)) * Math.sin(rad(b.lat)) -
            Math.sin(rad(a.lat)) * Math.cos(rad(b.lat)) * Math.cos(rad(b.lng - a.lng));
  return (deg(Math.atan2(y, x)) + 360) % 360;
}

/** точка на расстоянии dist (м) по азимуту brg (0–360) от точки a */
function destination(a, dist, brg) {
  const dr = dist / R_EARTH, b = rad(brg);
  const lat1 = rad(a.lat), lng1 = rad(a.lng);
  const lat2 = Math.asin(Math.sin(lat1) * Math.cos(dr) +
                         Math.cos(lat1) * Math.sin(dr) * Math.cos(b));
  const lng2 = lng1 + Math.atan2(Math.sin(b) * Math.sin(dr) * Math.cos(lat1),
                                 Math.cos(dr) - Math.sin(lat1) * Math.sin(lat2));
  return { lat: deg(lat2), lng: ((deg(lng2) + 540) % 360) - 180 };
}

function randomTarget(from) {
  const d = CFG.POINT_MIN + Math.random() * (CFG.POINT_MAX - CFG.POINT_MIN);
  return destination(from, d, Math.random() * 360);
}

function fmtDist(m) {
  return m >= 1000 ? (m / 1000).toFixed(2) + ' км' : Math.round(m) + ' м';
}

/* ---------------- DOM ---------------- */

const $ = id => document.getElementById(id);

const els = {
  mapEl: $('map'),
  statCards: $('stat-cards'),
  statWalks: $('stat-walks'),
  btnCollection: $('btn-collection'),
  hud: $('hud'),
  hudText: $('hud-text'),
  hudDist: $('hud-distance'),
  btnNavigate: $('btn-navigate'),
  btnCancel: $('btn-cancel'),
  startSheet: $('start-sheet'),
  modeHint: $('mode-hint'),
  modes: $('modes'),
  pointTools: $('point-tools'),
  btnReroll: $('btn-reroll'),
  btnStart: $('btn-start'),
  btnCloseSheet: $('btn-close-sheet'),
  btnOpenSheet: $('btn-open-sheet'),
  cardOverlay: $('card-overlay'),
  cardShell: $('card-shell'),
  cardInner: $('card-inner'),
  cardFront: $('card-front'),
  cardFrontDesc: $('card-front-desc'),
  cardBack: $('card-back'),
  cardNo: $('card-no'),
  cardImg: $('card-img'),
  cardName: $('card-name'),
  cardRarity: $('card-rarity'),
  btnCardOk: $('btn-card-ok'),
  collection: $('collection'),
  collectionTitle: $('collection-title'),
  collectionGrid: $('collection-grid'),
  collectionProgress: $('collection-progress'),
  packsList: $('packs-list'),
  packView: $('pack-view'),
  btnCollectionBack: $('btn-collection-back'),
  btnCollectionClose: $('btn-collection-close'),
  completeOverlay: $('complete-overlay'),
  btnCompleteOk: $('btn-complete-ok'),
  debug: $('debug'),
  btnSim350: $('btn-sim-350'),
  btnSimTarget: $('btn-sim-to-target')
};

/* ---------------- карта ---------------- */

let map = null;
let meMarker = null;
let layerGroup = null;      // всё, что относится к текущей прогулке
let homeLayer = null;       // «призрак» дома на карте (куда вернуться)
let draft = null;           // черновик точки до старта
let chosenMode = 'circle';

let me = null;              // {lat,lng,acc}
let simulate = false;       // включён ли симулятор
let lastTick = 0;
let watchId = null;

function initMap() {
  map = L.map('map', {
    zoomControl: false,
    attributionControl: true
  }).setView(CFG.DEFAULT_CENTER, CFG.ZOOM);

  // стандартные бесплатные плитки OSM; тёмную «ночную» раскраску даёт CSS-фильтр
  L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
  }).addTo(map);

  homeLayer = L.layerGroup().addTo(map);

  L.control.zoom({ position: 'bottomright' }).addTo(map);
  layerGroup = L.layerGroup().addTo(map);
}

function meIconHtml() { return '<div class="me-dot"></div>'; }

function updateMeMarker() {
  if (!me) return;
  if (meMarker) {
    meMarker.setLatLng([me.lat, me.lng]);
  } else {
    meMarker = L.marker([me.lat, me.lng], {
      icon: L.divIcon({ className: 'me-icon', html: meIconHtml(), iconSize: [26, 26], iconAnchor: [13, 13] }),
      zIndexOffset: 1000,
      interactive: false
    }).addTo(map);
  }
}

/* ---------------- геолокация ---------------- */

function startGeo() {
  if (!navigator.geolocation) {
    onGeoError({ code: 0, message: 'Браузер не поддерживает геолокацию' });
    return;
  }
  watchId = navigator.geolocation.watchPosition(onPosition, onGeoError, {
    enableHighAccuracy: true,
    maximumAge: 8000,
    timeout: 25000
  });
}

function onPosition(pos) {
  if (simulate) return;
  const c = pos.coords;
  me = { lat: c.latitude, lng: c.longitude, acc: c.accuracy };
  updateMeMarker();
  if (!state.active) map.panTo([me.lat, me.lng], { animate: true, duration: 0.6 });
  tick(true);
}

function onGeoError(err) {
  console.warn('geo error', err);
  if (!me) {
    els.hudText.textContent = 'Не вижу тебя на карте. Разреши геолокацию.';
  }
}

/* ---------------- карточка ---------------- */

let currentCard = null;
let cardFromGallery = false;
let pendingComplete = false;   // собрана последняя карточка — показать поздравление после неё

/* у каждого пака — своя рубашка: фон, узор и круглый знак задаёт CSS
   по data-pack. Надписей на рубашке нет. */

/** Показ большой карточки. fromGallery=true — открыт из коллекции (обычный просмотр) */
function showCard(card, fromGallery = false) {
  currentCard = card;
  cardFromGallery = fromGallery;
  const pack = card.pack || 'gorod';

  els.cardBack.dataset.pack = pack;
  els.cardFront.dataset.pack = pack;

  // подпись карточки всегда на лицевой стороне: на обороте только знак
  const desc = card.desc || '';
  els.cardFrontDesc.textContent = desc;
  els.cardFrontDesc.classList.toggle('hidden', !desc);
  els.cardFront.classList.toggle('no-desc', !desc);

  els.cardFront.classList.toggle('rare', card.rarity === 'rare');
  els.cardImg.src = card.img;
  els.cardImg.alt = card.name;
  els.cardName.textContent = card.name;
  const has = state.collection[card.id] || 0;
  els.cardRarity.textContent =
    (card.rarity === 'rare' ? '★ редкая' : 'обычная') +
    (fromGallery && has > 1 ? ' · есть ×' + has : '');
  els.cardNo.textContent = '№ ' + String(CARDS.indexOf(card) + 1).padStart(2, '0');
  els.btnCardOk.textContent = fromGallery ? 'Вернуть в галерею' : 'Забрать';
  els.cardInner.classList.remove('flipped');

  els.cardOverlay.classList.remove('hidden');
  els.cardShell.classList.remove('dropping');
  void els.cardShell.offsetWidth;   // перезапуск анимации
  els.cardShell.classList.add('dropping');
}

function hideCard() {
  els.cardOverlay.classList.add('hidden');
  const fromGallery = cardFromGallery;
  currentCard = null;
  cardFromGallery = false;
  if (fromGallery) {
    // возвращаемся в галерею, на то же место
    els.collection.classList.remove('hidden');
  } else if (pendingComplete) {
    // это была последняя карточка — поздравляем
    pendingComplete = false;
    els.completeOverlay.classList.remove('hidden');
  }
}

/* ---------------- коллекция ---------------- */

function packStats(key) {
  const cards = CARDS.filter(c => (c.pack || 'gorod') === key);
  const got = cards.filter(c => state.collection[c.id] > 0).length;
  return { total: cards.length, got };
}

function makeMiniCard(card) {
  const ownedCount = state.collection[card.id] || 0;
  const el = document.createElement('div');
  el.className = 'mini-card' + (card.rarity === 'rare' ? ' rare' : '');
  el.innerHTML = `<img src="${card.img}" alt=""><div>${card.name}</div><small class="mini-no">№ ${String(CARDS.indexOf(card) + 1).padStart(2, '0')}</small>`;
  if (ownedCount > 1) {
    const badge = document.createElement('span');
    badge.className = 'mini-count';
    badge.textContent = '×' + ownedCount;
    el.appendChild(badge);
  }
  el.addEventListener('click', () => {
    els.collection.classList.add('hidden');
    showCard(card, true);
  });
  return el;
}

/** Экран 1: список коллекций (паков). */
function renderCollection() {
  const got = CARDS.filter(c => state.collection[c.id] > 0).length;
  els.collectionTitle.textContent = 'Коллекция';
  els.collectionProgress.textContent = `Собрано ${got} из ${CARDS.length}`;
  els.btnCollectionBack.classList.add('hidden');
  els.packView.classList.add('hidden');
  els.packsList.classList.remove('hidden');
  els.packsList.innerHTML = '';

  PACKS.forEach(p => {
    const s = packStats(p.key);
    const tile = document.createElement('button');
    tile.type = 'button';
    tile.className = 'pack-tile';
    tile.dataset.pack = p.key;
    tile.innerHTML =
      '<span class="pack-tile-back card-back" data-pack="' + p.key + '">' +
        '<span class="card-back-inner"><span class="card-back-mark"></span></span>' +
      '</span>' +
      '<span class="pack-tile-info"><b>' + p.title + '</b>' +
        '<small>Собрано ' + s.got + ' из ' + s.total + '</small></span>' +
      '<span class="pack-tile-arrow" aria-hidden="true">›</span>';
    tile.addEventListener('click', () => openPack(p.key));
    els.packsList.appendChild(tile);
  });

  els.collection.scrollTop = 0;
}

/** Экран 2: собранные карточки одной коллекции. */
function openPack(key) {
  const info = PACK_BY_KEY[key];
  if (!info) return;

  const s = packStats(key);
  els.collectionTitle.textContent = info.title;
  els.collectionProgress.textContent = `Собрано ${s.got} из ${s.total}`;
  els.btnCollectionBack.classList.remove('hidden');
  els.packsList.classList.add('hidden');
  els.packView.classList.remove('hidden');
  els.collectionGrid.innerHTML = '';

  // state.order хранит порядок получения. Показываем наоборот:
  // последняя выпавшая карточка — первой в верхнем ряду.
  const order = state.order
    .filter(id => CARD_BY_ID[id] && state.collection[id] > 0 &&
                  (CARD_BY_ID[id].pack || 'gorod') === key)
    .reverse();

  if (!order.length) {
    const p = document.createElement('p');
    p.className = 'muted';
    p.textContent = 'Пока пусто. Выйди за круг — первая карточка твоя.';
    els.collectionGrid.appendChild(p);
  } else {
    order.forEach(id => els.collectionGrid.appendChild(makeMiniCard(CARD_BY_ID[id])));
  }

  els.collection.scrollTop = 0;
}

function renderStats() {
  els.statCards.textContent = Object.values(state.collection).reduce((a, b) => a + b, 0);
  els.statWalks.textContent = state.walks;
}

/* ---------------- режимы / старт ---------------- */

function selectMode(mode) {
  chosenMode = mode;
  els.startSheet.classList.add('compact');
  [...els.modes.children].forEach(b => b.classList.toggle('selected', b.dataset.mode === mode));
  const routeBtn = els.modes.querySelector('[data-mode="route"]');
  if (routeBtn) routeBtn.classList.toggle('locked', !state.unlocked.route);

  if (mode === 'point') {
    els.pointTools.classList.remove('hidden');
    els.modeHint.textContent = 'Отодвинь точку и выбери направление';
    makeDraftPoint();
  } else {
    els.pointTools.classList.add('hidden');
    clearDraft();
    els.modeHint.textContent = mode === 'circle'
      ? 'Выйди за круг — и карточка твоя'
      : 'Две точки подряд, редкая карточка в конце';
  }
}

function makeDraftPoint() {
  clearDraft();
  if (!me) return;
  const t = randomTarget(me);
  draft = t;

  const line = L.polyline([[me.lat, me.lng], [t.lat, t.lng]], {
    color: '#ffb020', weight: 2, dashArray: '6 8', opacity: 0.85
  }).addTo(layerGroup);

  const circle = L.circle([me.lat, me.lng], {
    radius: CFG.CIRCLE_R, color: '#7c5cff', weight: 2, fillColor: '#7c5cff', fillOpacity: 0.06,
    className: 'home-ring'
  }).addTo(layerGroup);

  const marker = L.marker([t.lat, t.lng], {
    draggable: true,
    icon: L.divIcon({ className: 'target-icon', html: '<div class="target-pin">★</div>', iconSize: [34, 34], iconAnchor: [17, 17] }),
    zIndexOffset: 900
  }).addTo(layerGroup);

  draft = { lat: t.lat, lng: t.lng, marker, line, circle };

  marker.on('drag', () => {
    const p = marker.getLatLng();
    line.setLatLngs([[me.lat, me.lng], [p.lat, p.lng]]);
    els.modeHint.textContent = 'Расстояние: ' + fmtDist(haversine(me, p));
  });

  marker.on('dragend', () => {
    let p = marker.getLatLng();
    const d = haversine(me, p);
    const brg = bearing(me, p);
    let fixed = p;
    if (d < CFG.POINT_MIN) fixed = destination(me, CFG.POINT_MIN, brg);
    if (d > CFG.POINT_MAX) fixed = destination(me, CFG.POINT_MAX, brg);
    marker.setLatLng([fixed.lat, fixed.lng]);
    line.setLatLngs([[me.lat, me.lng], [fixed.lat, fixed.lng]]);
    draft.lat = fixed.lat;
    draft.lng = fixed.lng;
    els.modeHint.textContent = 'Расстояние: ' + fmtDist(haversine(me, draft))
      + (haversine(me, draft) > 550 ? ' — шанс редкой выше' : '');
  });

  els.modeHint.textContent = 'Расстояние: ' + fmtDist(haversine(me, t));

  // вписываем обе точки так, чтобы они не прятались под панелью
  const sheetH = els.startSheet.getBoundingClientRect().height || 260;
  const pad = Math.max(30, sheetH + 40);
  map.fitBounds(L.latLngBounds([[me.lat, me.lng], [t.lat, t.lng]]), {
    paddingTopLeft: [40, 80],
    paddingBottomRight: [40, pad],
    animate: false
  });
  els.btnStart.textContent = 'В путь';
}

function clearDraft() {
  if (draft && draft.marker) layerGroup.clearLayers();
  draft = null;
}

function startWalk() {
  if (!me) {
    els.modeHint.textContent = 'Жду координаты GPS… включи геолокацию.';
    return;
  }
  if (chosenMode === 'route' && !state.unlocked.route) return;

  rollDay();
  if (cardsLeftToday() <= 0) {
    els.modeHint.textContent =
      'Дневной лимит карточек исчерпан — новая карточка завтра. ' +
      'Гуляешь дальше ради удовольствия? Прогулка без награды: «Закончить» сейчас.';
    return;
  }

  let active;
  if (chosenMode === 'circle') {
    active = { mode: 'circle', start: { lat: me.lat, lng: me.lng }, target: null, streak: 0 };
  } else if (chosenMode === 'point') {
    const t = draft ? { lat: draft.lat, lng: draft.lng } : randomTarget(me);
    active = { mode: 'point', start: { lat: me.lat, lng: me.lng }, target: t, streak: 0 };
  } else {
    const pts = [];
    let prev = { lat: me.lat, lng: me.lng };
    for (let i = 0; i < CFG.ROUTE_LEN; i++) {
      const p = destination(prev, CFG.CIRCLE_R + Math.random() * 200, Math.random() * 360);
      pts.push(p);
      prev = p;
    }
    active = { mode: 'route', start: { lat: me.lat, lng: me.lng }, route: pts, index: 0, streak: 0 };
  }

  state.active = active;
  state.home = { lat: me.lat, lng: me.lng };
  save();
  clearDraft();
  homeLayer.clearLayers();
  els.startSheet.classList.add('hidden');
  drawActive();
  tick(true);
}

/* ---------------- отрисовка активной прогулки ---------------- */

function drawActive() {
  layerGroup.clearLayers();
  const a = state.active;
  if (!a) return;
  const from = me || a.start;

  els.btnOpenSheet.classList.add('hidden');
  els.hud.classList.remove('hidden');
  els.hudDist.textContent = '';

  // стартовая точка
  L.circle([a.start.lat, a.start.lng], {
    radius: CFG.CIRCLE_R, color: '#7c5cff', weight: 2,
    fillColor: '#7c5cff', fillOpacity: 0.05, className: 'home-ring'
  }).addTo(layerGroup);

  if (a.mode === 'circle') {
    els.hudText.textContent = 'Выйди за круг';
    map.setView([a.start.lat, a.start.lng], 15);
  }

  if (a.mode === 'point') {
    els.hudText.textContent = 'Иди к точке';
    L.polyline([[from.lat, from.lng], [a.target.lat, a.target.lng]], {
      color: '#ffb020', weight: 2, dashArray: '6 8', opacity: 0.8
    }).addTo(layerGroup);
    L.marker([a.target.lat, a.target.lng], {
      icon: L.divIcon({ className: 'target-icon', html: '<div class="target-pin">★</div>', iconSize: [34, 34], iconAnchor: [17, 17] })
    }).addTo(layerGroup);
    L.circle([a.target.lat, a.target.lng], {
      radius: CFG.HIT_R, color: '#ffb020', weight: 1.5,
      fillColor: '#ffb020', fillOpacity: 0.12
    }).addTo(layerGroup);
    map.setView([a.target.lat, a.target.lng], 15);
  }

  if (a.mode === 'route') {
    a.route.forEach((p, i) => {
      const activePt = i === a.index;
      L.marker([p.lat, p.lng], {
        icon: L.divIcon({
          className: 'target-icon',
          html: `<div class="target-pin ${activePt ? '' : 'done'}">${i + 1}</div>`,
          iconSize: [34, 34], iconAnchor: [17, 17]
        })
      }).addTo(layerGroup);
      L.circle([p.lat, p.lng], {
        radius: CFG.HIT_R, color: activePt ? '#ffb020' : '#48d18a',
        weight: 1.5, fillColor: activePt ? '#ffb020' : '#48d18a', fillOpacity: 0.12
      }).addTo(layerGroup);
    });
    const cur = a.route[a.index];
    if (cur) L.polyline([[from.lat, from.lng], [cur.lat, cur.lng]], {
      color: '#ffb020', weight: 2, dashArray: '6 8', opacity: 0.8
    }).addTo(layerGroup);
    els.hudText.textContent = `Точка ${a.index + 1} из ${a.route.length}`;
    if (cur) map.setView([cur.lat, cur.lng], 15);
  }

  const goal = currentGoal(a);
  els.btnNavigate.classList.toggle('hidden', !goal);
}

function currentGoal(a) {
  if (!a) return null;
  if (a.mode === 'circle') return null;
  if (a.mode === 'point') return a.target;
  return a.route[a.index] || null;
}

/* ---------------- обработка позиции ---------------- */

function tick(force) {
  if (!state.active || !me) return;
  const now = Date.now();
  if (!force && now - lastTick < CFG.TICK_MS) return;
  lastTick = now;

  const a = state.active;
  let ok = false;
  let dist = 0;

  if (a.mode === 'circle') {
    dist = haversine(me, a.start);
    ok = dist > CFG.CIRCLE_R + 15;
    els.hudDist.textContent = fmtDist(dist) + ' от дома';
  } else if (a.mode === 'point') {
    dist = haversine(me, a.target);
    ok = dist < CFG.HIT_R;
    els.hudDist.textContent = fmtDist(dist) + ' до точки';
  } else {
    const t = a.route[a.index];
    dist = haversine(me, t);
    ok = dist < CFG.HIT_R;
    els.hudDist.textContent = fmtDist(dist) + ' до точки ' + (a.index + 1);
  }

  if (me.acc != null && me.acc > CFG.ACC_MAX) {
    els.hudDist.textContent += ' · GPS неточный';
    return;
  }

  if (ok) {
    a.streak = (a.streak || 0) + 1;
  } else {
    a.streak = 0;
  }

  if (a.streak >= CFG.CONFIRM) {
    success();
  }
}

function success() {
  const a = state.active;
  if (!a) return;

  if (a.mode === 'route' && a.index < a.route.length - 1) {
    a.index++;
    a.streak = 0;
    save();
    drawActive();
    els.hudText.textContent = `Точка ${a.index} пройдена! Дальше к ${a.index + 1}`;
    return;
  }

  finishWalk();
}

function finishWalk() {
  const a = state.active;
  let frac = 0;
  let mode = a.mode;

  if (mode === 'circle') {
    frac = Math.min(1, Math.max(0, (haversine(me, a.start) - CFG.CIRCLE_R) / CFG.CIRCLE_R));
  } else if (mode === 'point') {
    const d = haversine(a.start, a.target);
    frac = Math.min(1, Math.max(0, (d - CFG.POINT_MIN) / (CFG.POINT_MAX - CFG.POINT_MIN)));
  } else {
    frac = 1;
  }

  rollDay();

  // награда только если дневной лимит ещё не исчерпан
  if (cardsLeftToday() <= 0) {
    state.active = null;
    save();
    layerGroup.clearLayers();
    els.hud.classList.add('hidden');
    els.btnOpenSheet.classList.remove('hidden');
    openSheet();
    els.modeHint.textContent =
      'Дневной лимит карточек исчерпан — новая карточка завтра. До завтра!';
    return;
  }

  const wasComplete = CARDS.every(c => (state.collection[c.id] || 0) > 0);
  const card = pickReward(mode, frac);
  state.collection[card.id] = (state.collection[card.id] || 0) + 1;
  // последняя выпавшая карточка — всегда первая в галерее:
  // убираем её из старой позиции и дописываем в конец order
  state.order = (state.order || []).filter(id => id !== card.id);
  state.order.push(card.id);
  if (!wasComplete && CARDS.every(c => (state.collection[c.id] || 0) > 0)) {
    pendingComplete = true;
  }
  state.walksToday = (state.walksToday || 0) + 1;
  state.walks += 1;
  state.unlocked.route = state.walks >= CFG.ROUTE_UNLOCK_WALKS;
  state.active = null;
  save();

  layerGroup.clearLayers();
  els.hud.classList.add('hidden');
  els.btnOpenSheet.classList.remove('hidden');

  renderStats();
  showCard(card);
}

/* ---------------- навигация ----------------

   Открывает Яндекс.Карты с пешеходным маршрутом (rtt=pd).
   Ключ API не нужен. */

function openNavigation() {
  const a = state.active;
  const goal = currentGoal(a);
  if (!goal) return;
  const from = me || (a && a.start);
  if (!from) return;
  const url = `https://yandex.ru/maps/?rtext=${from.lat},${from.lng}~${goal.lat},${goal.lng}&rtt=pd`;
  window.open(url, '_blank');
}

/* ---------------- интерфейс ---------------- */

function openSheet() {
  els.startSheet.classList.remove('hidden', 'compact');
  els.btnOpenSheet.classList.add('hidden');
  els.btnStart.textContent = 'Начать поиск';
  // сброс выбора
  [...els.modes.children].forEach(b => b.classList.remove('selected'));
  els.pointTools.classList.add('hidden');

  // подсказка про дом, если ты далеко от него + сколько карточек осталось на сегодня
  const away = state.home && me ? haversine(me, state.home) : 0;
  const left = cardsLeftToday();
  const lim = dailyLimit();
  const limText = `Сегодня: ${lim - left} из ${lim} карточек`;
  els.modeHint.textContent =
    (away > CFG.CIRCLE_R ? `Ты в ${fmtDist(away)} от дома — выбери, каким путём вернёшься.` : '') +
    ` ${limText}.` +
    (left > 0 ? '' : ' Лимит исчерпан — новая карточка завтра.');

  if (state.home) {
    homeLayer.clearLayers();
    L.circle([state.home.lat, state.home.lng], {
      radius: CFG.CIRCLE_R, color: '#7c5cff', weight: 2, dashArray: '4 8',
      fillColor: '#7c5cff', fillOpacity: 0.04, className: 'home-ghost'
    }).addTo(homeLayer);
  }
  clearDraft();
}

function closeSheet() {
  els.startSheet.classList.add('hidden');
  els.btnOpenSheet.classList.remove('hidden');
  clearDraft();
}

function updateModeButtons() {
  const routeBtn = els.modes.querySelector('[data-mode="route"]');
  if (!routeBtn) return;
  routeBtn.classList.toggle('locked', !state.unlocked.route);
  const lock = routeBtn.querySelector('.lock');
  if (lock) lock.hidden = state.unlocked.route;
  routeBtn.querySelector('small').textContent = state.unlocked.route
    ? `${CFG.ROUTE_LEN} точки подряд, редкая в конце`
    : `Откроется после ${CFG.ROUTE_UNLOCK_WALKS} прогулок`;
}

/* ---------------- симулятор ---------------- */

function shiftMe(distM, brg) {
  if (!me) me = { lat: CFG.DEFAULT_CENTER[0], lng: CFG.DEFAULT_CENTER[1], acc: 5 };
  const p = destination(me, distM, brg);
  me = { lat: p.lat, lng: p.lng, acc: 5 };
  simulate = true;
  updateMeMarker();
  map.panTo([me.lat, me.lng], { animate: true, duration: 0.4 });
  tick(true);
}

function simToTarget() {
  const goal = currentGoal(state.active);
  if (goal) {
    if (!me) me = { lat: CFG.DEFAULT_CENTER[0], lng: CFG.DEFAULT_CENTER[1], acc: 5 };
    me = { lat: goal.lat, lng: goal.lng, acc: 5 };
    simulate = true;
    updateMeMarker();
    tick(true);
  } else {
    shiftMe(350, Math.random() * 360);
  }
}

/* ---------------- запуск ---------------- */

function bindUi() {
  els.btnOpenSheet.addEventListener('click', openSheet);
  els.btnCloseSheet.addEventListener('click', closeSheet);

  els.modes.addEventListener('click', e => {
    const btn = e.target.closest('.mode-card');
    if (!btn) return;
    const mode = btn.dataset.mode;
    if (mode === 'route' && !state.unlocked.route) {
      els.modeHint.textContent = `Маршрут откроется после ${CFG.ROUTE_UNLOCK_WALKS} прогулок`;
      return;
    }
    selectMode(mode);
  });

  els.btnStart.addEventListener('click', startWalk);
  els.btnReroll.addEventListener('click', makeDraftPoint);
  els.btnNavigate.addEventListener('click', openNavigation);

  els.btnCancel.addEventListener('click', () => {
    if (!state.active) return;
    if (!confirm('Закончить прогулку без награды?')) return;
    state.active = null;
    save();
    layerGroup.clearLayers();
    els.hud.classList.add('hidden');
    els.btnOpenSheet.classList.remove('hidden');
  });

  els.cardInner.addEventListener('click', () => els.cardInner.classList.toggle('flipped'));
  els.btnCardOk.addEventListener('click', hideCard);

  els.btnCollection.addEventListener('click', () => {
    renderCollection();               // открываем со списка коллекций
    els.collection.classList.remove('hidden');
  });
  els.btnCollectionBack.addEventListener('click', renderCollection);
  els.btnCollectionClose.addEventListener('click', () => els.collection.classList.add('hidden'));
  els.btnCompleteOk.addEventListener('click', () => els.completeOverlay.classList.add('hidden'));

  els.btnSim350.addEventListener('click', () => {
    const a = state.active;
    if (a && a.mode === 'circle') {
      shiftMe(CFG.CIRCLE_R + 120, Math.random() * 360);
    } else if (a) {
      const goal = currentGoal(a);
      shiftMe(haversine(me, goal) + 60, bearing(me, goal));
    } else {
      shiftMe(350, Math.random() * 360);
    }
  });
  els.btnSimTarget.addEventListener('click', simToTarget);
}

function init() {
  load();
  initMap();
  bindUi();
  updateModeButtons();
  renderStats();

  // восстановить незавершённую прогулку
  if (state.active) {
    drawActive();
    els.btnOpenSheet.classList.add('hidden');
  }

  // отладка
  const debug = location.search.includes('debug') || localStorage.getItem('wc_debug') === '1';
  if (debug) {
    els.debug.classList.remove('hidden');
    if (!me) me = { lat: CFG.DEFAULT_CENTER[0], lng: CFG.DEFAULT_CENTER[1], acc: 5 };
    updateMeMarker();
  }

  startGeo();

  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('sw.js').catch(() => {});
  }
}

init();
