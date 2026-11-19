# -*- coding: utf-8 -*-
"""Оживление картинки-тюльпана (otladka/i.webp): Lottie из готового рисунка.

Версия с заметным движением цветка:
  1) белый фон исходника становится прозрачным;
  2) бутон и листья вырезаются в отдельные PNG-слои;
  3) стебель рисуется векторной кривой и реально изгибается от корня;
  4) бутон следует за верхушкой стебля, листья качаются от своих оснований;
  5) лепестки и блёстки дополняют движение, но не заменяют его.

Все PNG вшиваются в JSON base64 — отдельные файлы картинок не нужны.
Цикл: 6 секунд, 30 кадров/с. Исходный otladka/i.webp не изменяется.

Запуск:  C:/Users/ADMIN/AppData/Local/Programs/Python/Python313/python.exe
         tools/make_tulip_from_image.py
Выход:   otladka/tulip_anim.json (превью) и img/flowers/02_tulip.json (карточка)
"""
import base64
import io
import json
import math
import os
import sys

from PIL import Image, ImageChops, ImageDraw, ImageFilter

sys.stdout.reconfigure(encoding='utf-8')

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'otladka', 'i.webp')
PREVIEW_OUT = os.path.join(ROOT, 'otladka', 'tulip_anim.json')
CARD_OUT = os.path.join(ROOT, 'img', 'flowers', '02_tulip.json')

FR, OP = 30, 180
EASE = {"i": {"x": [0.5], "y": [1]}, "o": {"x": [0.5], "y": [0]}}
EASE2 = {"i": {"x": [0.5, 0.5], "y": [1, 1]},
         "o": {"x": [0.5, 0.5], "y": [0, 0]}}
LIN = {"i": {"x": [0.833], "y": [0.833]},
       "o": {"x": [0.167], "y": [0.167]}}
LIN2 = {"i": {"x": [0.833, 0.833], "y": [0.833, 0.833]},
        "o": {"x": [0.167, 0.167], "y": [0.167, 0.167]}}

PINK = [0.91, 0.33, 0.42]
GOLD = [1.0, 0.87, 0.55]
STEM_DARK = [0.25, 0.36, 0.15]
STEM_GREEN = [0.43, 0.56, 0.27]
STEM_LIGHT = [0.72, 0.82, 0.46]

# Начало и конец одинаковы: зацикливание без скачка.
# +1 — ветер вправо, -1 — влево.
WIND_KEYS = [(0, 0.0), (45, 1.0), (90, 0.0), (135, -1.0), (179, 0.0)]
ROOT_X, ROOT_Y = 203.0, 710.0
TOP_X, TOP_Y = 202.0, 286.0
BEND_PIXELS = 29.4


# ---------------- подготовка картинок ----------------

def key_out_white(img):
    """Убирает только наружный белый фон, сохраняя светлые блики бутона."""
    img = img.convert('RGBA')
    w, h = img.size
    px = img.load()
    for xy in [(0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1),
               (w // 2, 0), (0, h // 2)]:
        if px[xy][:3] != (255, 0, 255):
            ImageDraw.floodfill(img, xy, value=(255, 0, 255, 255), thresh=12)
    data = [(0, 0, 0, 0) if (r, g, b) == (255, 0, 255) else (r, g, b, a)
            for (r, g, b, a) in img.getdata()]
    img.putdata(data)
    r, g, b, a = img.split()
    a = a.filter(ImageFilter.MinFilter(3)).filter(ImageFilter.GaussianBlur(0.6))
    return Image.merge('RGBA', (r, g, b, a))


def remove_white_matte(img):
    """Убирает белый ореол: восстанавливает цвет полупрозрачных краёв."""
    cleaned = []
    for r, g, b, a in img.getdata():
        if 0 < a < 255:
            r = max(0, min(255, round(255 + (r - 255) * 255 / a)))
            g = max(0, min(255, round(255 + (g - 255) * 255 / a)))
            b = max(0, min(255, round(255 + (b - 255) * 255 / a)))
        cleaned.append((r, g, b, a))
    img.putdata(cleaned)
    return img


def polygon_mask(size, points):
    mask = Image.new('L', size, 0)
    ImageDraw.Draw(mask).polygon(points, fill=255)
    return mask


def apply_mask(img, mask):
    out = img.copy()
    out.putalpha(ImageChops.multiply(out.getchannel('A'), mask))
    return out


def to_png_b64(img):
    buf = io.BytesIO()
    img.save(buf, 'PNG', optimize=True)
    return 'data:image/png;base64,' + base64.b64encode(buf.getvalue()).decode('ascii')


# ---------------- Lottie-помощники ----------------

def value_keys(points, multi=False):
    """points = [(кадр, значение), ...]; easing обязателен для lottie-web."""
    ease = EASE2 if multi else EASE
    return {"a": 1, "k": [dict(ease, t=t, s=value) for t, value in points]}


def scalar_keys(amplitude):
    return value_keys([(t, [round(amplitude * wind, 3)]) for t, wind in WIND_KEYS])


def directional_keys(right_amplitude, left_amplitude):
    """Разный угол вправо/влево: листья не вылезают за границы рисунка."""
    return value_keys([
        (t, [right_amplitude if wind > 0 else left_amplitude if wind < 0 else 0])
        for t, wind in WIND_KEYS
    ])


def image_layer(ind, ref_id, anchor, position, rotation=None, name='img'):
    pos = position if isinstance(position, dict) else {"a": 0, "k": list(position) + [0]}
    return {
        "ddd": 0, "ind": ind, "ty": 2, "nm": name, "sr": 1,
        "ks": {
            "o": {"a": 0, "k": 100},
            "r": rotation or {"a": 0, "k": 0},
            "p": pos,
            "a": {"a": 0, "k": [anchor[0], anchor[1], 0]},
            "s": {"a": 0, "k": [100, 100, 100]}
        },
        "ao": 0, "refId": ref_id,
        "ip": 0, "op": OP, "st": 0, "bm": 0
    }


def shape_layer(ind, shapes, name='vec'):
    return {
        "ddd": 0, "ind": ind, "ty": 4, "nm": name, "sr": 1,
        "ks": {
            "o": {"a": 0, "k": 100}, "r": {"a": 0, "k": 0},
            "p": {"a": 0, "k": [0, 0, 0]}, "a": {"a": 0, "k": [0, 0, 0]},
            "s": {"a": 0, "k": [100, 100, 100]}
        },
        "ao": 0, "shapes": shapes, "ip": 0, "op": OP, "st": 0, "bm": 0
    }


def fill(color, opacity=100):
    return {"ty": "fl", "c": {"a": 0, "k": color + [1]},
            "o": {"a": 0, "k": opacity}, "r": 1, "nm": "fill"}


def stroke(color, width, opacity=100):
    return {"ty": "st", "c": {"a": 0, "k": color + [1]},
            "o": {"a": 0, "k": opacity}, "w": {"a": 0, "k": width},
            "lc": 2, "lj": 2, "ml": 4, "nm": "stroke"}


def path_shape(v, i, o, c=True):
    return {"ty": "sh", "nm": "shp",
            "ks": {"a": 0, "k": {"c": c, "v": v, "i": i, "o": o}}}


def tr(p=(0, 0), a=(0, 0), s=(100, 100), r=None, o=100):
    return {"ty": "tr",
            "p": p if isinstance(p, dict) else {"a": 0, "k": list(p)},
            "a": {"a": 0, "k": list(a)},
            "s": {"a": 0, "k": list(s)},
            "r": r if r is not None else {"a": 0, "k": 0},
            "o": o if isinstance(o, dict) else {"a": 0, "k": o}}


def grp(items, trf=None):
    return {"ty": "gr", "nm": "g", "it": list(items) + [trf or tr()]}


# ---------------- изгиб стебля и связанное движение ----------------

def stem_x(y, wind):
    """Корень неподвижен; чем выше точка стебля, тем сильнее она отклоняется."""
    progress = max(0.0, min(1.0, (ROOT_Y - y) / (ROOT_Y - TOP_Y)))
    rest_curve = -3.0 * math.sin(math.pi * progress)
    return ROOT_X + (TOP_X - ROOT_X) * progress + rest_curve + BEND_PIXELS * wind * progress ** 1.55


def position_keys(y):
    return value_keys([
        (t, [round(stem_x(y, wind), 3), y, 0]) for t, wind in WIND_KEYS
    ], multi=True)


def smooth_open_path(points):
    """Вершины и касательные Безье: стебель гибкий, без изломов между ключами."""
    incoming, outgoing = [], []
    for idx in range(len(points)):
        prev = points[max(0, idx - 1)]
        nxt = points[min(len(points) - 1, idx + 1)]
        tx = (nxt[0] - prev[0]) * 0.20
        ty = (nxt[1] - prev[1]) * 0.20
        incoming.append([-tx, -ty])
        outgoing.append([tx, ty])
    return {"c": False, "v": points, "i": incoming, "o": outgoing}


def stem_animated_path(x_offset=0.0):
    keys = []
    ys = [710, 625, 540, 455, 370, 286]
    for t, wind in WIND_KEYS:
        points = [[round(stem_x(y, wind) + x_offset, 3), y] for y in ys]
        keys.append(dict(EASE, t=t, s=[smooth_open_path(points)]))
    return {"ty": "sh", "nm": "bending-stem", "ks": {"a": 1, "k": keys}}


def stem_layer(ind=7):
    # Тёмная кромка, основной зелёный и тонкий блик дают объём без тяжёлых эффектов.
    shapes = [
        grp([stem_animated_path(), stroke(STEM_DARK, 31, 70)]),
        grp([stem_animated_path(), stroke(STEM_GREEN, 25, 100)]),
        grp([stem_animated_path(-5), stroke(STEM_LIGHT, 5, 28)])
    ]
    return shape_layer(ind, shapes, 'flexible-stem')


def leaf_joint(ind, y, size=(20, 28)):
    """Небольшая зелёная «подмышка» скрывает шов между вращающимся листом и стеблем."""
    ellipse = {"ty": "el", "nm": "joint",
               "p": {"a": 0, "k": [0, 0]}, "s": {"a": 0, "k": list(size)}}
    return shape_layer(ind, [grp([ellipse, fill(STEM_DARK)],
                                 tr(p=position_keys(y)))], 'leaf-joint')


# ---------------- дополнительные эффекты ----------------

def falling_petal(ind, x0, spin, y_shift=0):
    petal = grp([
        path_shape(
            [(0, 0), (18, -23), (0, -58), (-18, -23)],
            [[-9, -3], [9, -3], [9, 11], [-9, -3]],
            [[9, -3], [-7, -12], [-9, 11], [7, -12]]),
        fill(PINK, 88)
    ], tr(
        p={"a": 1, "k": [
            dict(LIN2, t=0, s=[x0, -70 + y_shift, 0]),
            dict(LIN2, t=45, s=[x0 + 42, 140 + y_shift, 0]),
            dict(LIN2, t=90, s=[x0, 350 + y_shift, 0]),
            dict(LIN2, t=135, s=[x0 - 42, 560 + y_shift, 0]),
            dict(LIN2, t=179, s=[x0, 770 + y_shift, 0])]},
        r={"a": 1, "k": [dict(LIN, t=0, s=[0]), dict(LIN, t=179, s=[spin])]},
        o={"a": 1, "k": [dict(LIN, t=0, s=[0]), dict(LIN, t=18, s=[85]),
                          dict(LIN, t=150, s=[85]), dict(LIN, t=179, s=[0])]}
    ))
    return shape_layer(ind, [petal], 'falling-petal')


SPARKLES = [
    (75, 155, 25, 15, 70, 70),
    (405, 245, 23, 75, 135, 55),
    (135, 420, 20, 125, 175, 80),
    (365, 475, 18, 35, 90, -65),
]


def sparkle_layer(ind, x, y, size, t_in, t_out, spin):
    star = grp([
        path_shape(
            [(0, -size), (size * 0.20, -size * 0.20), (size, 0),
             (size * 0.20, size * 0.20), (0, size),
             (-size * 0.20, size * 0.20), (-size, 0),
             (-size * 0.20, -size * 0.20)],
            [(0, 0)] * 8, [(0, 0)] * 8),
        fill(GOLD, 95)
    ], {
        "ty": "tr", "p": {"a": 0, "k": [x, y]}, "a": {"a": 0, "k": [0, 0]},
        "s": {"a": 1, "k": [
            dict(EASE2, t=t_in, s=[0, 0, 100]),
            dict(EASE2, t=(t_in + t_out) // 2, s=[125, 125, 100]),
            dict(EASE2, t=t_out, s=[0, 0, 100]), dict(EASE2, t=OP, s=[0, 0, 100])]},
        "r": {"a": 1, "k": [dict(LIN, t=t_in, s=[0]), dict(LIN, t=t_out, s=[spin])]},
        "o": {"a": 1, "k": [dict(LIN, t=t_in, s=[0]),
                              dict(LIN, t=(t_in + t_out) // 2, s=[95]),
                              dict(LIN, t=t_out, s=[0]), dict(LIN, t=OP, s=[0])]}
    })
    return shape_layer(ind, [star], 'sparkle')


# ---------------- сборка ----------------

def main():
    src = Image.open(SRC)
    w, h = src.size
    img = remove_white_matte(key_out_white(src))

    # Контур проходит снаружи бутона. Верхние кончики листьев в слой головы не попадают.
    head_outline = [
        (200, 5), (260, 5), (295, 25), (320, 75), (322, 180),
        (305, 240), (275, 275), (230, 291), (205, 297), (170, 296),
        (125, 288), (85, 275), (60, 240), (45, 190), (45, 115),
        (55, 65), (70, 35), (90, 35), (105, 65), (125, 35), (160, 12)
    ]
    head_mask = polygon_mask((w, h), head_outline)
    head_full = apply_mask(img, head_mask)
    head_box = (35, 0, 330, 302)
    head = head_full.crop(head_box)

    # Убираем бутон и старый прямой стебель: вместо него будет гибкий векторный.
    base_alpha = ImageChops.subtract(img.getchannel('A'), head_mask)
    base = img.copy()
    base.putalpha(base_alpha)
    old_stem_mask = polygon_mask((w, h), [(190, 282), (218, 282), (219, 725), (189, 725)])
    base.putalpha(ImageChops.subtract(base.getchannel('A'), old_stem_mask))

    left_box = (0, 215, 200, 630)
    right_box = (207, 205, 447, 655)
    left_leaf = base.crop(left_box)
    right_leaf = base.crop(right_box)

    # Точки крепления листьев и бутона заданы в координатах исходного рисунка.
    head_pivot = (TOP_X, TOP_Y)
    left_pivot = (190.0, 580.0)
    right_pivot = (213.0, 620.0)

    layers = [
        # В Lottie первые слои находятся на переднем плане.
        sparkle_layer(1, *SPARKLES[0]),
        sparkle_layer(2, *SPARKLES[1]),
        sparkle_layer(3, *SPARKLES[2]),
        sparkle_layer(4, *SPARKLES[3]),
        image_layer(
            5, 'img_head',
            (head_pivot[0] - head_box[0], head_pivot[1] - head_box[1]),
            position_keys(TOP_Y), rotation=scalar_keys(4.9), name='head-follows-stem'
        ),
        image_layer(
            6, 'img_left_leaf',
            (left_pivot[0] - left_box[0], left_pivot[1] - left_box[1]),
            position_keys(left_pivot[1]), rotation=directional_keys(7.7, -4.2), name='left-leaf-sway'
        ),
        image_layer(
            7, 'img_right_leaf',
            (right_pivot[0] - right_box[0], right_pivot[1] - right_box[1]),
            position_keys(right_pivot[1]), rotation=directional_keys(-6.3, 4.2), name='right-leaf-sway'
        ),
        leaf_joint(8, left_pivot[1]),
        leaf_joint(9, right_pivot[1], (18, 26)),
        stem_layer(10),
        falling_petal(11, 100, 400, 0),
        falling_petal(12, 390, -540, 160),
        falling_petal(13, 285, 460, 330),
    ]

    assets = [
        {"id": 'img_head', "w": head.width, "h": head.height,
         "u": "", "p": to_png_b64(head), "e": 1},
        {"id": 'img_left_leaf', "w": left_leaf.width, "h": left_leaf.height,
         "u": "", "p": to_png_b64(left_leaf), "e": 1},
        {"id": 'img_right_leaf', "w": right_leaf.width, "h": right_leaf.height,
         "u": "", "p": to_png_b64(right_leaf), "e": 1},
    ]

    doc = {"v": "5.7.4", "fr": FR, "ip": 0, "op": OP, "w": w, "h": h,
           "nm": "tulip-live-flex", "ddd": 0, "assets": assets, "layers": layers}
    for out in (PREVIEW_OUT, CARD_OUT):
        with open(out, 'w', encoding='utf-8') as f:
            json.dump(doc, f, indent=1)

    print('Разделено: бутон %sx%s, левый лист %sx%s, правый лист %sx%s' % (
        head.width, head.height, left_leaf.width, left_leaf.height,
        right_leaf.width, right_leaf.height))
    print('Изгиб верхушки: ±%s px; бутон: ±4.9°; листья: до 7.7°' % BEND_PIXELS)
    print('Готово:', PREVIEW_OUT, 'и', CARD_OUT)


if __name__ == '__main__':
    main()
