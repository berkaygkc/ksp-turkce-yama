#!/usr/bin/env python3
"""Ceviri partilerini sozluk dosyalarina yazar.

Guvenlik:
  - once dogrula.py calistirilir, hata varsa yazmaz
  - BOM + CRLF korunur
  - anahtar/satir sayisi degismemeli, degisirse geri alir
  - her calistirmada .onceki yedegi birakir
"""
import io
import os
import re
import shutil
import subprocess
import sys

KOK = os.path.dirname(os.path.abspath(__file__))
OYUN = os.path.dirname(KOK)
GD = os.path.join(OYUN, "GameData")

SOZLUKLER = {
    "squad":    os.path.join(GD, "Squad/Localization/dictionary.cfg"),
    "serenity": os.path.join(GD, "SquadExpansion/Serenity/Localization/dictionary.cfg"),
}


def harita_yukle():
    h = {}
    with io.open(os.path.join(KOK, "harita.tsv"), encoding="utf-8") as f:
        next(f)
        for satir in f:
            p = satir.rstrip("\n").split("\t")
            if len(p) >= 3:
                h[p[0]] = (p[1], p[2])       # idx -> (anahtar, dosya)
    return h


def ceviriler_yukle(faz=None):
    """faz verilirse sadece o fazin partileri uygulanir (or. 'P1').
    Paralel calisan ajanlar baska fazlara yaziyorken guvenli uygulama saglar."""
    c = {}
    d = os.path.join(KOK, "partiler/ceviri")
    if not os.path.isdir(d):
        return c
    for ad in sorted(os.listdir(d)):
        if not ad.endswith(".tsv"):
            continue
        if faz and not ad.startswith(faz + "-"):
            continue
        with io.open(os.path.join(d, ad), encoding="utf-8") as f:
            for satir in f:
                if "\t" not in satir:
                    continue
                i, tr = satir.rstrip("\n").split("\t", 1)
                if tr.strip():
                    c[i] = tr
    return c


def main():
    faz_arg = [a for a in sys.argv[1:] if a.startswith("--faz=")]
    if "--dogrulamayi-atla" not in sys.argv:
        r = subprocess.run([sys.executable, os.path.join(KOK, "dogrula.py")]
                           + faz_arg)
        if r.returncode != 0:
            print("\nDogrulama basarisiz - yazma iptal.")
            return 1

    faz = None
    for a in sys.argv[1:]:
        if a.startswith("--faz="):
            faz = a.split("=", 1)[1]
    harita = harita_yukle()
    ceviri = ceviriler_yukle(faz)
    if faz:
        print(f"(sadece {faz} partileri uygulanacak)")
    if not ceviri:
        print("uygulanacak ceviri yok"); return 0

    # dosya bazinda anahtar -> turkce
    hedefler = {}
    for i, tr in ceviri.items():
        if i not in harita:
            print(f"uyari: idx {i} haritada yok, atlandi")
            continue
        anahtar, dosya = harita[i]
        hedefler.setdefault(dosya, {})[anahtar] = tr

    toplam = 0
    for dosya, esleme in hedefler.items():
        yol = SOZLUKLER[dosya]
        shutil.copy2(yol, yol + ".onceki")

        with io.open(yol, "r", encoding="utf-8", newline="") as f:
            satirlar = f.readlines()
        onceki_satir = len(satirlar)
        onceki_anahtar = sum(
            1 for s in satirlar if re.match(r"^\s*#[A-Za-z0-9_]+\s*=", s))

        n = 0
        for j, satir in enumerate(satirlar):
            m = re.match(r"^(\s*)#([A-Za-z0-9_]+)(\s*=\s*)(.*?)(\r?\n?)$", satir)
            if not m:
                continue
            girinti, anahtar, ayrac, _, son = m.groups()
            if anahtar in esleme:
                satirlar[j] = (f"{girinti}#{anahtar}{ayrac}"
                               f"{esleme[anahtar]}{son}")
                n += 1

        yeni_satir = len(satirlar)
        yeni_anahtar = sum(
            1 for s in satirlar if re.match(r"^\s*#[A-Za-z0-9_]+\s*=", s))
        if (yeni_satir, yeni_anahtar) != (onceki_satir, onceki_anahtar):
            print(f"!! {dosya}: satir/anahtar sayisi degisti - yazilmadi")
            continue

        with io.open(yol, "w", encoding="utf-8", newline="") as f:
            f.writelines(satirlar)
        print(f"{dosya}: {n} anahtar yazildi "
              f"({yeni_anahtar} anahtar / {yeni_satir} satir korundu)")
        toplam += n

    print(f"\nTOPLAM {toplam} anahtar guncellendi.")
    print(f"Ilerleme: {len(ceviri)}/{len(harita)} "
          f"(%{100*len(ceviri)/max(len(harita),1):.1f})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
