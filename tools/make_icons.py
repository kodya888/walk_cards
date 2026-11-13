# Пересборка иконок PWA:
# 1) "any" версии — убираем белую рамку вокруг фиолетового квадрата,
#    углы делаем прозрачными (скругление сохраняем).
# 2) "maskable" версии — фон (фиолетовый) заливает весь квадрат до краёв,
#    рисунок масштабируется в безопасную зону (центральный круг d=80%),
#    чтобы Android не обрезал кроссовок/карточки своей маской.
import sys
from PIL import Image, ImageDraw

sys.stdout.reconfigure(encoding='utf-8')

SRC = r'C:\Users\ADMIN\Documents\ai_moi\walk_cards\icons\icon-512-src.png'
OUT = r'C:\Users\ADMIN\Documents\ai_moi\walk_cards\icons'
BG = (50, 38, 103, 255)          # цвет фона иконки #322667
SAFE = 0.80                       # безопасная зона maskable: круг d=80%


def corner_radius(im, left, top):
    """Радиус скругления: подгонка окружности по двум измерениям края.

    dx = ширина скругления на глубине d от верха: r - sqrt(2rd - d^2) = dx.
    Два измерения -> квадратное уравнение -> r. Надёжнее, чем верхняя строка
    (там пиксели антиалиасные и радиус занижается).
    """
    px = im.load()

    def first_purple(y):
        for x in range(left, left + 200):
            p = px[(x, y)]
            if p[2] > 90 and p[0] < 160:
                return x
        return left

    d1, d2 = 7, 25
    x1 = first_purple(top + d1) - left
    x2 = first_purple(top + d2) - left
    best_r, best_err = None, 1e9
    for r in range(10, 120):  # перебор: точнее аналитики при пиксельном шуме
        e1 = abs(r - (2 * r * d1 - d1 * d1) ** 0.5 - x1)
        e2 = abs(r - (2 * r * d2 - d2 * d2) ** 0.5 - x2)
        if e1 + e2 < best_err:
            best_err, best_r = e1 + e2, r
    return best_r


def purple_bounds(im):
    """Границы фиолетового квадрата (не-белая область)."""
    w, h = im.size
    px = im.load()

    def is_purple(p):
        return p[2] > 90 and p[0] < 160

    left = next(x for x in range(w) if is_purple(px[(x, h // 2)]))
    right = next(x for x in range(w - 1, -1, -1) if is_purple(px[(x, h // 2)]))
    top = next(y for y in range(h) if is_purple(px[(w // 2, y)]))
    bottom = next(y for y in range(h - 1, -1, -1) if is_purple(px[(w // 2, y)]))
    return (left, top, right + 1, bottom + 1)


def rounded_mask(size, radius, inset=0):
    m = Image.new('L', (size, size), 0)
    d = ImageDraw.Draw(m)
    d.rounded_rectangle([inset, inset, size - 1 - inset, size - 1 - inset],
                        radius=radius, fill=255)
    return m


def main():
    im = Image.open(SRC).convert('RGBA')
    bounds = purple_bounds(im)
    sq = im.crop(bounds)
    side = sq.size[0]
    print('bounds:', bounds, 'side:', side)

    # радиус скругления: подгонка окружности по краю угла
    r = corner_radius(im, bounds[0], bounds[1])
    print('corner radius (px в исходном масштабе):', r)

    # --- "any": скруглённый квадрат без белой рамки ---
    for size in (512, 192):
        art = sq.resize((size, size), Image.LANCZOS)
        art.putalpha(rounded_mask(size, round(r * size / side), inset=2))
        path = rf'{OUT}\icon-{size}.png'
        art.save(path)
        print('saved', path)

    # --- "maskable": фон до краёв, рисуем в безопасной зоне ---
    for size in (512, 192):
        canvas = Image.new('RGBA', (size, size), BG)
        safe_side = round(size * SAFE)
        art = sq.resize((safe_side, safe_side), Image.LANCZOS)
        # маска на 3px внутрь: съедаем антиалиасный белый ореол по краям квадрата
        m = rounded_mask(safe_side, round(r * safe_side / side) + 2, inset=3)
        art.putalpha(m)
        off = (size - safe_side) // 2
        canvas.paste(art, (off, off), art)
        path = rf'{OUT}\icon-{size}-maskable.png'
        canvas.save(path)
        print('saved', path)


if __name__ == '__main__':
    main()
