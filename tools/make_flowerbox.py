# -*- coding: utf-8 -*-
"""Генератор карточек «Коробка цветов» (Lattice-JSON Lottie, написан кодом).

Идея (наша, не копия чужой анимации): в кадре стоит открытая коробка,
первые полсекунды она пустая, затем цветы по одному «выпрыгивают» из неё
снизу вверх (с лёгким перелётом и покачиванием), покачиваются, а в конце
цикла все обратно прячутся — и кадр зацикливается.

Всё настраивается в конфигах ниже (BOX_STYLES, BOX_SHOTS):
  - цвета коробки (корпус, кромка, внутренности, рисунок);
  - список цветов-цветов: вид, позиция по X, высота, наклон, задержка старта,
    своя палитра;
  - блёстки вкл/выкл.

Чтобы сделать новую коробку — скопируй блок в BOX_SHOTS, поменяй параметры,
запусти:  C:/Users/ADMIN/AppData/Local/Programs/Python/Python313/python.exe
          tools/make_flowerbox.py [имя_конфига|all]

Выход: img/flowers/<имя>.json (+ печать пути).
"""
import json
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FR = 30            # кадров в секунду
OP = 120           # длина цикла, кадров (4 с)
W, H = 500, 700

# ---------- геометрия коробки (в координатах кадра 500x700) ----------
BOX_X0, BOX_X1 = 118, 382      # ширина передней стенки
RIM = 460                      # верхний край передней стенки
WALL_BOT = 612                 # низ коробки


# ---------- easing (взят из работавшего make_tulip_lottie.py) ----------
EASE = {"i": {"x": [0.5], "y": [1]}, "o": {"x": [0.5], "y": [0]}}        # мягкий
IN_H = {"i": {"x": [0.7], "y": [1]}, "o": {"x": [0.3], "y": [0]}}        # с разгоном
LIN = {"i": {"x": [0.833], "y": [0.833]}, "o": {"x": [0.167], "y": [0.167]}}


# ---------- цвета ----------
def hx(s):
    """'#rrggbb' -> [r,g,b] в 0..1 (для Lottie)."""
    s = s.lstrip('#')
    return [int(s[i:i + 2], 16) / 255 for i in (0, 2, 4)]


def mix(c1, c2, f):
    return [a + (b - a) * f for a, b in zip(c1, c2)]


# ---------- ключи анимации ----------
def kf(t, s, ease=EASE):
    return dict(ease, t=t, s=s)


def kf3(t, x, y, ease=EASE):
    return dict(ease, t=t, s=[x, y, 0])


# ---------- примитивы Lottie ----------
def fill(c, o=100):
    return {"ty": "fl", "c": {"a": 0, "k": list(c) + [1]},
            "o": {"a": 0, "k": o}, "r": 1, "nm": "fill"}


def stroke(c, w, o=100):
    return {"ty": "st", "c": {"a": 0, "k": list(c) + [1]},
            "o": {"a": 0, "k": o}, "w": {"a": 0, "k": w},
            "lc": 2, "lj": 2, "nm": "line"}


def gfill(c1, c2, s, e, o=100):
    """Линейный градиент (плавный переход цвета) от точки s к точке e.
    c1 — цвет у начала (s), c2 — у конца (e). Даёт «объём» без теней."""
    return {"ty": "gf", "o": {"a": 0, "k": o}, "r": 1, "bm": 0, "t": 1,
            "g": {"p": 2, "k": {"a": 0, "k": [0] + list(c1) + [1] + list(c2)}},
            "s": {"a": 0, "k": list(s)}, "e": {"a": 0, "k": list(e)}, "nm": "gf"}


def quad(p1, p2, p3, p4, nm="shp"):
    """Замкнутый четырёхугольник (прямые стороны)."""
    return {"ty": "sh", "ks": {"a": 0, "k": {
        "c": True, "v": [p1, p2, p3, p4],
        "i": [[0, 0]] * 4, "o": [[0, 0]] * 4}}, "nm": nm}


def pth(v, i, o, c=False, nm="shp"):
    return {"ty": "sh", "ks": {"a": 0, "k": {"c": c, "v": v, "i": i, "o": o}}, "nm": nm}


def ell(cx, cy, rx, ry, nm="el"):
    return {"ty": "el", "p": {"a": 0, "k": [cx, cy]},
            "s": {"a": 0, "k": [rx * 2, ry * 2]}, "nm": nm}


def st_tr(p=(0, 0), a=(0, 0), r=0, o=100):
    """Статичный transform для группы."""
    return {"ty": "tr", "p": {"a": 0, "k": list(p)}, "a": {"a": 0, "k": list(a)},
            "s": {"a": 0, "k": [100, 100]}, "r": {"a": 0, "k": r},
            "o": {"a": 0, "k": o}}


def grp(*items):
    """Группа фигур. В Lottie последним элементом ОБЯЗАН идти transform (tr) —
    если его забыли, добавляем нейтральный, иначе слой не рисуется вообще.
    Списки внутри аргументов разворачиваем (голый список внутри `it` Lottie
    молча выбрасывает вместе со всем содержимым)."""
    flat = []
    for it in items:
        if isinstance(it, list):
            flat.extend(it)
        else:
            flat.append(it)
    items = flat
    if not (items and items[-1].get("ty") == "tr"):
        items.append(st_tr())
    return {"ty": "gr", "nm": "g", "it": items}


def g_rot(items, pivot, deg, nm="g"):
    """Группа с поворотом вокруг точки pivot на месте.
    В Lottie формула трансформации: x' = R·(x − a) + p, поэтому чтобы
    центр поворота не сместился, a и p должны обе равняться pivot."""
    return grp(*(items + [{"ty": "tr", "p": {"a": 0, "k": list(pivot)},
                           "a": {"a": 0, "k": list(pivot)},
                           "s": {"a": 0, "k": [100, 100]},
                           "r": {"a": 0, "k": deg}, "o": {"a": 0, "k": 100}}]))


def layer(ind, shapes, p_k, s_k=None, r_k=None, o_k=None, nm="l"):
    """ty=4 слой. p_k/k s_k/r_k — словари {a,k} или статические значения."""
    ks = {
        "o": o_k if o_k else {"a": 0, "k": 100},
        "r": r_k if r_k else {"a": 0, "k": 0},
        "p": p_k,
        "a": {"a": 0, "k": [0, 0, 0]},
        "s": s_k if s_k else {"a": 0, "k": [100, 100, 100]}
    }
    return {"ddd": 0, "ind": ind, "ty": 4, "nm": nm, "sr": 1,
            "ks": ks, "ao": 0, "shapes": shapes, "ip": 0, "op": OP, "st": 0, "bm": 0}


def anim(keys):
    return {"a": 1, "k": keys}


# ======================================================================
#  Цветы
# ======================================================================
STEM_C = hx('3d8828')      # яркий стеблевой зелёный (как в примере)
LEAF_C = hx('57a83a')      # чуть светлее — листья


def stem_group(top_y, stem_c, leaf_c=None, w=9, curl=12, leaves=2, head_leaves=False):
    """Стебель от (0,0) до (0, top_y): толстый, с изгибом, листьями на середине
    и — по желанию — парой больших листьев прямо под головкой (как в примере)."""
    sh = pth([(0, 0), (0, top_y)],
             [[0, 0], [-curl, 0]], [[curl, 0], [0, 0]], nm="stem")
    shapes = [grp(sh, stroke(stem_c, w))]
    if leaf_c and leaves >= 1:
        # листья — у НИЗА стебля, у кромки коробки: выше стебли остаются
        # открытыми, видны вертикальные «прутики» до головок
        shapes.append(leaf(-14, top_y * 0.2, 10, 24, -36, leaf_c, (0, top_y * 0.26)))
    if leaf_c and leaves >= 2:
        shapes.append(leaf(14, top_y * 0.38, 9, 22, 32, leaf_c, (0, top_y * 0.44)))
    if leaf_c and head_leaves:
        shapes.append(leaf(-17, top_y + 16, 10, 26, -52, leaf_c, (0, top_y + 22)))
        shapes.append(leaf(17, top_y + 24, 9, 24, 48, leaf_c, (0, top_y + 30)))
    return shapes


def daisy_shapes(h, petals, pr, pw, rc, pet_c, cen_c, dot_c=None,
                 stem_c=STEM_C, leaf_c=LEAF_C, curl=12):
    """Ромашка (как в примере): крупные лепестки с тёмным контуром, два ряда."""
    hc = (0, -h)
    line_c = mix(pet_c, [0, 0, 0], 0.45)
    shapes = stem_group(-h + rc * 0.8, stem_c, leaf_c, w=9, curl=curl,
                        head_leaves=True)
    for i in range(petals):                                   # внешний (основной)
        shapes.append(g_rot(
            [ell(0, -h - pr + 2, pw, pr, "petal"),
             fill(mix(pet_c, [0, 0, 0], 0.08)), stroke(line_c, 3)],
            hc, i * 360.0 / petals, "pet%d" % i))
    for i in range(petals):                                   # внутренний (светлый)
        shapes.append(g_rot(
            [ell(0, -h - pr + 11, pw * 0.7, pr * 0.62, "petal"),
             fill(mix(pet_c, [1, 1, 1], 0.4))],
            hc, i * 360.0 / petals + 360.0 / (petals * 2), "pi%d" % i))
    core = [ell(0, -h, rc, rc, "core"), fill(cen_c),
            stroke(mix(cen_c, [0, 0, 0], 0.4), 3),
            ell(0, -h - rc * 0.13, rc * 0.5, rc * 0.48, "core2"),
            fill(mix(cen_c, [1, 1, 1], 0.32))]
    if dot_c:
        core += [ell(0, -h, rc * 0.28, rc * 0.28, "dot"), fill(dot_c)]
    shapes.append(grp(*core))
    return shapes


def pop_shapes(h, r, outer_c, ring_c, inner_c, stem_c=STEM_C, leaf_c=LEAF_C, curl=10):
    """Крупный цветок: 6 лепестков-яичек с тёмным контуром + жирная серединка."""
    hc = (0, -h)
    pr = r * 1.15
    pw = r * 0.52
    line_c = mix(outer_c, [0, 0, 0], 0.42)
    shapes = stem_group(-h + r * 0.3, stem_c, leaf_c, w=9, curl=curl,
                        head_leaves=True)
    for i in range(6):
        shapes.append(g_rot(
            [ell(0, -h - pr + 2, pw, pr, "petal"),
             fill(mix(outer_c, [0, 0, 0], 0.06)), stroke(line_c, 3)],
            hc, i * 60.0 + 22, "pet%d" % i))
    shapes.append(grp(ell(0, -h, r, r, "mid"), fill(ring_c),
                      stroke(mix(ring_c, [0, 0, 0], 0.35), 3),
                      ell(0, -h - r * 0.12, r * 0.45, r * 0.42, "mid2"),
                      fill(inner_c)))
    return shapes


def tulip_shapes(h, head_c, stem_c=STEM_C, leaf_c=LEAF_C, curl=11):
    """Тюльпан как в примере: три лепестка-лопасти с тёмным контуром
    (центральный выше и светлее)."""
    top = -h
    line_c = mix(head_c, [0, 0, 0], 0.42)
    return stem_group(top + 40, stem_c, leaf_c, w=9, curl=curl, head_leaves=True) + [
        # нижняя «чаша», объединяющая лепестки
        grp(quad((-34, top + 42), (34, top + 42), (26, top - 2), (-26, top - 2),
                 "cup"), fill(head_c)),
        # боковые лепестки
        grp(ell(-21, top + 4, 19, 31, "pl"), fill(head_c),
            stroke(line_c, 3)),
        grp(ell(21, top + 4, 19, 31, "pr"), fill(head_c),
            stroke(line_c, 3)),
        # центральный лепесток — светлее и выше
        grp(ell(0, top - 12, 21, 32, "pc"),
            fill(mix(head_c, [1, 1, 1], 0.14)), stroke(line_c, 3)),
        # белые блики-овалы (как в примере)
        grp(ell(-13, top + 18, 6, 11, "hl1"), fill([1, 1, 1], 85)),
        grp(ell(-6, top + 34, 3.5, 6, "hl2"), fill([1, 1, 1], 85)),
    ]


def bud_shapes(h, head_c, stem_c=STEM_C, leaf_c=LEAF_C, curl=10):
    """Бутончик: крупная слезинка на стебле, с контуром и бликом."""
    top = -h
    drop = pth(
        [(0, top), (21, top + 26), (0, top + 52), (-21, top + 26)],
        [[-11, 0], [0, -12], [11, 0], [0, -12]],
        [[11, 0], [0, 12], [-11, 0], [0, 12]], c=True)
    return stem_group(top + 24, stem_c, leaf_c, w=9, curl=curl, leaves=1) + [
        grp(drop, fill(head_c), stroke(mix(head_c, [0, 0, 0], 0.35), 3)),
        grp(ell(-7, top + 14, 7, 10, "hl"), fill(mix(head_c, [1, 1, 1], 0.5))),
        grp(ell(4, top + 30, 3.5, 6, "hl2"), fill([1, 1, 1], 80)),
        leaf(-15, top + 16, 9, 18, -40, leaf_c, (0, top + 22)),
        leaf(14, top + 18, 8, 16, 34, leaf_c, (0, top + 24)),
    ]


def leaf(x, y, rx, ry, deg, c, pivot):
    """Лист со светлой жилкой по центру."""
    vein = grp(pth([(x, y - ry * 0.72), (x, y + ry * 0.72)],
                   [[0, 0], [0, 0]], [[0, 0], [0, 0]], nm="vein"),
               stroke(mix(c, [1, 1, 1], 0.45), 2))
    return g_rot([ell(x, y, rx, ry, "leaf"), fill(c), vein], pivot, deg, "leaf")


def sprig_shapes(h, leaf_c, stem_c):
    """Зелёная веточка-заполнитель с крупными листьями."""
    top = -h
    stem = pth([(0, 2), (0, top)], [[0, 0], [0, 0]], [[0, 0], [0, 0]], nm="stem")
    shapes = [grp(stem, stroke(stem_c, 8))]
    shapes.append(leaf(-16, top + 32, 12, 30, -36, leaf_c, (0, top + 38)))
    shapes.append(leaf(16, top + 62, 11, 27, 31, leaf_c, (0, top + 68)))
    shapes.append(leaf(0, top - 14, 12, 30, 0, leaf_c, (0, top - 8)))
    return shapes


KINDS = {
    'daisy': daisy_shapes,
    'pop': pop_shapes,
    'tulip': tulip_shapes,
    'sprig': sprig_shapes,
    'bud': bud_shapes,
}

GREEN = STEM_C


def flower_shapes(f):
    k = f['kind']
    c = f.get('colors', {})
    stem_c = c.get('stem', STEM_C)
    leaf_c = c.get('leaf', LEAF_C)
    if k == 'daisy':
        return daisy_shapes(
            f['h'], f.get('petals', 7), f.get('pr', 16), f.get('pw', 12),
            f.get('rc', 15),
            c.get('petal', hx('f4699e')), c.get('center', hx('ffd166')),
            c.get('dot'), stem_c, leaf_c, f.get('curl', 12))
    if k == 'pop':
        return pop_shapes(
            f['h'], f.get('r', 26),
            c.get('outer', hx('4d8fe8')), c.get('ring', hx('ffd166')),
            c.get('inner', hx('2b5fc9')), stem_c, leaf_c, f.get('curl', 10))
    if k == 'tulip':
        return tulip_shapes(f['h'], c.get('head', hx('e94f5f')),
                            stem_c, leaf_c, f.get('curl', 9))
    if k == 'bud':
        return bud_shapes(f['h'], c.get('head', hx('f28fb2')),
                          stem_c, leaf_c, f.get('curl', 8))
    if k == 'sprig':
        return sprig_shapes(f['h'], leaf_c, stem_c)
    raise KeyError(k)


# ======================================================================
#  Анимация одного цветка
# ======================================================================
T_SINK = 104             # с этого кадра все цветы прячутся в коробку
T_HIDDEN = 116           # к этому кадру скрылись (до конца цикла пусто)


def flower_layer(ind, f, nm):
    """Слой цветка. Спрятанный цветок — крошечный (2 %) и глубоко в стенке
    (y0 = RIM+140, там его закрывает передняя стенка). Дальше он ОДНОВРЕМЕННО
    растёт (2 -> 112 -> 100 %) и поднимается (y0 -> чуть выше -> y_end):
    головка пересекает кромку коробки первой, стебель выезжает следом —
    как в примере. Основание стебля всё время не ниже y0, поэтому снизу
    коробки ничего торчать не может.
    Наклон (lean): у каждого цветка свой, по умолчанию наружу от центра
    коробки; поверх наклона — лёгкое покачивание."""
    x = f['x']
    t0 = f.get('t0', 26)
    y0 = RIM + 140                                   # спрятан глубоко в стенке
    y_end = RIM + 30                                 # основание стебля спрятано
    y_over = y_end - 16                              # лёгкий перелёт вверх

    pos = anim([
        kf3(t0, x, y0, LIN),
        kf3(t0 + 9, x, y_over, EASE),
        kf3(t0 + 15, x, y_end, EASE),
        kf3(T_SINK, x, y_end, LIN),
        kf3(T_SINK + 8, x, y0, IN_H),
        kf3(OP - 1, x, y0, LIN),
    ])
    sc = anim([
        kf(t0, [2, 2], LIN),
        kf(t0 + 9, [112, 112], EASE),
        kf(t0 + 15, [100, 100], EASE),
        kf(T_SINK, [100, 100], LIN),
        kf(T_SINK + 8, [2, 2], IN_H),
        kf(OP - 1, [2, 2], LIN),
    ])
    # ВАЖНО: у вращения значения ключей ОБЯЗАНЫ быть массивами [deg] —
    # lottie-web 5.13 на скалярах s:0 ломается и рисует слой под ~78°.
    lean = f.get('lean', round((x - 250) / 6.0, 1))     # левые — влево, правые — вправо
    tilt = f.get('tilt', 2.5)
    rt_keys = [kf(t0, [lean], LIN)]
    t, amp, sign = t0 + 30, abs(tilt), 1
    while t < T_SINK - 2:
        rt_keys.append(kf(t, [lean + sign * amp], EASE))
        t += 18
        sign = -sign
        amp = max(1.3, amp * 0.85)      # затухает медленнее — качается до конца
    rt_keys += [kf(T_SINK, [lean], LIN), kf(T_SINK + 8, [lean], LIN),
                kf(OP - 1, [lean], LIN)]
    rt = anim(rt_keys)
    if t0 >= T_SINK - 16:                       # защита: старт слишком поздно
        raise ValueError('t0 слишком большой: %s' % t0)
    return layer(ind, flower_shapes(f), pos, sc, rt, nm=nm)


# ======================================================================
#  Коробка
# ======================================================================
def box_front_shapes(b):
    """Передняя стенка (градиент + тёмная обводка + складки + лента с бант)
    + кромка с белыми бликами. Рисуется ПОВЕРХ цветов."""
    body = hx(b['body'])
    edge = hx(b['edge'])
    deco = hx(b['deco'])
    line_c = mix(body, [0, 0, 0], 0.66)          # тёмная обводка, как в примере
    cx = (BOX_X0 + BOX_X1) / 2.0
    # складки «рифлёной» бумаги: вертикальные чуть темнее полосы
    ribs = []
    for x in range(int(BOX_X0) + 56, int(BOX_X1) - 40, 50):
        ribs.append(grp(
            pth([(x, RIM + 36), (x - 3, WALL_BOT - 14)],
                [[0, 0], [-2, 0]], [[2, 0], [0, 0]], nm="rib"),
            stroke(mix(body, [0, 0, 0], 0.12), 3)))
    shapes = [
        grp(quad((BOX_X0 - 6, RIM + 1), (BOX_X1 + 6, RIM + 1),
                 (BOX_X1 + 2, RIM + 22), (BOX_X0 + 2, RIM + 22), "rim"),
            gfill(mix(edge, [1, 1, 1], 0.18), edge,
                  (cx, RIM + 1), (cx, RIM + 22)),
            stroke(line_c, 5))]
    shapes += ribs
    shapes += [
        grp(quad((BOX_X0 + 4, RIM + 20), (BOX_X1 - 4, RIM + 20),
                 (BOX_X1 - 18, WALL_BOT), (BOX_X0 + 18, WALL_BOT), "wall"),
            gfill(mix(body, [1, 1, 1], 0.2), mix(body, [0, 0, 0], 0.13),
                  (cx, RIM + 20), (cx, WALL_BOT)),
            stroke(line_c, 5))]
    # лента поперёк нижней части стенки + бант по центру
    ribbon = mix(deco, body, 0.12)
    shapes += [
        grp(quad((BOX_X0 + 15, RIM + 92), (BOX_X1 - 15, RIM + 92),
                 (BOX_X1 - 12, RIM + 124), (BOX_X0 + 12, RIM + 124), "ribbon"),
            fill(deco)),
        grp(quad((BOX_X0 + 15, RIM + 108), (BOX_X1 - 15, RIM + 108),
                 (BOX_X1 - 12, RIM + 114), (BOX_X0 + 12, RIM + 114), "ribline"),
            fill(mix(deco, [0, 0, 0], 0.14))),
        grp(ell(cx - 22, RIM + 116, 17, 10, "bowL"), fill(ribbon)),
        grp(ell(cx + 22, RIM + 116, 17, 10, "bowR"), fill(ribbon)),
        grp(ell(cx, RIM + 120, 9, 9, "knot"), fill(mix(deco, [0, 0, 0], 0.16))),
        # белые блики-«росчерки», как на картонной коробке в примере
        grp(pth([(BOX_X0 + 30, RIM + 46), (BOX_X0 + 62, RIM + 40)],
                [[0, 0], [-10, -4]], [[10, 4], [0, 0]], nm="gloss1"),
            stroke(mix(body, [1, 1, 1], 0.85), 8)),
        grp(ell(BOX_X0 + 44, RIM + 66, 7, 12, "gloss2"), fill(mix(body, [1, 1, 1], 0.8))),
    ]
    return shapes


def box_back_shapes(b):
    """Внутренность, задние и боковые створки (рисуется ЗА цветами)."""
    inner = hx(b['inner'])
    body = hx(b['body'])
    back = mix(body, [0, 0, 0], 0.22)
    line_c = mix(body, [0, 0, 0], 0.66)
    return [
        grp(quad((BOX_X0 + 14, RIM + 12), (BOX_X1 - 14, RIM + 12),   # щель внутри
                 (BOX_X1 - 22, RIM - 16), (BOX_X0 + 22, RIM - 16), "slot"),
            fill(inner)),
        grp(quad((BOX_X0 + 24, RIM - 14), (BOX_X0 + 106, RIM - 18),  # задняя лев. створка
                 (BOX_X0 + 84, RIM - 78), (BOX_X0 - 6, RIM - 54), "bflapL"),
            fill(back), stroke(line_c, 5)),
        grp(quad((BOX_X1 - 24, RIM - 14), (BOX_X1 - 106, RIM - 18),  # задняя прав. створка
                 (BOX_X1 - 84, RIM - 78), (BOX_X1 + 6, RIM - 54), "bflapR"),
            fill(mix(back, [0, 0, 0], 0.06)), stroke(line_c, 5)),
        grp(quad((BOX_X0 - 2, RIM + 12), (BOX_X0 + 58, RIM + 18),    # боковая лев. створка
                 (BOX_X0 + 38, RIM + 62), (BOX_X0 - 26, RIM + 40), "sflapL"),
            fill(back), stroke(line_c, 5)),
        grp(quad((BOX_X1 + 2, RIM + 12), (BOX_X1 - 58, RIM + 18),    # боковая прав. створка
                 (BOX_X1 - 38, RIM + 62), (BOX_X1 + 26, RIM + 40), "sflapR"),
            fill(mix(back, [0, 0, 0], 0.06)), stroke(line_c, 5)),
    ]


def sparkle_layer(ind, x, y, r, t, nm):
    """Мелькающая блёстка-звёздочка (как в примере), вспыхивает по фазе."""
    c = hx('ffffff')
    op = anim([
        kf(t % OP, 0, LIN), kf((t + 8) % OP, 90, EASE),
        kf((t + 18) % OP, 0, EASE), kf(OP - 1, 0, LIN)])
    sc = anim([
        kf(t % OP, [60, 60], LIN), kf((t + 8) % OP, [110, 110], EASE),
        kf((t + 18) % OP, [60, 60], EASE), kf(OP - 1, [60, 60], LIN)])
    star = pth([(0, -r), (r * 0.3, -r * 0.3), (r, 0), (r * 0.3, r * 0.3),
                (0, r), (-r * 0.3, r * 0.3), (-r, 0), (-r * 0.3, -r * 0.3)],
               [[0, 0]] * 8, [[0, 0]] * 8, c=True, nm="star")
    shapes = [grp(star, fill(c))]
    return layer(ind, shapes,
                 {"a": 0, "k": [x, y, 0]}, sc, o_k=op, nm=nm)


def petal_layer(ind, x0, y0, t0, c, nm):
    """Отдельный лепесток, парящий по воздуху после того, как букет собрался."""
    pos = anim([kf3(t0, x0, y0, EASE),
                kf3(t0 + 50, x0 + 46, 468, EASE),
                kf3(OP - 1, x0 + 46, 468, LIN)])
    op = anim([kf(t0, 0, LIN), kf(t0 + 6, 90, LIN),
               kf(t0 + 50, 0, EASE), kf(OP - 1, 0, LIN)])
    rt = anim([kf(t0, [20], LIN), kf(t0 + 50, [150], LIN), kf(OP - 1, [150], LIN)])
    shapes = [grp(ell(0, 0, 8, 13, "petal"), fill(c),
                  stroke(mix(c, [0, 0, 0], 0.15), 2))]
    return layer(ind, shapes, pos, None, rt, o_k=op, nm=nm)


# ======================================================================
#  Сборка кадра
# ======================================================================
def doc(shots, nm):
    layers = []
    ind = 1
    # поверх всего — блёстки
    if shots.get('sparkles', True):
        for i, (x, y, r, t) in enumerate(shots.get('sparkle_pos', [
                (150, 250, 13, 20), (352, 300, 15, 55), (250, 200, 11, 85)])):
            layers.append(sparkle_layer(ind, x, y, r, t, "spark%d" % i))
            ind += 1
    # падающие лепестки (тоже поверх, но под блёстками уже не видно — ладно)
    if shots.get('petals', True):
        for i, (x0, t0, c) in enumerate(shots.get('petal_drop', [
                (150, 56, hx('f9b7cd')), (330, 62, hx('ffe1a0')),
                (215, 68, hx('c9dcff'))])):
            layers.append(petal_layer(ind, x0, 140, t0, c, "dr%d" % i))
            ind += 1
    # передняя стенка (на цветами)
    layers.append(layer(ind, box_front_shapes(shots['box']), {"a": 0, "k": [0, 0, 0]},
                        nm="box_front"))
    ind += 1
    # цветы: кто первый в списке — тот ближе к зрителю
    for i, f in enumerate(shots['flowers']):
        layers.append(flower_layer(ind, f, "fl%d" % i))
        ind += 1
    # задняя часть коробки (внутренность + створки)
    layers.append(layer(ind, box_back_shapes(shots['box']), {"a": 0, "k": [0, 0, 0]},
                        nm="box_back"))
    ind += 1
    # мягкая тень под коробкой (рисуется позади всего)
    layers.append(layer(ind, [grp(ell(250, 636, 168, 15, "shadow"),
                                  fill(hx('8a6a4a'), o=30))],
                        {"a": 0, "k": [0, 0, 0]}, nm="shadow"))
    return {"v": "5.7.4", "fr": FR, "ip": 0, "op": OP, "w": W, "h": H,
            "nm": nm, "ddd": 0, "assets": [], "layers": layers}


# ======================================================================
#  НАСТРОЙКИ: цвета коробок + состав букетов
# ======================================================================
# Палитра цветов-цветков
P_PINK = {'petal': hx('f4699e'), 'center': hx('ffd166')}
P_BLUE = {'outer': hx('4d8fe8'), 'ring': hx('ffd166'), 'inner': hx('2b5fc9')}
P_RED = {'head': hx('e04550')}
P_ORANGE = {'outer': hx('ff8a3d'), 'ring': hx('ffd166'), 'inner': hx('d9542f')}

# Стили коробки: body — корпус, edge — кромка, inner — тёмная щель,
# line/deco не используются напрямую в плоском стиле (deco — блики)
BOX_STYLES = {
    'orange': {'body': 'e8804f', 'edge': 'c65a2e', 'inner': '5a2c17', 'deco': 'ffd9b3'},
    'blue':   {'body': '5f8fd6', 'edge': '3d6bb0', 'inner': '1e3557', 'deco': 'cfe0ff'},
    'pink':   {'body': 'e97fa6', 'edge': 'c05a83', 'inner': '5c2337', 'deco': 'ffd4e5'},
    'green':  {'body': '6faf6c', 'edge': '4d8a4e', 'inner': '26402a', 'deco': 'd7f2d7'},
    'purple': {'body': '9b7fd6', 'edge': '7560ad', 'inner': '332a4f', 'deco': 'e6dcff'},
}

# Состав букета в «настоящий» вид: сзади высокая зелень, в середине крупные
# цветы на стеблях, впереди низкий ряд; порядок в flowers — первый ближе
# к зрителю (перекрывает остальных).
# x: 145..355 — держим внутри стенки, иначе цветок торчит мимо коробки.
# t0: кадр старта (26..70) — чем больше, тем позже выпрыгивает.
BOX_SHOTS = {
    'flowerbox': {
        'box': BOX_STYLES['orange'],
        'flowers': [
            # --- передний ряд: низкие цветы с короткими стеблями ---
            {'kind': 'pop', 'x': 262, 'h': 122, 'r': 24, 't0': 64, 'tilt': -2.5,
             'colors': P_ORANGE},
            {'kind': 'daisy', 'x': 216, 'h': 140, 'petals': 6, 'pr': 18, 'pw': 13,
             'rc': 12, 't0': 60, 'tilt': 3,
             'colors': {'petal': hx('fff3dd'), 'center': hx('e8873a')}},
            {'kind': 'bud', 'x': 322, 'h': 148, 't0': 68, 'tilt': 2,
             'colors': {'head': hx('ef6a9e')}},
            {'kind': 'tulip', 'x': 172, 'h': 164, 't0': 56, 'tilt': -3,
             'colors': {'head': hx('b487e8')}},
            # --- средний ряд ---
            {'kind': 'pop', 'x': 306, 'h': 198, 'r': 26, 't0': 50, 'tilt': 2.5,
             'colors': P_BLUE},
            {'kind': 'daisy', 'x': 252, 'h': 214, 'petals': 7, 't0': 45, 'tilt': -2.5,
             'colors': P_PINK},
            {'kind': 'tulip', 'x': 338, 'h': 232, 't0': 52, 'tilt': 3,
             'colors': {'head': hx('ffc233')}},
            {'kind': 'tulip', 'x': 196, 'h': 252, 't0': 38, 'tilt': -2,
             'colors': P_RED},
            # --- задний ряд: первыми выскакивают бутоны на стеблях ---
            {'kind': 'bud', 'x': 172, 'h': 242, 't0': 28, 'tilt': 2.5,
             'colors': {'head': hx('ffc233'), 'leaf': hx('6db46a')}},
            {'kind': 'bud', 'x': 255, 'h': 226, 't0': 31, 'tilt': -2,
             'colors': {'head': hx('b487e8'), 'leaf': hx('8cc86f')}},
            {'kind': 'bud', 'x': 332, 'h': 236, 't0': 34, 'tilt': 2,
             'colors': {'head': hx('f9b7cd'), 'leaf': hx('57a05c')}},
        ],
    },
    'flowerboxb': {
        'box': BOX_STYLES['blue'],
        'flowers': [
            {'kind': 'bud', 'x': 250, 'h': 130, 't0': 68, 'tilt': -2,
             'colors': {'head': hx('ff8f5e')}},
            {'kind': 'daisy', 'x': 296, 'h': 142, 'petals': 6, 'pr': 18, 'pw': 13,
             'rc': 12, 't0': 62, 'tilt': 3,
             'colors': {'petal': hx('fff3dd'), 'center': hx('e8873a')}},
            {'kind': 'pop', 'x': 206, 'h': 160, 'r': 24, 't0': 57, 'tilt': 2.5,
             'colors': {'outer': hx('ffc233'), 'ring': hx('e8873a'),
                        'inner': hx('a04a20')}},
            {'kind': 'tulip', 'x': 332, 'h': 172, 't0': 52, 'tilt': 3,
             'colors': {'head': hx('ff8f5e')}},
            {'kind': 'daisy', 'x': 168, 'h': 212, 'petals': 8, 't0': 46, 'tilt': -3,
             'colors': P_PINK},
            {'kind': 'pop', 'x': 254, 'h': 226, 'r': 26, 't0': 42, 'tilt': 2,
             'colors': {'outer': hx('e8434c'), 'ring': hx('ffd166'),
                        'inner': hx('8e2030')}},
            {'kind': 'tulip', 'x': 330, 'h': 244, 't0': 36, 'tilt': -2.5,
             'colors': {'head': hx('ffc233')}},
            {'kind': 'bud', 'x': 158, 'h': 248, 't0': 28, 'tilt': 2.5,
             'colors': {'head': hx('ffc233'), 'leaf': hx('6db46a')}},
            {'kind': 'bud', 'x': 292, 'h': 228, 't0': 31, 'tilt': -2,
             'colors': {'head': hx('f9b7cd'), 'leaf': hx('8cc86f')}},
            {'kind': 'bud', 'x': 218, 'h': 236, 't0': 34, 'tilt': 2,
             'colors': {'head': hx('fff3dd'), 'leaf': hx('57a05c')}},
        ],
    },
    'flowerboxc': {
        'box': BOX_STYLES['pink'],
        'flowers': [
            {'kind': 'pop', 'x': 260, 'h': 126, 'r': 24, 't0': 65, 'tilt': -2.5,
             'colors': P_BLUE},
            {'kind': 'bud', 'x': 310, 'h': 140, 't0': 69, 'tilt': 2,
             'colors': {'head': hx('ffc233')}},
            {'kind': 'tulip', 'x': 210, 'h': 158, 't0': 58, 'tilt': 3,
             'colors': {'head': hx('fff3ea')}},
            {'kind': 'tulip', 'x': 168, 'h': 184, 't0': 53, 'tilt': -3,
             'colors': {'head': hx('ffc233')}},
            {'kind': 'pop', 'x': 345, 'h': 204, 'r': 25, 't0': 49, 'tilt': 2.5,
             'colors': {'outer': hx('ff8a3d'), 'ring': hx('ffd166'),
                        'inner': hx('d9542f')}},
            {'kind': 'daisy', 'x': 262, 'h': 220, 'petals': 7, 't0': 44, 'tilt': 2.5,
             'colors': {'petal': hx('ef5a63'), 'center': hx('ffd166')}},
            {'kind': 'tulip', 'x': 300, 'h': 248, 't0': 37, 'tilt': -2,
             'colors': {'head': hx('4d8fe8')}},
            {'kind': 'bud', 'x': 172, 'h': 244, 't0': 28, 'tilt': 2,
             'colors': {'head': hx('4d8fe8'), 'leaf': hx('7bb86b')}},
            {'kind': 'bud', 'x': 232, 'h': 226, 't0': 31, 'tilt': -2.5,
             'colors': {'head': hx('fff3ea'), 'leaf': hx('6db46a')}},
            {'kind': 'bud', 'x': 330, 'h': 236, 't0': 34, 'tilt': 2.5,
             'colors': {'head': hx('f9b7cd'), 'leaf': hx('57a05c')}},
        ],
    },
}


FILE_PREFIX = '11_'   # нумерация файлов пака «Цветы» (11_flowerbox*.json)


def main():
    names = sys.argv[1:] or ['flowerbox_a']
    if names == ['all']:
        names = list(BOX_SHOTS)
    for nm in names:
        shots = BOX_SHOTS[nm]
        anim_json = doc(shots, nm)
        out = os.path.join(ROOT, 'img', 'flowers', FILE_PREFIX + nm + '.json')
        os.makedirs(os.path.dirname(out), exist_ok=True)
        with open(out, 'w', encoding='utf-8') as f:
            json.dump(anim_json, f, separators=(',', ':'))
        kb = os.path.getsize(out) / 1024
        print('%s -> img/flowers/%s%s.json (%.1f KB)' % (nm, FILE_PREFIX, nm, kb))


if __name__ == '__main__':
    main()
