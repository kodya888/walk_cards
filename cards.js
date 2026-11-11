/* =========================================================
   Карточки «Гуляю-собираю»
   ---------------------------------------------------------
   Чтобы добавить нового чудика:
   1) положи его картинку в img/ (лучше SVG или WebP — лёгкие)
   2) добавь запись ниже; поле pack: 'gorod' или 'lisa'
   Идентификатор (id) должен быть уникальным.
   ========================================================= */

const CARDS = [
  /* --- ПАК 1: городской, рисунки SVG --- */
  {
    id: 'letopisets',
    name: 'Летописец двора',
    img: 'img/1_letopisets_dvora.svg',
    pack: 'gorod',
    rarity: 'common',
    desc: 'Записывает всё, что происходит во дворе с 1987 года.'
  },
  {
    id: 'smotritel',
    name: 'Ночной смотритель фонарей',
    img: 'img/2-nochnoy_smotritel_fonarey.svg',
    pack: 'gorod',
    rarity: 'common',
    desc: 'Знает, какой фонарь погаснет первым.'
  },
  {
    id: 'pirozhkov',
    name: 'Инспектор пирожков',
    img: 'img/3_inspektor_pirozhkov.svg',
    pack: 'gorod',
    rarity: 'common',
    desc: 'Проверяет начинку и следит за хрустом.'
  },

  /* --- редкие версии тех же персонажей (золотая рамка) --- */
  {
    id: 'letopisets-rare',
    name: 'Летописец двора',
    img: 'img/1_letopisets_dvora.svg',
    pack: 'gorod',
    rarity: 'rare',
    desc: 'Первый лист его летописи. Говорят, приносит удачу в поисках.'
  },
  {
    id: 'smotritel-rare',
    name: 'Ночной смотритель фонарей',
    img: 'img/2-nochnoy_smotritel_fonarey.svg',
    pack: 'gorod',
    rarity: 'rare',
    desc: 'Единственный, кто видел, как зажигается самый первый фонарь.'
  },
  {
    id: 'pirozhkov-rare',
    name: 'Инспектор пирожков',
    img: 'img/3_inspektor_pirozhkov.svg',
    pack: 'gorod',
    rarity: 'rare',
    desc: 'Золотой значок за безупречную проверку 10 000 пирожков.'
  },

  /* --- ПАК 2: осенняя лиса, рисунки иллюстратора (WebP) --- */
  {
    id: 'borovik',
    name: 'Боровик-молчун',
    img: 'img/lisa/01_borovik.webp',
    pack: 'lisa',
    rarity: 'common',
    desc: 'Сидит в траве и всё слышит. Никому не рассказывает, но улыбается.'
  },
  {
    id: 'shapka-lisichka',
    name: 'Шапка-лисичка',
    img: 'img/lisa/02_shapka_lisichka.webp',
    pack: 'lisa',
    rarity: 'common',
    desc: 'Думает, что она шапка. Другие лисы вежливо не спорят.'
  },
  {
    id: 'lisa-ryaninushka',
    name: 'Лиса-рябинушка',
    img: 'img/lisa/03_lisa_ryaninushka.webp',
    pack: 'lisa',
    rarity: 'common',
    desc: 'Приносит рябину тому, кто идёт с добром. Проверено.'
  },
  {
    id: 'progulshchitsa',
    name: 'Прогульщица',
    img: 'img/lisa/04_progulshchitsa.webp',
    pack: 'lisa',
    rarity: 'common',
    desc: 'Ушла по листу и не собирается объясняться.'
  },
  {
    id: 'zheludekhranitelnitsa',
    name: 'Жёлудехранительница',
    img: 'img/lisa/05_zheludekhranitelnitsa.webp',
    pack: 'lisa',
    rarity: 'common',
    desc: 'Считает каждый жёлудь. Сбилась со счёта — начала заново.'
  },
  {
    id: 'kruzhka-dlya-dvoih',
    name: 'Кружка для двоих',
    img: 'img/lisa/06_kruzhka_dlya_dvoih.webp',
    pack: 'lisa',
    rarity: 'rare',
    desc: 'Пар поднимается сердечком, когда рядом тот, с кем хорошо.'
  },
  {
    id: 'tykolub',
    name: 'Тыколюб',
    img: 'img/lisa/07_tykolub.webp',
    pack: 'lisa',
    rarity: 'common',
    desc: 'Обнял тыкву и понял: это тыква обняла его.'
  },
  {
    id: 'sbortsitca-nalivnyh',
    name: 'Сборщица наливных',
    img: 'img/lisa/08_sbortsitca_nalivnyh.webp',
    pack: 'lisa',
    rarity: 'common',
    desc: 'Несёт яблоки аккуратно: каждое уже выбрало своего хозяина.'
  },
  {
    id: 'hodoka-pod-goroshek',
    name: 'Ходока под горошек',
    img: 'img/lisa/09_hodoka_pod_goroshek.webp',
    pack: 'lisa',
    rarity: 'common',
    desc: 'Дождь для неё — повод, а не помеха.'
  },
  {
    id: 'sviter-domik',
    name: 'Свитер-домик',
    img: 'img/lisa/10_sviter_domik.webp',
    pack: 'lisa',
    rarity: 'common',
    desc: 'Свитер связан так удачно, что лиса в нём живёт. Прописана.'
  },
  {
    id: 'tykvenny-vsadnik',
    name: 'Тыквенный всадник',
    img: 'img/lisa/11_tykvenny_vsadnik.webp',
    pack: 'lisa',
    rarity: 'rare',
    desc: 'Едет тихо: тыква не любит галопа.'
  },
  {
    id: 'zont-v-goroshek',
    name: 'Зонт в горошек',
    img: 'img/lisa/12_zont_v_goroshek.webp',
    pack: 'lisa',
    rarity: 'common',
    desc: 'Открывается только для тех, кто не суетится.'
  },
  {
    id: 'buketodarka',
    name: 'Букетодарка',
    img: 'img/lisa/13_buketodarka.webp',
    pack: 'lisa',
    rarity: 'common',
    desc: 'Нарвала букет из листьев. В букете — весь ноябрь.'
  },
  {
    id: 'chitatel-pod-pledom',
    name: 'Читатель под пледом',
    img: 'img/lisa/14_chitatel_pod_pledom.webp',
    pack: 'lisa',
    rarity: 'rare',
    desc: 'Читает и греется. Гений многозадачности.'
  },
  {
    id: 'fonarshchitsa-s-ryabinoi',
    name: 'Фонарщица с рябиной',
    img: 'img/lisa/15_fonarshchitsa_s_ryabinoi.webp',
    pack: 'lisa',
    rarity: 'common',
    desc: 'Зажигает фонарь и оставляет рядом рябину — для тех, кто ночью идёт домой.'
  },
  {
    id: 'gerbarii',
    name: 'Осенний гербарий',
    img: 'img/lisa/16_gerbarii.webp',
    pack: 'lisa',
    rarity: 'common',
    desc: 'Собран медленно, с чаем. Хранит запах самой красивой прогулки.'
  },
  {
    id: 'gurman-degustator',
    name: 'Гурман-дегустатор',
    img: 'img/lisa/17_gurman_degustator.webp',
    pack: 'lisa',
    rarity: 'common',
    desc: 'Съел гриб и отметил: «со вкусом осени». Тот самый гриб.'
  },
  {
    id: 'sapogi-poprygunyi',
    name: 'Сапоги-попрыгуньи',
    img: 'img/lisa/18_sapogi_poprygunyi.webp',
    pack: 'lisa',
    rarity: 'common',
    desc: 'Сами прыгают в лужи. Владельцу остаётся держаться.'
  },
  {
    id: 'kokon-so-vkusom',
    name: 'Кокон со вкусом',
    img: 'img/lisa/19_kokon_so_vkusom.webp',
    pack: 'lisa',
    rarity: 'common',
    desc: 'Плед, чай и никакой спешки. Выдаётся тем, кто дошёл.'
  },
  {
    id: 'luzheprohodets',
    name: 'Лужепроходец',
    img: 'img/lisa/20_luzheprohodets.webp',
    pack: 'lisa',
    rarity: 'rare',
    desc: 'Проверил каждую лужу на маршруте. Ни одна не укрылась.'
  },
  {
    id: 'ryabinovyi-adres',
    name: 'Рябиновый адрес',
    img: 'img/lisa/21_ryabinovyi_adres.webp',
    pack: 'lisa',
    rarity: 'common',
    desc: 'Ветка указывает на дом, где пахнет пирогами.'
  },
  {
    id: 'kudryavaya-tykva',
    name: 'Кудрявая тыква',
    img: 'img/lisa/22_kudryavaya_tykva.webp',
    pack: 'lisa',
    rarity: 'common',
    desc: 'С утра сделала завивку. Весь двор ахнул.'
  },
  {
    id: 'gribnaya-kurerka',
    name: 'Грибная курьерка',
    img: 'img/lisa/23_gribnaya_kurerka.webp',
    pack: 'lisa',
    rarity: 'common',
    desc: 'Доставит корзину до подъезда. Сдачи не берёт — берёт гриб.'
  },
  {
    id: 'sviter-obnimashka',
    name: 'Свитер-обнимашка',
    img: 'img/lisa/24_sviter_obnimashka.webp',
    pack: 'lisa',
    rarity: 'common',
    desc: 'Связан из трёх носков и одной надежды. Греет как сто одеял.'
  },
  {
    id: 'masteritsa',
    name: 'Мастерица-лисичка',
    img: 'img/lisa/25_masteritsa.webp',
    pack: 'lisa',
    rarity: 'rare',
    desc: 'Вяжет шарф длиной в прогулку. Довяжет — осень закончится.'
  }
];

const CARD_BY_ID = Object.fromEntries(CARDS.map(c => [c.id, c]));

/**
 * Выбрать карточку-награду.
 * mode: 'circle' | 'point' | 'route'
 * frac: насколько далеко ушёл от минимума (0..1) — чем дальше, тем выше шанс редкой
 *
 * Правило: пока карточка не собрана, дубли не падают («пока не кончатся»).
 * Когда всё собрано — снова падают любые.
 */
function pickReward(mode, frac = 0) {
  const owns = (typeof state !== 'undefined' && state.collection) || {};
  const notOwned = c => !(owns[c.id] > 0);

  const commons = CARDS.filter(c => c.rarity === 'common').filter(notOwned);
  const rares   = CARDS.filter(c => c.rarity === 'rare').filter(notOwned);

  let rareChance = 0;
  if (mode === 'point') rareChance = 0.15 + 0.35 * frac;   // 15–50 %
  if (mode === 'route') rareChance = 1;                     // маршрут — всегда редкая

  let pool = (Math.random() < rareChance) ? rares : commons;
  if (!pool.length) pool = rares.length ? rares : commons;

  // совсем всё собрано — падают любые (дубли)
  if (!pool.length) pool = CARDS;
  return pool[Math.floor(Math.random() * pool.length)];
}
