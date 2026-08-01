#!/usr/bin/env python3
"""KSP icin Turk bayragi dokusu uretir.

Geometri UYDURULMADI: Wikimedia'daki standart Flag_of_Turkey.svg'nin kendi
koordinatlari cozulup G (bayrak eni) cinsine cevrildi. SVG viewBox 90000x60000,
yani G = 60000, boy = 1.5 G:

    dis daire   merkez 30000  yaricap 15000   ->  0.5    G  /  0.25  G
    ic daire    merkez 33750  yaricap 12000   ->  0.5625 G  /  0.2   G
    yildiz      merkez 49250  yaricap  7500   ->  0.8208 G  /  0.125 G
    kirmizi     #e30a17

Yildizin donusu: SVG'de yildizin kose noktalari
    (41750,0) (55318,-4408) (46932,7133) (46932,-7133) (55318,4408)
En soldaki kose (41750, 0) tam olarak merkezle ayni yukseklikte, yani
yildizin bir kolu DOGRUDAN SOLA — ay'in acikligina — bakiyor. Dik duran
yildiz yanlis olurdu.

KSP dokusu 512x256 (2:1), bayragin gercek orani ise 3:2. Gerdirirsek daireler
elipse doner. Onun yerine gercek oranli bayrak (384x256) tuvale ORTALANIYOR;
zemin zaten duz kirmizi oldugu icin ek alan gorunmuyor.
"""
import math
import os
import sys

from PIL import Image, ImageDraw

KIRMIZI = (0xE3, 0x0A, 0x17)
BEYAZ = (255, 255, 255)

# G cinsinden resmi olculer
DIS_MERKEZ, DIS_YARICAP = 0.5, 0.25
IC_MERKEZ,  IC_YARICAP = 0.5625, 0.2
YILDIZ_MERKEZ, YILDIZ_YARICAP = 49250 / 60000, 0.125
YILDIZ_ACI = 180                      # bir kol sola bakar

# Bes kollu yildizin ic/dis yaricap orani
IC_ORAN = math.cos(math.radians(72)) / math.cos(math.radians(36))

ORNEKLEME = 8                         # kenar yumusatma icin buyuk cizip kucult


def yildiz_koseleri(cx, cy, R, aci):
    """10 kose: dis ve ic yaricap donusumlu. Kendisiyle kesisen 5 koseli
    cokgen cizilirse cift-tek dolgu kurali yildizin ortasini BOS birakir."""
    n = []
    for i in range(10):
        a = math.radians(aci + i * 36)
        r = R if i % 2 == 0 else R * IC_ORAN
        n.append((cx + r * math.cos(a), cy - r * math.sin(a)))
    return n


def uret(genislik=512, yukseklik=256):
    g = yukseklik * ORNEKLEME
    W, H = genislik * ORNEKLEME, yukseklik * ORNEKLEME
    # gercek oranli bayragi (1.5 G) tuvale ortala
    kaydir = (W - 1.5 * g) / 2
    cy = H / 2

    im = Image.new("RGBA", (W, H), KIRMIZI + (255,))
    dr = ImageDraw.Draw(im)
    d, r = DIS_MERKEZ * g + kaydir, DIS_YARICAP * g
    dr.ellipse([d - r, cy - r, d + r, cy + r], fill=BEYAZ + (255,))
    d, r = IC_MERKEZ * g + kaydir, IC_YARICAP * g
    dr.ellipse([d - r, cy - r, d + r, cy + r], fill=KIRMIZI + (255,))
    dr.polygon(yildiz_koseleri(YILDIZ_MERKEZ * g + kaydir, cy,
                               YILDIZ_YARICAP * g, YILDIZ_ACI),
               fill=BEYAZ + (255,))
    return im.resize((genislik, yukseklik), Image.LANCZOS)


def _dogrula(im):
    """Uretilen dokunun gercekten bayrak gibi oldugunu olc."""
    px = im.convert("RGB").load()
    W, H = im.size
    sorun = []
    if px[4, 4] != KIRMIZI:
        sorun.append(f"kose kirmizi degil: {px[4, 4]}")
    # ay'in govdesi: dis dairenin sol tarafi beyaz olmali
    g = H
    kaydir = (W - 1.5 * g) / 2
    x = int((DIS_MERKEZ - DIS_YARICAP + 0.02) * g + kaydir)
    if px[x, H // 2] != BEYAZ:
        sorun.append(f"ay govdesi beyaz degil ({x},{H//2}) = {px[x, H // 2]}")
    # ay'in ici: ic dairenin merkezi kirmizi olmali
    x = int(IC_MERKEZ * g + kaydir)
    if px[x, H // 2] != KIRMIZI:
        sorun.append(f"ay ici kirmizi degil ({x},{H//2}) = {px[x, H // 2]}")
    # yildizin merkezi beyaz olmali (ici bos cizilmis olma hatasi)
    x = int(YILDIZ_MERKEZ * g + kaydir)
    if px[x, H // 2] != BEYAZ:
        sorun.append(f"yildiz ortasi bos ({x},{H//2}) = {px[x, H // 2]}")
    # Yildizin bir kolu tam SOLA bakmali. Kolun ucunda piksel cok ince ve
    # kenar yumusatma yuzunden saf beyaz olmaz; olcumu kolun 0.03 G icine
    # kaydirip tolerans veriyoruz. Dik duran yildizda ayni noktada govde
    # olmadigi icin bu denetim iki durumu ayirt eder.
    x = int((YILDIZ_MERKEZ - YILDIZ_YARICAP + 0.03) * g + kaydir)
    r, yesil, mavi = px[x, H // 2]
    if not (r > 200 and yesil > 200 and mavi > 200):
        sorun.append(f"yildizin sol kolu yok ({x},{H//2}) = {(r, yesil, mavi)}"
                     " — yildiz yanlis donmus olabilir")
    return sorun


if __name__ == "__main__":
    hedef = sys.argv[1] if len(sys.argv) > 1 else "TurkBayragi.png"
    im = uret()
    sorunlar = _dogrula(im)
    for s in sorunlar:
        print(f"  !! {s}")
    if sorunlar:
        raise SystemExit(1)
    os.makedirs(os.path.dirname(os.path.abspath(hedef)), exist_ok=True)
    im.save(hedef)
    print(f"  OK  {hedef}  {im.size[0]}x{im.size[1]} {im.mode}  "
          f"{os.path.getsize(hedef):,} bayt")
