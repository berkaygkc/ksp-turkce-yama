#!/usr/bin/env python3
"""Tum KSPedia sayfalarini tarayip tasanlari raporlar ve resmini uretir.

226 sayfayi oyunda tek tek gezmek yerine, yerlestirme simulasyonu (onizleme.py)
hepsini tarar; sadece SORUNLU sayfalarin resmi uretilir. Boylece incelenecek
sayfa sayisi bir avuca iner.

Kalibrasyon: --kaynak ile ingilizce yedekler taranir. Orada cikan tasmalar
modelin kendi hatasidir (oyunun yazi tipi degil sistem yazi tipi kullaniliyor);
o metinler Turkce taramada da cikacaksa gercek sorun sayilmaz. Rapor bu farki
ayirir.
"""
import glob
import os
import sys

from onizleme import ciz, sayfa_oku, yerlestir
from PIL import Image, ImageDraw

KOK = os.path.dirname(os.path.abspath(__file__))
OYUN = os.path.dirname(KOK)
YEDEK = os.path.join(KOK, "yedek")
CIKTI = os.path.join(KOK, "onizleme")

HEDEF_DIZIN = {
    "Squad":         "GameData/Squad/KSPedia",
    "MakingHistory": "GameData/SquadExpansion/MakingHistory/KSPedia",
    "Serenity":      "GameData/SquadExpansion/Serenity/KSPedia",
    "SquadRoot":     "GameData/Squad",
}


def tara(yol):
    """Sayfadaki tasan metinleri dondurur (resim uretmeden — hizli)."""
    try:
        _, metinler = sayfa_oku(yol)
    except Exception as e:
        return None, str(e)
    dr = ImageDraw.Draw(Image.new("RGB", (8, 8)))
    tasan = []
    for m in metinler:
        if m["font"] <= 0 or m["w"] <= 0 or m["h"] <= 0:
            continue
        if yerlestir(dr, m)[2]:
            tasan.append(m["metin"].split("\n")[0][:44])
    return tasan, None


def main():
    kaynak_modu = "--kaynak" in sys.argv
    os.makedirs(CIKTI, exist_ok=True)

    # once ingilizce kaynagi tara: modelin kendi yanilma payi
    kaynak_tasan = {}
    for yol in sorted(glob.glob(os.path.join(YEDEK, "*", "*.ksp"))):
        anahtar = f"{os.path.basename(os.path.dirname(yol))}/{os.path.basename(yol)}"
        t, hata = tara(yol)
        if t:
            kaynak_tasan[anahtar] = set(t)
    print(f"INGILIZCE kaynak: {sum(len(v) for v in kaynak_tasan.values())} tasma "
          f"({len(kaynak_tasan)} sayfada) — bu modelin yanilma tabani")
    if kaynak_modu:
        for s, v in sorted(kaynak_tasan.items())[:20]:
            print(f"   {s}: {sorted(v)[:2]}")
        return 0

    gercek, toplam_sayfa = [], 0
    for alt, dizin in HEDEF_DIZIN.items():
        for yol in sorted(glob.glob(os.path.join(OYUN, dizin, "*.ksp"))):
            anahtar = f"{alt}/{os.path.basename(yol)}"
            if not os.path.exists(os.path.join(YEDEK, anahtar)):
                continue
            toplam_sayfa += 1
            t, hata = tara(yol)
            if hata:
                print(f"   !! {anahtar}: {hata}")
                continue
            if not t:
                continue
            # kaynakta da tasan sayida metin varsa model yanilgisi olabilir
            taban = len(kaynak_tasan.get(anahtar, ()))
            if len(t) > taban:
                gercek.append((anahtar, t, taban))

    print(f"\nTURKCE: {toplam_sayfa} sayfa tarandi, "
          f"{len(gercek)} sayfada kaynaktan FAZLA tasma var")
    sorunlu_dizin = os.path.join(CIKTI, "sorunlu")
    for anahtar, t, taban in gercek:
        print(f"\n   {anahtar}  ({len(t)} tasma, kaynakta {taban})")
        for x in t[:4]:
            print(f"      {x!r}")
        alt, ad = anahtar.split("/")
        yol = os.path.join(OYUN, HEDEF_DIZIN[alt], ad)
        try:
            p, _, _ = ciz(yol, os.path.join(sorunlu_dizin, f"{alt}_{ad[:-4]}.png"))
            print(f"      resim: {p}")
        except Exception as e:
            print(f"      resim uretilemedi: {e}")
    if not gercek:
        print("   tasma yok — 226 sayfanin hicbirinde kaynaktan fazla sorun cikmadi")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
