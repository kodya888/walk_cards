/* =========================================================
   Карточки «Гуляю-собираю»
   ---------------------------------------------------------
   Чтобы добавить нового чудика:
   1) положи его картинку в img/ (лучше SVG или WebP — лёгкие)
   2) добавь запись ниже; поле pack: 'gorod' | 'lisa' | 'zima'
   Идентификатор (id) должен быть уникальным.
   Поле desc необязательное: если его нет, карточка показывает
   только название и редкость.
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

  /* --- ПАК 2 «Лисичка.Осень»: рисунки иллюстратора (WebP),
         без описаний — только названия --- */
  {
    id: 'borovik',
    name: 'Боровик-молчун',
    img: 'img/lisa/01_borovik.webp',
    pack: 'lisa',
    rarity: 'common'
  },
  {
    id: 'shapka-lisichka',
    name: 'Шапка-лисичка',
    img: 'img/lisa/02_shapka_lisichka.webp',
    pack: 'lisa',
    rarity: 'common'
  },
  {
    id: 'lisa-ryaninushka',
    name: 'Лиса-рябинушка',
    img: 'img/lisa/03_lisa_ryaninushka.webp',
    pack: 'lisa',
    rarity: 'common'
  },
  {
    id: 'progulshchitsa',
    name: 'Прогульщица',
    img: 'img/lisa/04_progulshchitsa.webp',
    pack: 'lisa',
    rarity: 'common'
  },
  {
    id: 'zheludekhranitelnitsa',
    name: 'Жёлудехранительница',
    img: 'img/lisa/05_zheludekhranitelnitsa.webp',
    pack: 'lisa',
    rarity: 'common'
  },
  {
    id: 'kruzhka-dlya-dvoih',
    name: 'Кружка для двоих',
    img: 'img/lisa/06_kruzhka_dlya_dvoih.webp',
    pack: 'lisa',
    rarity: 'rare'
  },
  {
    id: 'tykolub',
    name: 'Тыколюб',
    img: 'img/lisa/07_tykolub.webp',
    pack: 'lisa',
    rarity: 'common'
  },
  {
    id: 'sbortsitca-nalivnyh',
    name: 'Сборщица наливных',
    img: 'img/lisa/08_sbortsitca_nalivnyh.webp',
    pack: 'lisa',
    rarity: 'common'
  },
  {
    id: 'hodoka-pod-goroshek',
    name: 'Ходока под горошек',
    img: 'img/lisa/09_hodoka_pod_goroshek.webp',
    pack: 'lisa',
    rarity: 'common'
  },
  {
    id: 'sviter-domik',
    name: 'Свитер-домик',
    img: 'img/lisa/10_sviter_domik.webp',
    pack: 'lisa',
    rarity: 'common'
  },
  {
    id: 'tykvenny-vsadnik',
    name: 'Тыквенный всадник',
    img: 'img/lisa/11_tykvenny_vsadnik.webp',
    pack: 'lisa',
    rarity: 'rare'
  },
  {
    id: 'zont-v-goroshek',
    name: 'Зонт в горошек',
    img: 'img/lisa/12_zont_v_goroshek.webp',
    pack: 'lisa',
    rarity: 'common'
  },
  {
    id: 'buketodarka',
    name: 'Букетодарка',
    img: 'img/lisa/13_buketodarka.webp',
    pack: 'lisa',
    rarity: 'common'
  },
  {
    id: 'chitatel-pod-pledom',
    name: 'Читатель под пледом',
    img: 'img/lisa/14_chitatel_pod_pledom.webp',
    pack: 'lisa',
    rarity: 'rare'
  },
  {
    id: 'fonarshchitsa-s-ryabinoi',
    name: 'Фонарщица с рябиной',
    img: 'img/lisa/15_fonarshchitsa_s_ryabinoi.webp',
    pack: 'lisa',
    rarity: 'common'
  },
  {
    id: 'gerbarii',
    name: 'Осенний гербарий',
    img: 'img/lisa/16_gerbarii.webp',
    pack: 'lisa',
    rarity: 'common'
  },
  {
    id: 'gurman-degustator',
    name: 'Гурман-дегустатор',
    img: 'img/lisa/17_gurman_degustator.webp',
    pack: 'lisa',
    rarity: 'common'
  },
  {
    id: 'sapogi-poprygunyi',
    name: 'Сапоги-попрыгуньи',
    img: 'img/lisa/18_sapogi_poprygunyi.webp',
    pack: 'lisa',
    rarity: 'common'
  },
  {
    id: 'kokon-so-vkusom',
    name: 'Кокон со вкусом',
    img: 'img/lisa/19_kokon_so_vkusom.webp',
    pack: 'lisa',
    rarity: 'common'
  },
  {
    id: 'luzheprohodets',
    name: 'Лужепроходец',
    img: 'img/lisa/20_luzheprohodets.webp',
    pack: 'lisa',
    rarity: 'rare'
  },
  {
    id: 'ryabinovyi-adres',
    name: 'Рябиновый адрес',
    img: 'img/lisa/21_ryabinovyi_adres.webp',
    pack: 'lisa',
    rarity: 'common'
  },
  {
    id: 'kudryavaya-tykva',
    name: 'Кудрявая тыква',
    img: 'img/lisa/22_kudryavaya_tykva.webp',
    pack: 'lisa',
    rarity: 'common'
  },
  {
    id: 'gribnaya-kurerka',
    name: 'Грибная курьерка',
    img: 'img/lisa/23_gribnaya_kurerka.webp',
    pack: 'lisa',
    rarity: 'common'
  },
  {
    id: 'sviter-obnimashka',
    name: 'Свитер-обнимашка',
    img: 'img/lisa/24_sviter_obnimashka.webp',
    pack: 'lisa',
    rarity: 'common'
  },
  {
    id: 'masteritsa',
    name: 'Мастерица-лисичка',
    img: 'img/lisa/25_masteritsa.webp',
    pack: 'lisa',
    rarity: 'rare'
  },

  /* --- ПАК 3 «Лис.Зима»: тот же герой-лис, мужские имена,
         без описаний — только названия --- */
  {
    id: 'elochny-naryadchik',
    name: 'Ёлочный нарядчик',
    img: 'img/zima/01_elochny_naryadchik.webp',
    pack: 'zima',
    rarity: 'common'
  },
  {
    id: 'termos-sogrevatel',
    name: 'Термос-согреватель',
    img: 'img/zima/02_termos_sogrevatel.webp',
    pack: 'zima',
    rarity: 'common'
  },
  {
    id: 'elochny-verholaz',
    name: 'Ёлочный верхолаз',
    img: 'img/zima/03_elochny_verholaz.webp',
    pack: 'zima',
    rarity: 'rare'
  },
  {
    id: 'pled-kokon',
    name: 'Плед-кокон',
    img: 'img/zima/04_pled_kokon.webp',
    pack: 'zima',
    rarity: 'common'
  },
  {
    id: 'pervy-led',
    name: 'Первый лёд',
    img: 'img/zima/05_pervy_led.webp',
    pack: 'zima',
    rarity: 'common'
  },
  {
    id: 'podarkonosets',
    name: 'Подарконосец',
    img: 'img/zima/06_podarkonosets.webp',
    pack: 'zima',
    rarity: 'common'
  },
  {
    id: 'sharik-zateynik',
    name: 'Шарик-затейник',
    img: 'img/zima/07_sharik_zateynik.webp',
    pack: 'zima',
    rarity: 'common'
  },
  {
    id: 'podarok-fonarik',
    name: 'Подарок-фонарик',
    img: 'img/zima/08_podarok_fonarik.webp',
    pack: 'zima',
    rarity: 'common'
  },
  {
    id: 'elkonosets',
    name: 'Ёлконосец',
    img: 'img/zima/09_elkonosets.webp',
    pack: 'zima',
    rarity: 'common'
  },
  {
    id: 'snegovikov-drug',
    name: 'Снеговиков друг',
    img: 'img/zima/10_snegovikov_drug.webp',
    pack: 'zima',
    rarity: 'common'
  },
  {
    id: 'figurist-lis',
    name: 'Фигурист-лис',
    img: 'img/zima/11_figurist_lis.webp',
    pack: 'zima',
    rarity: 'rare'
  },
  {
    id: 'snegouborshchik',
    name: 'Снегоуборщик',
    img: 'img/zima/12_snegouborshchik.webp',
    pack: 'zima',
    rarity: 'common'
  },
  {
    id: 'snezhny-kurier',
    name: 'Снежный курьер',
    img: 'img/zima/13_snezhny_kurier.webp',
    pack: 'zima',
    rarity: 'common'
  },
  {
    id: 'chitatel-u-fonarya',
    name: 'Читатель у фонаря',
    img: 'img/zima/14_chitatel_u_fonarya.webp',
    pack: 'zima',
    rarity: 'rare'
  },
  {
    id: 'snezhny-plyasun',
    name: 'Снежный плясун',
    img: 'img/zima/15_snezhny_plyasun.webp',
    pack: 'zima',
    rarity: 'common'
  },
  {
    id: 'pryanichny-stol',
    name: 'Пряничный стол',
    img: 'img/zima/16_pryanichny_stol.webp',
    pack: 'zima',
    rarity: 'common'
  },
  {
    id: 'drovonos',
    name: 'Дровонос',
    img: 'img/zima/17_drovonos.webp',
    pack: 'zima',
    rarity: 'common'
  },
  {
    id: 'hozyain-kresla',
    name: 'Хозяин кресла',
    img: 'img/zima/18_hozyain_kresla.webp',
    pack: 'zima',
    rarity: 'common'
  },
  {
    id: 'drug-batarei',
    name: 'Друг батареи',
    img: 'img/zima/19_drug_batarei.webp',
    pack: 'zima',
    rarity: 'common'
  },
  {
    id: 'lyzhnik-lis',
    name: 'Лыжник-лис',
    img: 'img/zima/20_lyzhnik_lis.webp',
    pack: 'zima',
    rarity: 'common'
  },
  {
    id: 'lovets-snezhinok',
    name: 'Ловец снежинок',
    img: 'img/zima/21_lovets_snezhinok.webp',
    pack: 'zima',
    rarity: 'common'
  },
  {
    id: 'snezhny-angel',
    name: 'Снежный ангел',
    img: 'img/zima/22_snezhny_angel.webp',
    pack: 'zima',
    rarity: 'rare'
  },
  {
    id: 'nablyudatel-u-okna',
    name: 'Наблюдатель у окна',
    img: 'img/zima/23_nablyudatel_u_okna.webp',
    pack: 'zima',
    rarity: 'rare'
  },
  {
    id: 'passazhir-s-kakao',
    name: 'Пассажир с какао',
    img: 'img/zima/24_passazhir_s_kakao.webp',
    pack: 'zima',
    rarity: 'common'
  }
];

/* Коллекции (паки) в порядке показа в галерее. */
const PACKS = [
  { key: 'gorod', title: 'Чудики' },
  { key: 'lisa',  title: 'Лисичка.Осень' },
  { key: 'zima',  title: 'Лис.Зима' }
];
const PACK_BY_KEY = Object.fromEntries(PACKS.map(p => [p.key, p]));

const CARD_BY_ID = Object.fromEntries(CARDS.map(c => [c.id, c]));

/**
 * Выбрать карточку-награду.
 * mode: 'circle' | 'point' | 'route'
 * frac: насколько далеко ушёл от минимума (0..1) — чем дальше, тем выше шанс редкой
 *
 * Правило: пока в паке есть несобранные карточки, дубли из него не падают.
 * Пак выбирается случайно среди недособранных, внутри пака — случайная карточка.
 * Когда все паки собраны — снова падают любые.
 */
function pickReward(mode, frac = 0) {
  const owns = (typeof state !== 'undefined' && state.collection) || {};
  const notOwned = c => !(owns[c.id] > 0);

  const packs = [...new Set(CARDS.map(c => c.pack || 'gorod'))]
    .filter(p => CARDS.some(c => (c.pack || 'gorod') === p && notOwned(c)));

  let pool = [];
  if (packs.length) {
    // карточки падают из каждого пака, пока его коллекция не собрана:
    // пак — случайный среди недособранных, порядок внутри — случайный
    const pack = packs[Math.floor(Math.random() * packs.length)];
    const inPack = CARDS.filter(c => (c.pack || 'gorod') === pack && notOwned(c));
    const commons = inPack.filter(c => c.rarity === 'common');
    const rares   = inPack.filter(c => c.rarity === 'rare');

    let rareChance = 0;
    if (mode === 'point') rareChance = 0.15 + 0.35 * frac;   // 15–50 %
    if (mode === 'route') rareChance = 1;                     // маршрут — всегда редкая

    pool = (Math.random() < rareChance) ? rares : commons;
    if (!pool.length) pool = rares.length ? rares : commons;
  }

  // совсем всё собрано — падают любые (дубли)
  if (!pool.length) pool = CARDS;
  return pool[Math.floor(Math.random() * pool.length)];
}
