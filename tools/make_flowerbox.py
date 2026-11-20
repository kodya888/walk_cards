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
    если его забыли, добавляем нейтральный, иначе слой не рисуется вообще."""
    items = list(items)
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
def daisy_shapes(h, petals, pr, pw, rc, pet_c, cen_c, dot_c=None):
    """Ромашка: n лепестков-эллипсов вокруг центра. Основание в (0,0)."""
    hc = (0, -h)
    shapes = []
    for i in range(petals):
        deg = i * 360.0 / petals
        petal = [ell(0, -h - pr, pw, pr, "petal"), fill(pet_c)]
        shapes.append(g_rot(petal, hc, deg, "pet%d" % i))
    core = [ell(0, -h, rc, rc, "core"), fill(cen_c)]
    if dot_c:
        core += [ell(0, -h, rc * 0.45, rc * 0.45, "dot"), fill(dot_c)]
    shapes.append(grp(*core))
    return shapes


def pop_shapes(h, r, outer_c, ring_c, inner_c):
    """Круглый цветок: большой круг + кольцо + серединка."""
    return [
        grp(ell(0, -h, r, r, "big"), fill(outer_c)),
        grp(ell(0, -h, r * 0.62, r * 0.62, "ring"), fill(ring_c)),
        grp(ell(0, -h, r * 0.26, r * 0.26, "mid"), fill(inner_c)),
    ]


def tulip_shapes(h, head_c, stem_c):
    """Тюльпан: стебель + чашечка. Основание в (0,0)."""
    top = -h
    cup = pth(
        [(-34, top + 34), (34, top + 34), (24, top - 6), (0, top - 26), (-24, top - 6)],
        [[0, 0], [5, -14], [4, -22], [0, -6], [-4, -22]],
        [[-8, 4], [-5, -14], [-3, -14], [3, -14], [8, 4]], c=True)
    inner = pth(
        [(-16, top + 30), (16, top + 30), (10, top - 16), (0, top - 24), (-10, top - 16)],
        [[0, 0], [3, -16], [2, -12], [0, -6], [-2, -12]],
        [[-5, 2], [-2, -14], [-2, -12], [2, -12], [5, 2]], c=True)
    stem = pth([(0, 2), (0, top + 36)], [[0, 0], [0, 0]], [[0, 0], [0, 0]], nm="stem")
    return [
        grp(stem, stroke(stem_c, 8)),
        grp(cup, fill(head_c)),
        grp(inner, fill(mix(head_c, [1, 1, 1], 0.28))),
    ]


def leaf(x, y, rx, ry, deg, c, pivot):
    return g_rot([ell(x, y, rx, ry, "leaf"), fill(c)], pivot, deg, "leaf")


def sprig_shapes(h, leaf_c, stem_c):
    """Зелёная веточка-заполнитель."""
    top = -h
    stem = pth([(0, 2), (0, top)], [[0, 0], [0, 0]], [[0, 0], [0, 0]], nm="stem")
    shapes = [grp(stem, stroke(stem_c, 7))]
    shapes.append(leaf(-14, top + 30, 9, 22, -34, leaf_c, (0, top + 36)))
    shapes.append(leaf(14, top + 58, 9, 20, 30, leaf_c, (0, top + 62)))
    shapes.append(leaf(0, top, 10, 22, 0, leaf_c, (0, top + 4)))
    return shapes


def bell_shapes(h, r, pet_c, cen_c):
    """Простой цветок из 5 круглых лепестков."""
    hc = (0, -h)
    shapes = []
    for i in range(5):
        deg = i * 72.0 + 14
        shapes.append(g_rot(
            [ell(0, -h - r * 0.62, r * 0.62, r * 0.62, "petal"), fill(pet_c)],
            hc, deg, "pet%d" % i))
    shapes.append(grp(ell(0, -h, r * 0.46, r * 0.46, "core"), fill(cen_c)))
    return shapes


KINDS = {
    'daisy': daisy_shapes,
    'pop': pop_shapes,
    'tulip': tulip_shapes,
    'sprig': sprig_shapes,
    'bell': bell_shapes,
}

GREEN = hx('2d6b3c')


def flower_shapes(f):
    k = f['kind']
    c = f.get('colors', {})
    if k == 'daisy':
        return daisy_shapes(
            f['h'], f.get('petals', 7), f.get('pr', 16), f.get('pw', 7),
            f.get('rc', 13),
            c.get('petal', hx('f28fb2')), c.get('center', hx('ffd166')),
            c.get('dot'))
    if k == 'pop':
        return pop_shapes(
            f['h'], f.get('r', 30),
            c.get('outer', hx('6fa8ff')), c.get('ring', hx('b3d4ff')),
            c.get('inner', hx('2b5fc9')))
    if k == 'tulip':
        return tulip_shapes(f['h'], c.get('head', hx('e94f5f')),
                            c.get('stem', GREEN))
    if k == 'sprig':
        return sprig_shapes(f['h'], c.get('leaf', hx('57a05c')),
                            c.get('stem', GREEN))
    if k == 'bell':
        return bell_shapes(f['h'], f.get('r', 26),
                           c.get('petal', hx('ffd166')), c.get('center', hx('e8873a')))
    raise KeyError(k)


# ======================================================================
#  Анимация одного цветка
# ======================================================================
T_SINK = 104             # с этого кадра все цветы прячутся в коробку
T_HIDDEN = 116           # к этому кадру скрылись (до конца цикла пусто)


def flower_layer(ind, f, nm):
    """Слой цветка. Прятание за стенкой — через масштаб: до прыжка цветок
    сжат до 2 % прямо за стенкой (основание чуть ниже кромки), затем растёт
    и «выстреливает» вверх с перелётом, оседает и качается."""
    x = f['x']
    t0 = f.get('t0', 26)
    rim = RIM
    y_hide = rim + 10                                  # спрятан за стенкой
    y_end = rim + 4                                    # приземляется у кромки
    y_over = rim - 8                                   # лёгкий перелёт вверх

    pos = anim([
        kf3(t0, x, y_hide, LIN),
        kf3(t0 + 9, x, y_over, EASE),
        kf3(t0 + 15, x, y_end, EASE),
        kf3(T_SINK, x, y_end, LIN),
        kf3(T_HIDDEN, x, y_hide, IN_H),
        kf3(OP - 1, x, y_hide, LIN),
    ])
    sc = anim([
        kf(t0, [2, 2], LIN),
        kf(t0 + 9, [112, 112], EASE),
        kf(t0 + 15, [100, 100], EASE),
        kf(T_SINK, [100, 100], LIN),
        kf(T_HIDDEN, [2, 2], IN_H),
        kf(OP - 1, [2, 2], LIN),
    ])
    # лёгкое покачивание после приземления: до T_SINK, ключи строго по возрастанию.
    # ВАЖНО: у вращения значения ключей ОБЯЗАНЫ быть массивами [deg] —
    # lottie-web 5.13 на скалярах s:0 ломается и рисует слой под ~78°.
    tilt = f.get('tilt', 2)
    rt_keys = [kf(t0, [0], LIN), kf(t0 + 15, [0], LIN)]
    t, amp, sign = t0 + 30, tilt, 1
    while t < T_SINK - 2:
        rt_keys.append(kf(t, [sign * amp], EASE))
        t += 16
        sign = -sign
        amp = max(1.0, amp * 0.7)
    rt_keys += [kf(T_SINK, [0], LIN), kf(T_HIDDEN, [0], LIN), kf(OP - 1, [0], LIN)]
    rt = anim(rt_keys)
    if t0 >= T_SINK - 16:                       # защита: старт слишком поздно
        raise ValueError('t0 слишком большой: %s' % t0)
    return layer(ind, flower_shapes(f), pos, sc, rt, nm=nm)


# ======================================================================
#  Коробка
# ======================================================================
def box_front_shapes(b):
    """Передняя стенка + кромка + рисунок (рисуется ПОВЕРХ цветов)."""
    body = hx(b['body'])
    edge = hx(b['edge'])
    deco = hx(b['deco'])
    shapes = [
        grp(quad((BOX_X0 - 6, RIM + 1), (BOX_X1 + 6, RIM + 1),
                 (BOX_X1 + 2, RIM + 22), (BOX_X0 + 2, RIM + 22), "rim"),
            fill(edge)),
        grp(quad((BOX_X0 + 4, RIM + 20), (BOX_X1 - 4, RIM + 20),
                 (BOX_X1 - 18, WALL_BOT), (BOX_X0 + 18, WALL_BOT), "wall"),
            fill(body)),
        grp(pth(  # волнистая линия-рисунок
            [(BOX_X0 + 60, RIM + 70), (BOX_X0 + 100, RIM + 82),
             (BOX_X0 + 140, RIM + 62), (BOX_X0 + 178, RIM + 76)],
            [[0, 0], [-16, 12], [-13, -13], [0, 0]],
            [[0, 0], [14, -12], [14, 14], [0, 0]], nm="squig"),
            stroke(mix(body, [1, 1, 1], 0.38), 9)),
        grp(ell(BOX_X0 + 52, RIM + 48, 10, 10, "hl"), fill(deco)),
        grp(ell(BOX_X0 + 44, RIM + 108, 6, 6, "d1"), fill(mix(body, [1, 1, 1], 0.3))),
        grp(ell(BOX_X1 - 70, RIM + 120, 8, 8, "d2"), fill(mix(body, [1, 1, 1], 0.3))),
    ]
    return shapes


def box_back_shapes(b):
    """Внутренность, задние и боковые створки (рисуется ЗА цветами)."""
    inner = hx(b['inner'])
    back = mix(hx(b['body']), [0, 0, 0], 0.22)
    return [
        grp(quad((BOX_X0 + 14, RIM + 12), (BOX_X1 - 14, RIM + 12),   # щель внутри
                 (BOX_X1 - 22, RIM - 16), (BOX_X0 + 22, RIM - 16), "slot"),
            fill(inner)),
        grp(quad((BOX_X0 + 24, RIM - 14), (BOX_X0 + 106, RIM - 18),  # задняя лев. створка
                 (BOX_X0 + 84, RIM - 78), (BOX_X0 - 6, RIM - 54), "bflapL"),
            fill(back)),
        grp(quad((BOX_X1 - 24, RIM - 14), (BOX_X1 - 106, RIM - 18),  # задняя прав. створка
                 (BOX_X1 - 84, RIM - 78), (BOX_X1 + 6, RIM - 54), "bflapR"),
            fill(mix(back, [0, 0, 0], 0.06))),
        grp(quad((BOX_X0 - 2, RIM + 12), (BOX_X0 + 58, RIM + 18),    # боковая лев. створка
                 (BOX_X0 + 38, RIM + 62), (BOX_X0 - 26, RIM + 40), "sflapL"),
            fill(back)),
        grp(quad((BOX_X1 + 2, RIM + 12), (BOX_X1 - 58, RIM + 18),    # боковая прав. створка
                 (BOX_X1 - 38, RIM + 62), (BOX_X1 + 26, RIM + 40), "sflapR"),
            fill(mix(back, [0, 0, 0], 0.06))),
    ]


def sparkle_layer(ind, x, y, r, t, nm):
    """Мелькающая блёстка: крестик, вспыхивает по своей фазе."""
    c = hx('ffe9a3')
    op = anim([
        kf(t % OP, 0, LIN), kf((t + 8) % OP, 90, EASE),
        kf((t + 18) % OP, 0, EASE), kf(OP - 1, 0, LIN)])
    sc = anim([
        kf(t % OP, [60, 60], LIN), kf((t + 8) % OP, [110, 110], EASE),
        kf((t + 18) % OP, [60, 60], EASE), kf(OP - 1, [60, 60], LIN)])
    shapes = [
        grp(pth([(0, -r), (0, r)], [[0, 0], [0, 0]], [[0, 0], [0, 0]], nm="s1"),
            stroke(c, 7)),
        grp(pth([(-r, 0), (r, 0)], [[0, 0], [0, 0]], [[0, 0], [0, 0]], nm="s2"),
            stroke(c, 7)),
    ]
    return layer(ind, shapes,
                 {"a": 0, "k": [x, y, 0]}, sc, o_k=op, nm=nm)


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
    return {"v": "5.7.4", "fr": FR, "ip": 0, "op": OP, "w": W, "h": H,
            "nm": nm, "ddd": 0, "assets": [], "layers": layers}


# ======================================================================
#  НАСТРОЙКИ: цвета коробок + состав букетов
# ======================================================================
# Палитра цветов-цветков
P_PINK = {'petal': hx('f17ba4'), 'center': hx('ffd166')}
P_BLUE = {'outer': hx('6fa8ff'), 'ring': hx('aecffb'), 'inner': hx('2b5fc9')}
P_RED = {'head': hx('e05055')}
P_YEL = {'petal': hx('ffcf5c'), 'center': hx('e8873a')}
P_ORANGE = {'outer': hx('ff9e5e'), 'ring': hx('ffc79a'), 'inner': hx('d9542f')}

# Стили коробки: body — корпус, edge — кромка, inner — тёмная щель,
# line/deco не используются напрямую в плоском стиле (deco — блики)
BOX_STYLES = {
    'orange': {'body': 'e8804f', 'edge': 'c65a2e', 'inner': '5a2c17', 'deco': 'ffd9b3'},
    'blue':   {'body': '5f8fd6', 'edge': '3d6bb0', 'inner': '1e3557', 'deco': 'cfe0ff'},
    'pink':   {'body': 'e97fa6', 'edge': 'c05a83', 'inner': '5c2337', 'deco': 'ffd4e5'},
    'green':  {'body': '6faf6c', 'edge': '4d8a4e', 'inner': '26402a', 'deco': 'd7f2d7'},
    'purple': {'body': '9b7fd6', 'edge': '7560ad', 'inner': '332a4f', 'deco': 'e6dcff'},
}

# Варианты карточек (каждый — самостоятельный файл).
# Порядок в flowers: первый в списке — ближе к зрителю (перекрывает других).
# x: 150..350 — держим внутри стенки, иначе цветок торчит мимо коробки.
# t0: кадр старта (26..60) — чем больше, тем позже выпрыгивает.
BOX_SHOTS = {
    'flowerbox_a': {
        'box': BOX_STYLES['orange'],
        'flowers': [
            {'kind': 'sprig', 'x': 168, 'h': 200, 't0': 30, 'tilt': 2.5,
             'colors': {'leaf': hx('6db46a')}},
            {'kind': 'sprig', 'x': 330, 'h': 190, 't0': 33, 'tilt': -2.5,
             'colors': {'leaf': hx('8cc86f')}},
            {'kind': 'bell', 'x': 196, 'h': 150, 'r': 27, 't0': 38, 'tilt': -3,
             'colors': P_YEL},
            {'kind': 'tulip', 'x': 268, 'h': 215, 't0': 44, 'tilt': 2,
             'colors': P_RED},
            {'kind': 'daisy', 'x': 316, 'h': 165, 'petals': 7, 't0': 50, 'tilt': 3,
             'colors': P_PINK},
            {'kind': 'pop', 'x': 236, 'h': 150, 'r': 27, 't0': 56, 'tilt': -2,
             'colors': P_BLUE},
        ],
    },
    'flowerbox_b': {
        'box': BOX_STYLES['blue'],
        'flowers': [
            {'kind': 'sprig', 'x': 200, 'h': 195, 't0': 30, 'tilt': 2.5,
             'colors': {'leaf': hx('6db46a')}},
            {'kind': 'daisy', 'x': 246, 'h': 175, 'petals': 8, 't0': 38, 'tilt': -3,
             'colors': P_PINK},
            {'kind': 'bell', 'x': 300, 'h': 148, 'r': 25, 't0': 45, 'tilt': 3,
             'colors': P_ORANGE},
            {'kind': 'pop', 'x': 180, 'h': 150, 'r': 26, 't0': 52, 'tilt': 2,
             'colors': P_YEL and {'outer': hx('ffd166'), 'ring': hx('ffe7a8'),
                                  'inner': hx('d9542f')}},
            {'kind': 'sprig', 'x': 330, 'h': 185, 't0': 58, 'tilt': -2,
             'colors': {'leaf': hx('57a05c')}},
        ],
    },
    'flowerbox_c': {
        'box': BOX_STYLES['pink'],
        'flowers': [
            {'kind': 'sprig', 'x': 175, 'h': 205, 't0': 30, 'tilt': 2,
             'colors': {'leaf': hx('7bb86b')}},
            {'kind': 'tulip', 'x': 220, 'h': 210, 't0': 37, 'tilt': -2.5,
             'colors': {'head': hx('f2c14e')}},
            {'kind': 'pop', 'x': 285, 'h': 150, 'r': 27, 't0': 44, 'tilt': 2,
             'colors': P_BLUE},
            {'kind': 'bell', 'x': 330, 'h': 145, 'r': 24, 't0': 51, 'tilt': -3,
             'colors': {'petal': hx('ffffff'), 'center': hx('ffd166')}},
            {'kind': 'daisy', 'x': 258, 'h': 170, 'petals': 7, 't0': 58, 'tilt': 2.5,
             'colors': {'petal': hx('e05055'), 'center': hx('fff3c4')}},
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
