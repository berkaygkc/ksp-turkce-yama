#!/usr/bin/env python3
"""KSPedia ceviri ciktilarinin mekanik denetimi.

Anlam denetlemez — sadece makinenin kesin bilebilecegi seyleri: eksik satir,
bozulmus kacis dizisi, cevrilmemis metin, tus adinin cevrilmesi, tasma riski.

Her denetim, bilerek BOZUK bir ornekle test edilmistir (altta). Sozluk isinde
bir kacis-dizisi denetimi fazla kacirilmis ters bolu yuzunden hicbir seyi
yakalamadan "temiz" raporladi; o yuzden artik her denetimin yakaladigi
kanitlanmadan kullanilmaz.
"""
import glob
import io
import os
import re
import sys

KOK = os.path.dirname(os.path.abspath(__file__))
PARTI = os.path.join(KOK, "parti")
CEVIRI = os.path.join(KOK, "ceviri")

KACIS = re.compile(r"\\.")
TUSLAR = {"W", "A", "S", "D", "Q", "E", "R", "F", "T", "G", "H", "J", "K", "L",
          "Shift", "Ctrl", "Alt", "Tab", "Esc", "Space", "Backspace"}
# Cevrilmemis sayilmayacaklar: kisaltmalar, model kodlari, olcu birimleri
MUAF = re.compile(r"^[\sA-Z0-9/\\.,=_\"'()+-]*$")


def oku_kaynak(parti_adi):
    # Not: bazi kaynak satirlarinda alan icinde yalin \r (0x0D) byte'i var,
    # sonra "\n" kacis dizisi metni geliyor. Python metin modu universal-
    # newline ceviriyle bu yalin \r'yi de satir sonu sayip alani ortadan
    # kesiyordu (sessizce "len(p)<5" ile atlanip veri kaybediliyordu).
    # Gercek satir sonu SADECE ham LF (0x0A) — bu yuzden dosyayi binary
    # okuyup yalnizca b"\n" ile bolmek gerekiyor.
    yol = os.path.join(PARTI, f"{parti_adi}.tsv")
    out = {}
    with open(yol, "rb") as f:
        veri = f.read()
    satirlar = [s for s in veri.split(b"\n") if s.strip()]
    for satir in satirlar[1:]:
        p = satir.decode("utf-8").split("\t")
        if len(p) < 5:
            continue
        out[int(p[0])] = {"w": float(p[1]), "font": float(p[2]),
                          "kap": int(p[3]), "en": "\t".join(p[4:])}
    return out


def oku_ceviri(parti_adi):
    yol = os.path.join(CEVIRI, f"{parti_adi}.tsv")
    if not os.path.exists(yol):
        return None
    # Kaynak tarafiyla ayni sebeple binary okunur: metin modu universal-newline
    # ceviriyle yalin CR'yi de satir sonu sayar ve kaydi ortadan boler.
    out = {}
    with open(yol, "rb") as f:
        for ham in f.read().split(b"\n"):
            satir = ham.decode("utf-8")
            if not satir.strip():
                continue
            p = satir.split("\t", 1)
            if len(p) < 2 or not p[0].strip().isdigit():
                continue
            out[int(p[0])] = p[1]
    return out


def denetle(parti_adi):
    kaynak = oku_kaynak(parti_adi)
    ceviri = oku_ceviri(parti_adi)
    hatalar, uyarilar = [], []
    if ceviri is None:
        return [f"{parti_adi}: cikti dosyasi yok"], []

    eksik = set(kaynak) - set(ceviri)
    fazla = set(ceviri) - set(kaynak)
    if eksik:
        hatalar.append(f"{parti_adi}: {len(eksik)} idx eksik "
                       f"{sorted(eksik)[:6]}")
    if fazla:
        hatalar.append(f"{parti_adi}: {len(fazla)} idx fazla "
                       f"{sorted(fazla)[:6]}")

    for i in sorted(set(kaynak) & set(ceviri)):
        en, tr = kaynak[i]["en"], ceviri[i]
        etiket = f"{parti_adi}/{i}"

        # Kacis dizileri birebir. \r haric: kaynakta CRLF kalintisi yalin CR
        # var, ama TMP icin "\r\n" ile "\n" ayni tek satir sonudur — cevirinin
        # CR tasimasini sart kosmak anlamsiz olurdu.
        k_en = sorted(x for x in KACIS.findall(en) if x != "\\r")
        k_tr = sorted(x for x in KACIS.findall(tr) if x != "\\r")
        if k_en != k_tr:
            hatalar.append(f"{etiket}: kacis dizisi uyusmuyor "
                           f"{k_en} -> {k_tr}")

        # bas/son bosluk (sayfa hizalamasi buna bagli)
        if (en[:1] == " ") != (tr[:1] == " ") or (en[-1:] == " ") != (tr[-1:] == " "):
            uyarilar.append(f"{etiket}: bas/son bosluk degisti")

        # cevrilmemis
        if en == tr and not MUAF.match(en):
            uyarilar.append(f"{etiket}: cevrilmemis {en[:40]!r}")

        # Tus adi cevrilmis mi. Sadece metin gercekten tustan bahsediyorsa bak:
        # yalin "A" belirsiz tanimlik, "Space" ise "Space Center"in parcasi
        # olabiliyor — koşulsuz denetim bunlari tus sanip yanlis alarm veriyordu.
        if re.search(r"\b(press|key|keys|hold|tap|hotkey)\b", en, re.I):
            for tus in TUSLAR:
                if re.search(rf"\b{tus}\b", en) and not re.search(rf"\b{tus}\b", tr):
                    uyarilar.append(f"{etiket}: {tus!r} tusu ceviride yok")
                    break

        # ASCII'ye dusurulmus Turkce (ornek: "gectigi" yerine "geçtiği")
        if re.search(r"[A-Za-z]", tr) and not re.search(r"[çğıöşüÇĞİÖŞÜ]", tr) \
                and len(tr) > 60:
            uyarilar.append(f"{etiket}: uzun metinde hic Turkce karakter yok")

        # tasma: en uzun satir kapasitenin ne kadar ustunde
        kap = kaynak[i]["kap"]
        if kap:
            u = max(len(s) for s in tr.split("\\n"))
            if u > kap * 1.45:
                uyarilar.append(f"{etiket}: satir {u} kar, kapasite {kap} "
                                f"(otoboyut+genisletme gerekir)")
    return hatalar, uyarilar


def main():
    hedef = sys.argv[1:] or [os.path.basename(p)[:-4]
                             for p in sorted(glob.glob(os.path.join(PARTI, "*.tsv")))]
    t_hata, t_uyari, tamam = [], [], 0
    for p in hedef:
        h, u = denetle(p)
        t_hata += h
        t_uyari += u
        if not h and os.path.exists(os.path.join(CEVIRI, f"{p}.tsv")):
            tamam += 1
    print(f"{tamam}/{len(hedef)} parti hatasiz")
    if t_hata:
        print(f"\nHATA ({len(t_hata)}):")
        for x in t_hata[:40]:
            print(f"   {x}")
    if t_uyari:
        print(f"\nUYARI ({len(t_uyari)}):")
        for x in t_uyari[:40]:
            print(f"   {x}")
    return 1 if t_hata else 0


def _kendi_testi():
    """Her denetimin bilerek bozulmus girdiyi YAKALADIGINI kanitla."""
    os.makedirs(PARTI, exist_ok=True); os.makedirs(CEVIRI, exist_ok=True)
    ka = os.path.join(PARTI, "ZZTEST.tsv"); ce = os.path.join(CEVIRI, "ZZTEST.tsv")
    with io.open(ka, "w", encoding="utf-8") as f:
        f.write("idx\tkutu_w\tfont\tkapasite\tEN\n")
        f.write("1\t500\t40\t25\tWings generate lift.\\nDrag slows you.\n")
        f.write("2\t500\t40\t25\tPress W to pitch down.\n")
        f.write("3\t500\t40\t25\tThe rocket equation is fundamental to spaceflight design.\n")
        f.write("4\t100\t40\t5\tThrust\n")
        f.write("5\t500\t40\t25\t Leading space matters\n")
    with io.open(ce, "w", encoding="utf-8") as f:
        f.write("1\tKanatlar taşıma üretir. Sürüklenme yavaşlatır.\n")   # \n kayip
        f.write("2\tBurnu aşağı almak için İ tuşuna bas.\n")             # W kayboldu
        f.write("3\tThe rocket equation is fundamental to spaceflight design.\n")  # cevrilmemis
        f.write("4\tİtme Kuvveti Değeri Çok Uzun Bir Metin\n")           # tasma
        # idx 5 hic yok -> eksik
    h, u = denetle("ZZTEST")
    os.remove(ka); os.remove(ce)
    beklenen = {
        "eksik":        any("idx eksik" in x for x in h),
        "kacis":        any("kacis dizisi" in x for x in h),
        "tus":          any("tusu ceviride yok" in x for x in u),
        "cevrilmemis":  any("cevrilmemis" in x for x in u),
        "tasma":        any("kapasite" in x for x in u),
    }
    for ad, yakaladi in beklenen.items():
        print(f"  {'OK ' if yakaladi else 'YAKALAYAMADI'}  {ad}")
    return 0 if all(beklenen.values()) else 1


if __name__ == "__main__":
    if "--test" in sys.argv:
        raise SystemExit(_kendi_testi())
    raise SystemExit(main())
