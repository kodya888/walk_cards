/* =========================================================
   Карточки «Гуляю-собираю»
   ---------------------------------------------------------
   Чтобы добавить нового чудика:
   1) положи его картинку в img/ (лучше SVG — лёгкий)
   2) добавь две записи ниже: обычную и редкую (rarity: 'rare')
   Идентификатор (id) должен быть уникальным.
   ========================================================= */

const CARDS = [
  {
    id: 'letopisets',
    name: 'Летописец двора',
    img: 'img/1_letopisets_dvora.svg',
    rarity: 'common',
    desc: 'Записывает всё, что происходит во дворе с 1987 года.'
  },
  {
    id: 'smotritel',
    name: 'Ночной смотритель фонарей',
    img: 'img/2-nochnoy_smotritel_fonarey.svg',
    rarity: 'common',
    desc: 'Знает, какой фонарь погаснет первым.'
  },
  {
    id: 'pirozhkov',
    name: 'Инспектор пирожков',
    img: 'img/3_inspektor_pirozhkov.svg',
    rarity: 'common',
    desc: 'Проверяет начинку и следит за хрустом.'
  },

  /* --- редкие версии тех же персонажей (золотая рамка) --- */
  {
    id: 'letopisets-rare',
    name: 'Летописец двора',
    img: 'img/1_letopisets_dvora.svg',
    rarity: 'rare',
    desc: 'Первый лист его летописи. Говорят, приносит удачу в поисках.'
  },
  {
    id: 'smotritel-rare',
    name: 'Ночной смотритель фонарей',
    img: 'img/2-nochnoy_smotritel_fonarey.svg',
    rarity: 'rare',
    desc: 'Единственный, кто видел, как зажигается самый первый фонарь.'
  },
  {
    id: 'pirozhkov-rare',
    name: 'Инспектор пирожков',
    img: 'img/3_inspektor_pirozhkov.svg',
    rarity: 'rare',
    desc: 'Золотой значок за безупречную проверку 10 000 пирожков.'
  }
];

const CARD_BY_ID = Object.fromEntries(CARDS.map(c => [c.id, c]));

/**
 * Выбрать карточку-награду.
 * mode: 'circle' | 'point' | 'route'
 * frac: насколько далеко ушёл от минимума (0..1) — чем дальше, тем выше шанс редкой
 */
function pickReward(mode, frac = 0) {
  const commons = CARDS.filter(c => c.rarity === 'common');
  const rares = CARDS.filter(c => c.rarity === 'rare');

  let rareChance = 0;
  if (mode === 'point') rareChance = 0.15 + 0.35 * frac;   // 15–50 %
  if (mode === 'route') rareChance = 1;                     // маршрут — всегда редкая

  const pool = (Math.random() < rareChance) ? rares : commons;
  return pool[Math.floor(Math.random() * pool.length)];
}
