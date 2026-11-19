'use strict';

/* =========================================================
   Гуляю-собираю — логика
   ========================================================= */

const CFG = {
  CIRCLE_R: 250,          // радиус круга квеста «выйди за круг», м
  ACC_MAX: 60,            // замеры с точностью хуже 60 м не засчитываем
  CONFIRM: 2,             // сколько замеров подряд нужно для срабатывания
  TICK_MS: 4000,          // как часто обрабатывать позицию
  LIMITS_ENABLED: false,  // дневной лимит выключен (для теста; вернуть, когда появится монетизация)
  LIMIT_TIERS: [          // дневной лимит карточек по «прокачке» (всего прогулок)
    { from: 0,  limit: 2 },
    { from: 5,  limit: 3 },
    { from: 15, limit: 4 },
    { from: 30, limit: 5 }
    // анлим — в будущем за купленный пак (снимать лимит через флаг в save)
  ],
  ZOOM: 15.8,             // стартовый масштаб: круг 250 м чуть меньше экрана
  ZOOM_SNAP: 0,           // разрешаем дробный зум (иначе 15.8 округлится до 16)
  DEFAULT_CENTER: [56.3269, 44.0059] // Нижний Новгород
};

const STORE_KEY = 'walk_cards_v1';

/* ---------------- состояние ---------------- */

let state = {
  collection: {},                 // id карточки -> сколько раз попадалась
  order: [],                      // id карточек в порядке получения (для галереи)
  giftsAccepted: [],              // канонические подарочные коды, принятые на этом телефоне
  walks: 0,
  walksToday: 0,                  // карточек за сегодня
  day: '',                        // 'ГГГГ-ММ-ДД' — сброс дневного счётчика
  active: null                    // текущая прогулка
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
  if (!Array.isArray(state.giftsAccepted)) state.giftsAccepted = [];
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
  if (!CFG.LIMITS_ENABLED) return Infinity;
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
  btnCancel: $('btn-cancel'),
  btnGo: $('btn-go'),
  goHint: $('go-hint'),
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
  cardHint: $('card-hint'),
  collection: $('collection'),
  collectionTitle: $('collection-title'),
  collectionGrid: $('collection-grid'),
  collectionProgress: $('collection-progress'),
  packsList: $('packs-list'),
  packView: $('pack-view'),
  btnCollectionBack: $('btn-collection-back'),
  btnCollectionClose: $('btn-collection-close'),
  completeOverlay: $('complete-overlay'),
  rewardOverlay: $('reward-overlay'),
  rewardRow: $('reward-row'),
  rewardHint: $('reward-hint'),
  btnRewardOk: $('btn-reward-ok'),
  btnCompleteOk: $('btn-complete-ok'),
  btnGift: $('btn-gift'),
  btnCardGift: $('btn-card-gift'),
  giftOverlay: $('gift-overlay'),
  giftConfirmView: $('gift-confirm-view'),
  giftCodeView: $('gift-code-view'),
  giftInputView: $('gift-input-view'),
  giftCardname: $('gift-cardname'),
  giftWarn: $('gift-warn'),
  giftCodeName: $('gift-code-name'),
  giftCode: $('gift-code'),
  giftInput: $('gift-input'),
  giftMsg: $('gift-msg'),
  btnGiftYes: $('btn-gift-yes'),
  btnGiftNo: $('btn-gift-no'),
  btnGiftCopy: $('btn-gift-copy'),
  btnGiftShare: $('btn-gift-share'),
  btnGiftDone: $('btn-gift-done'),
  btnGiftAccept: $('btn-gift-accept'),
  btnGiftCancel: $('btn-gift-cancel'),
  debug: $('debug'),
  btnSim350: $('btn-sim-350')
};

/* ---------------- карта ---------------- */

let map = null;
let meMarker = null;
let layerGroup = null;      // всё, что относится к активной прогулке
let homeLayer = null;       // «спокойный» круг главного экрана
let openPackKey = null;     // какой пак открыт в галерее (null — список паков)

let me = null;              // {lat,lng,acc}
let simulate = false;       // включён ли симулятор
let lastTick = 0;
let watchId = null;

function initMap() {
  map = L.map('map', {
    zoomControl: false,
    attributionControl: true,
    zoomSnap: CFG.ZOOM_SNAP
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
  if (!state.active) {
    // квест не идёт — круг «наводится» на тебя, карта следует
    map.panTo([me.lat, me.lng], { animate: true, duration: 0.6 });
    drawIdleCircle();
  }
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
let galleryList = [];          // карточки открытого пака в галерее — порядок как на экране
let galleryIndex = -1;         // какая из них показана в большом оверлее

function swipeGallery(step) {
  // листание по кругу: от последней — к первой и наоборот
  if (!cardFromGallery || !galleryList.length) return;
  galleryIndex = (galleryIndex + step + galleryList.length) % galleryList.length;
  showCard(galleryList[galleryIndex], true);
}

/* у каждого пака — своя рубашка: фон, узор и круглый знак задаёт CSS
   по data-pack. Надписей на рубашке нет. */

/** Показ большой карточки. fromGallery=true — открыт из коллекции (обычный просмотр) */
function showCard(card, fromGallery = false) {
  currentCard = card;
  cardFromGallery = fromGallery;
  if (fromGallery) galleryIndex = galleryList.indexOf(card);
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
  els.btnCardGift.classList.toggle('hidden', !fromGallery);
  els.cardHint.textContent = fromGallery
    ? 'Листай влево-вправо · тап — перевернуть'
    : 'Нажми на карточку — она перевернётся';
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

/* ---------------- награда за прогулку: открытие карточек ---------------- */

/* Карточки падают по одной, рубашкой вверх, в большом размере.
   Первый тап — карточка переворачивается. Второй тап — улетает вверх,
   падает следующая. Последняя улетела — появляется «Забрать». */

function showRewards(cards) {
  let idx = 0;
  els.btnRewardOk.classList.add('hidden');
  els.rewardHint.textContent = 'Нажми на карточку — она откроется';
  els.rewardHint.classList.remove('hidden');
  els.rewardRow.classList.remove('mini');

  function renderCurrent() {
    const card = cards[idx];
    const pack = card.pack || 'gorod';
    const no = String(CARDS.indexOf(card) + 1).padStart(2, '0');
    els.rewardRow.innerHTML = '';
    const shell = document.createElement('div');
    shell.className = 'reward-shell';
    shell.innerHTML =
      '<div class="card-inner flipped">' +
        '<div class="face card-front' + (card.rarity === 'rare' ? ' rare' : '') + '" data-pack="' + pack + '">' +
          '<span class="card-no">№ ' + no + '</span>' +
          '<div class="card-scene"><img src="' + card.img + '" alt=""></div>' +
          '<div class="card-text">' + card.name + '</div>' +
          '<span class="card-rarity">' + (card.rarity === 'rare' ? '★ редкая' : 'обычная') + '</span>' +
        '</div>' +
        '<div class="face card-back" data-pack="' + pack + '">' +
          '<div class="card-back-inner"><div class="card-back-mark"></div></div>' +
        '</div>' +
      '</div>';
    shell.addEventListener('click', () => {
      // первый тап — открыть, второй тап — улетела
      if (!shell.classList.contains('opened')) {
        shell.classList.add('opened');
        shell.querySelector('.card-inner').classList.remove('flipped');
        els.rewardHint.textContent = 'Нажми ещё раз — она улетит';
        return;
      }
      shell.classList.add('fly-out');
      if (idx + 1 < cards.length) {
        idx++;
        setTimeout(renderCurrent, 500);
      } else {
        // все карточки выпали — показываем их горизонтальный ряд
        setTimeout(renderMiniRow, 500);
      }
    });
    els.rewardRow.appendChild(shell);
  }

  /* финал награды: маленькие карточки лицом вверх в ряд, падают по очереди */
  function renderMiniRow() {
    els.rewardRow.innerHTML = '';
    els.rewardRow.classList.add('mini');
    els.rewardHint.textContent = 'Прогулка принесла:';
    cards.forEach((card, i) => {
      const pack = card.pack || 'gorod';
      const no = String(CARDS.indexOf(card) + 1).padStart(2, '0');
      const shell = document.createElement('div');
      shell.className = 'reward-mini';
      shell.style.animationDelay = (i * 0.12).toFixed(2) + 's';
      shell.innerHTML =
        '<div class="card-inner">' +
          '<div class="face card-front' + (card.rarity === 'rare' ? ' rare' : '') + '" data-pack="' + pack + '">' +
            '<span class="card-no">№ ' + no + '</span>' +
            '<div class="card-scene"><img src="' + card.img + '" loading="lazy" alt=""></div>' +
            '<div class="card-text">' + card.name + '</div>' +
            '<span class="card-rarity">' + (card.rarity === 'rare' ? '★ редкая' : 'обычная') + '</span>' +
          '</div>' +
        '</div>';
      els.rewardRow.appendChild(shell);
    });
    // подгоняем шрифт названий: самое длинное слово должно влезать
    // в мини-карточку, уменьшаем шрифт пропорционально (максимум 11px, пол 6.5px)
    els.rewardRow.querySelectorAll('.reward-mini').forEach(m => {
      const t = m.querySelector('.card-text');
      const inner = t.clientWidth - 9;              // паддинги 2px 4px + запас
      if (inner < 20) return;
      const cs = getComputedStyle(t);
      const probe = document.createElement('span');
      probe.style.cssText = 'position:absolute;visibility:hidden;white-space:nowrap;font-weight:' + cs.fontWeight + ';font-family:' + cs.fontFamily + ';font-size:11px';
      document.body.appendChild(probe);
      let maxW = 0;
      t.textContent.split(/\s+/).forEach(w => {
        probe.textContent = w;
        const wd = probe.getBoundingClientRect().width;
        if (wd > maxW) maxW = wd;
      });
      probe.remove();
      if (maxW > inner) t.style.fontSize = Math.max(6.5, Math.floor(11 * inner / maxW * 10) / 10) + 'px';
    });
    els.btnRewardOk.classList.remove('hidden');
  }

  renderCurrent();
  els.rewardOverlay.classList.remove('hidden');
}

function hideRewards() {
  els.rewardOverlay.classList.add('hidden');
  if (pendingComplete) {
    // всё собрано — после награды показываем поздравление
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
  el.innerHTML = `<img src="${card.img}" alt="" loading="lazy" decoding="async"><div>${card.name}</div><small class="mini-no">№ ${String(CARDS.indexOf(card) + 1).padStart(2, '0')}</small>`;
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
  openPackKey = null;
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
  openPackKey = key;
  els.packsList.classList.add('hidden');
  els.packView.classList.remove('hidden');
  els.collectionGrid.innerHTML = '';

  // state.order хранит порядок получения. Показываем наоборот:
  // последняя выпавшая карточка — первой в верхнем ряду.
  const order = state.order
    .filter(id => CARD_BY_ID[id] && state.collection[id] > 0 &&
                  (CARD_BY_ID[id].pack || 'gorod') === key)
    .reverse();

  // список для листания влево-вправо в большом оверлее
  galleryList = order.map(id => CARD_BY_ID[id]);

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

/* ---------------- старт / главный экран ---------------- */

/* «Спокойный» круг главного экрана: рисуется вокруг тебя до старта.
   Пока квест не начат — центрируется по GPS; после «Вперед» круг
   замирает на месте, двигается только точка. */
function drawIdleCircle() {
  if (!me || state.active) return;
  homeLayer.clearLayers();
  L.circle([me.lat, me.lng], {
    radius: CFG.CIRCLE_R, color: '#7c5cff', weight: 2,
    fillColor: '#7c5cff', fillOpacity: 0.05, className: 'home-ring'
  }).addTo(homeLayer);
}

/** Вернуть главный экран: круг вокруг тебя + кнопка «Вперед». */
function showMainScreen() {
  layerGroup.clearLayers();
  els.hud.classList.add('hidden');
  els.btnGo.classList.remove('hidden');
  els.goHint.classList.remove('hidden');
  els.goHint.textContent = 'Выйди за круг';
  drawIdleCircle();
}

function startWalk() {
  if (!me) {
    els.goHint.textContent = 'Жду координаты GPS… включи геолокацию.';
    return;
  }

  rollDay();
  if (cardsLeftToday() <= 0) {
    els.goHint.textContent =
      'Дневной лимит карточек исчерпан — новая карточка завтра. ' +
      'Гуляешь дальше ради удовольствия? Прогулка без награды: «Закончить» сейчас.';
    return;
  }

  state.active = { mode: 'circle', start: { lat: me.lat, lng: me.lng }, streak: 0 };
  save();
  homeLayer.clearLayers();
  drawActive();
  tick(true);
}

/* ---------------- отрисовка активной прогулки ---------------- */

function drawActive() {
  layerGroup.clearLayers();
  const a = state.active;
  if (!a) return;

  els.btnGo.classList.add('hidden');
  els.goHint.classList.add('hidden');
  els.hud.classList.remove('hidden');
  els.hudDist.textContent = '';
  els.hudText.textContent = 'Выйди за круг';

  // круг замирает на месте старта (точка GPS идёт дальше)
  L.circle([a.start.lat, a.start.lng], {
    radius: CFG.CIRCLE_R, color: '#7c5cff', weight: 2,
    fillColor: '#7c5cff', fillOpacity: 0.05, className: 'home-ring'
  }).addTo(layerGroup);

  map.setView([a.start.lat, a.start.lng], CFG.ZOOM);
}

/* ---------------- обработка позиции ---------------- */

function tick(force) {
  if (!state.active || !me) return;
  const now = Date.now();
  if (!force && now - lastTick < CFG.TICK_MS) return;
  lastTick = now;

  const a = state.active;
  const dist = haversine(me, a.start);
  const ok = dist > CFG.CIRCLE_R + 15;
  els.hudDist.textContent = fmtDist(dist) + ' от центра';

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

  /* вибрация события (Android Chrome; iOS Safari не поддерживает — молча пропускаем).
     Выход за круг — двойной «тук-тук». */
  try {
    if (navigator.vibrate) navigator.vibrate([110, 100, 110]);
  } catch (e) { /* вибрация недоступна — не важно */ }

  finishWalk();
}

function finishWalk() {
  const a = state.active;
  const frac = Math.min(1, Math.max(0, (haversine(me, a.start) - CFG.CIRCLE_R) / CFG.CIRCLE_R));

  rollDay();

  // награда только если дневной лимит ещё не исчерпан
  if (cardsLeftToday() <= 0) {
    state.active = null;
    save();
    showMainScreen();
    els.goHint.textContent =
      'Дневной лимит карточек исчерпан — новая карточка завтра. До завтра!';
    return;
  }

  const wasComplete = CARDS.every(c => (state.collection[c.id] || 0) > 0);
  const cards = pickRewards('circle', frac);   // до 3 карточек, по одной из пака
  cards.forEach(card => {
    state.collection[card.id] = (state.collection[card.id] || 0) + 1;
    // последняя выпавшая карточка — всегда первая в галерее:
    // убираем её из старой позиции и дописываем в конец order
    state.order = (state.order || []).filter(id => id !== card.id);
    state.order.push(card.id);
  });
  if (!wasComplete && CARDS.every(c => (state.collection[c.id] || 0) > 0)) {
    pendingComplete = true;
  }
  state.walksToday = (state.walksToday || 0) + 1;
  state.walks += 1;
  state.active = null;
  save();

  showMainScreen();
  renderStats();
  showRewards(cards);
}

/* ---------------- симулятор ---------------- */

function shiftMe(distM, brg) {
  if (!me) me = { lat: CFG.DEFAULT_CENTER[0], lng: CFG.DEFAULT_CENTER[1], acc: 5 };
  const p = destination(me, distM, brg);
  me = { lat: p.lat, lng: p.lng, acc: 5 };
  simulate = true;
  updateMeMarker();
  drawIdleCircle();
  map.panTo([me.lat, me.lng], { animate: true, duration: 0.4 });
  tick(true);
}

/* ---------------- обмен: подарочные коды ----------------

   Подарок по коду, без сервера: все 72 карточки вшиты в cards.js на
   каждом телефоне, передаётся только номер. Код = «пак-номер-слово»
   (ЧУДИКИ-7-АИСТ): номер внутри пака + контрольное слово, чтобы
   ошибка при диктовке/перепечатке не дарила чужую карточку.
   Подарил — карточка ушла (collection -1, вплоть до нуля): пак с
   дыркой снова начинает выпадать, «заработай заново». */

const GIFT_WORD = {
  gorod: { word: 'ЧУДИКИ', also: ['ГОРОД'] },
  lisa:  { word: 'ОСЕНЬ',  also: ['ЛИСА', 'ЛИСИЧКА'] },
  zima:  { word: 'ЗИМА',   also: ['ЗИМНИЙ'] },
  kot:   { word: 'КОТ',    also: ['КОШКА', 'КОТИК'] }
};
const GIFT_CHECK = ['АИСТ', 'БОБР', 'ВОЛК', 'ГНОМ', 'ДЫНЯ', 'ЕРШ'];

const giftPackCards = key => CARDS.filter(c => (c.pack || 'gorod') === key);

/** Код карточки: пак-номер-контрольное слово. */
function encodeGiftCode(card) {
  const key = card.pack || 'gorod';
  const n = giftPackCards(key).indexOf(card) + 1;
  return GIFT_WORD[key].word + '-' + n + '-' + GIFT_CHECK[(CARDS.indexOf(card) + n) % 6];
}

/** Разбор кода: латинские двойники -> кириллица, номера и слова по отдельности. */
function decodeGiftCode(raw) {
  let s = String(raw || '').toUpperCase();
  const lat = { A: 'А', B: 'В', C: 'С', E: 'Е', H: 'Н', K: 'К', M: 'М',
                O: 'О', P: 'Р', T: 'Т', X: 'Х' };
  s = s.replace(/[ABCEHKMOPTX]/g, ch => lat[ch]);
  const words = [], nums = [];
  (s.match(/[А-ЯЁ]+|\d+/g) || []).forEach(t => {
    if (/^\d+$/.test(t)) nums.push(parseInt(t, 10)); else words.push(t);
  });
  if (!words.length || !nums.length)
    return { error: 'Не похоже на код. Спроси у друга ещё раз.' };
  if (words.length < 2)
    return { error: 'Добавь контрольное слово в конце — например: ЧУДИКИ-7-АИСТ.' };
  const key = Object.keys(GIFT_WORD).find(k =>
    GIFT_WORD[k].word === words[0] || GIFT_WORD[k].also.includes(words[0]));
  if (!key)
    return { error: 'Не знаю коллекцию «' + words[0] + '». Проверь первое слово.' };
  const n = nums[0];
  const inPack = giftPackCards(key);
  if (n < 1 || n > inPack.length)
    return { error: 'Такого номера нет в коллекции. Проверь код.' };
  const card = inPack[n - 1];
  const check = GIFT_CHECK[(CARDS.indexOf(card) + n) % 6];
  if (words[1] !== check)
    return { error: 'Код не сходится — проверь номер и слово.' };
  return { card };
}

let giftCard = null;   // карточка, чей код уже показан (она уже ушла)

function showGiftView(v) {
  els.giftConfirmView.classList.toggle('hidden', v !== 'confirm');
  els.giftCodeView.classList.toggle('hidden', v !== 'code');
  els.giftInputView.classList.toggle('hidden', v !== 'input');
  els.giftOverlay.classList.remove('hidden');
}

function openGiftConfirm(card) {
  giftCard = null;
  const n = state.collection[card.id] || 0;
  els.giftCardname.textContent = '«' + card.name + '»';
  els.giftWarn.classList.toggle('hidden', n > 1);
  showGiftView('confirm');
}

/** Подарил = расстался: счётчик -1, при нуле карточка уходит и из галереи. */
function doGift(card) {
  const n = state.collection[card.id] || 0;
  if (n <= 1) {
    delete state.collection[card.id];
    state.order = (state.order || []).filter(id => id !== card.id);
  } else {
    state.collection[card.id] = n - 1;
  }
  save();
  giftCard = card;
  els.giftCodeName.textContent = '«' + card.name + '»';
  els.giftCode.textContent = encodeGiftCode(card);
  showGiftView('code');
  try { if (navigator.vibrate) navigator.vibrate(60); } catch (e) {}
}

/** Закрыть обмен. Если код был выдан — вернуть юзера в обновлённую галерею. */
function closeGift() {
  els.giftOverlay.classList.add('hidden');
  if (!giftCard) return;
  giftCard = null;
  els.cardOverlay.classList.add('hidden');
  currentCard = null;
  cardFromGallery = false;
  els.collection.classList.remove('hidden');
  if (openPackKey) openPack(openPackKey); else renderCollection();
  renderStats();
}

function copyGiftCode() {
  const code = els.giftCode.textContent;
  const done = () => {
    els.btnGiftCopy.textContent = 'Скопировано ✓';
    setTimeout(() => { els.btnGiftCopy.textContent = 'Скопировать код'; }, 1600);
  };
  const fallback = () => {
    const ta = document.createElement('textarea');
    ta.value = code;
    document.body.appendChild(ta);
    ta.select();
    try { document.execCommand('copy'); done(); } catch (e) {}
    ta.remove();
  };
  if (navigator.clipboard && navigator.clipboard.writeText)
    navigator.clipboard.writeText(code).then(done).catch(fallback);
  else fallback();
}

function giftShare() {
  const code = els.giftCode.textContent;
  if (navigator.share) {
    navigator.share({
      title: 'Гуляю-собираю — подарок!',
      text: 'Дарю тебе карточку! Введи код: ' + code
    }).catch(() => {});
  } else {
    copyGiftCode();
  }
}

/* приём: разобрать код, отметить как принятый, выдать карточку */
function acceptGiftDraft() {
  const res = decodeGiftCode(els.giftInput.value);
  const msg = els.giftMsg;
  msg.className = 'gift-msg';
  if (res.error) {
    msg.textContent = res.error;
    msg.classList.add('err');
    return;
  }
  const canonical = encodeGiftCode(res.card);
  if (state.giftsAccepted.includes(canonical)) {
    msg.textContent = 'Такой подарок уже принимали на этом телефоне.';
    msg.classList.add('err');
    return;
  }
  const wasComplete = CARDS.every(c => (state.collection[c.id] || 0) > 0);
  state.collection[res.card.id] = (state.collection[res.card.id] || 0) + 1;
  state.order = (state.order || []).filter(id => id !== res.card.id);
  state.order.push(res.card.id);
  state.giftsAccepted.push(canonical);
  save();
  renderStats();
  els.giftOverlay.classList.add('hidden');
  els.giftInput.value = '';
  msg.textContent = '';
  try { if (navigator.vibrate) navigator.vibrate([90, 80, 90]); } catch (e) {}
  showCard(res.card, false);
  if (!wasComplete && CARDS.every(c => (state.collection[c.id] || 0) > 0)) {
    pendingComplete = true;
  }
}

/* ---------------- заставка ---------------- */

function initSplash() {
  const s = $('splash');
  if (!s) return;
  const debug = location.search.includes('debug') || localStorage.getItem('wc_debug') === '1';
  if (debug) { s.remove(); return; }
  const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  let faded = false;
  const skip = () => {
    if (faded) return;
    faded = true;
    s.classList.add('splash-done');
    setTimeout(() => { if (s.parentNode) s.remove(); }, 520);
  };
  s.addEventListener('click', skip);
  setTimeout(skip, reduce ? 400 : 2450);
  // страховка: даже если что-то пошло не так, заставка исчезнет
  setTimeout(() => { if (s.parentNode) s.remove(); }, 3400);
}

/* ---------------- запуск ---------------- */

function bindUi() {
  els.btnGo.addEventListener('click', startWalk);

  els.btnCancel.addEventListener('click', () => {
    if (!state.active) return;
    if (!confirm('Закончить прогулку без награды?')) return;
    state.active = null;
    save();
    showMainScreen();
  });

  els.cardInner.addEventListener('click', () => els.cardInner.classList.toggle('flipped'));
  els.btnCardOk.addEventListener('click', hideCard);

  // листание большой карточки свайпом влево-вправо (из галереи)
  let swipeX = null, swipeY = null;
  els.cardOverlay.addEventListener('touchstart', e => {
    const t = e.changedTouches[0];
    swipeX = t.clientX; swipeY = t.clientY;
  }, { passive: true });
  els.cardOverlay.addEventListener('touchend', e => {
    if (swipeX === null) return;
    const t = e.changedTouches[0];
    const dx = t.clientX - swipeX, dy = t.clientY - swipeY;
    swipeX = null;
    if (!cardFromGallery) return;
    // короткий или вертикальный жест не считается: это тап или скролл
    if (Math.abs(dx) < 45 || Math.abs(dx) < Math.abs(dy) * 1.3) return;
    swipeGallery(dx < 0 ? 1 : -1);   // влево — следующая, вправо — предыдущая
  });
  // то же с клавиатуры, чтобы проверять на компе
  document.addEventListener('keydown', e => {
    if (els.cardOverlay.classList.contains('hidden') || !cardFromGallery) return;
    if (e.key === 'ArrowRight') swipeGallery(1);
    if (e.key === 'ArrowLeft') swipeGallery(-1);
  });
  els.btnRewardOk.addEventListener('click', hideRewards);

  els.btnCollection.addEventListener('click', () => {
    renderCollection();               // открываем со списка коллекций
    els.collection.classList.remove('hidden');
  });
  els.btnCollectionBack.addEventListener('click', renderCollection);
  els.btnCollectionClose.addEventListener('click', () => els.collection.classList.add('hidden'));
  els.btnCompleteOk.addEventListener('click', () => els.completeOverlay.classList.add('hidden'));

  // обмен
  els.btnGift.addEventListener('click', () => {
    els.giftInput.value = '';
    els.giftMsg.className = 'gift-msg';
    els.giftMsg.textContent = '';
    showGiftView('input');
  });
  els.btnGiftAccept.addEventListener('click', acceptGiftDraft);
  els.giftInput.addEventListener('keydown', e => { if (e.key === 'Enter') acceptGiftDraft(); });
  els.btnGiftCancel.addEventListener('click', closeGift);
  els.btnCardGift.addEventListener('click', () => { if (currentCard) openGiftConfirm(currentCard); });
  els.btnGiftYes.addEventListener('click', () => { if (currentCard) doGift(currentCard); });
  els.btnGiftNo.addEventListener('click', closeGift);
  els.btnGiftCopy.addEventListener('click', copyGiftCode);
  els.btnGiftShare.addEventListener('click', giftShare);
  els.btnGiftDone.addEventListener('click', closeGift);
  // «Поделиться» показываем, только если браузер умеет нативный шаринг
  if (!navigator.share) els.btnGiftShare.classList.add('hidden');
  else els.btnGiftShare.classList.remove('hidden');

  els.btnSim350.addEventListener('click', () => {
    shiftMe(CFG.CIRCLE_R + 120, Math.random() * 360);
  });
}

function init() {
  load();
  initSplash();
  initMap();
  bindUi();
  renderStats();

  // подарок пришёл ссылкой (?gift=ЧУДИКИ-7-АИСТ) — открываем ввод кода
  const giftParam = new URLSearchParams(location.search).get('gift');
  if (giftParam) {
    els.giftInput.value = giftParam;
    showGiftView('input');
  }

  // восстановить незавершённую прогулку
  if (state.active) {
    drawActive();
  }

  // отладка
  const debug = location.search.includes('debug') || localStorage.getItem('wc_debug') === '1';
  if (debug) {
    els.debug.classList.remove('hidden');
    if (!me) me = { lat: CFG.DEFAULT_CENTER[0], lng: CFG.DEFAULT_CENTER[1], acc: 5 };
    updateMeMarker();
    drawIdleCircle();
  }

  startGeo();

  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('sw.js').catch(() => {});
  }
}

init();
