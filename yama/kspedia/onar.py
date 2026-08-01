#!/usr/bin/env python3
"""Ajan ciktilarindaki 'gercek satir sonu' hatasini onarir.

Ajanlardan `\\n` KACIS DIZISI yazmalari istendi (iki karakter: ters bolu + n).
Bir kismi bunun yerine GERCEK satir sonu yazdi; dosya 41 satir yerine 72 satir
oldu. Bu, uyarilan tuzagin aynisi.

Onarim deterministik: her veri satiri `<sayi><TAB>` ile baslamak ZORUNDA, o
yuzden oyle baslamayan her satir bir oncekinin devamidir ve araya `\\n` girer.

Guvenlik: onarim ancak KAYNAKLA dogrulanirsa yazilir. Onarilmis metindeki
kacis dizileri kaynaktakiyle birebir tutmuyorsa dosyaya dokunulmaz — yanlis
tahminle bozmaktansa hatali birakip ajana geri gondermek yeglenir.
"""
import glob
import io
import os
import re
import sys

from dogrula_kspedia import oku_kaynak, KACIS, PARTI, CEVIRI

BASLIK = re.compile(r"^(\d+)\t")
# metnin sonundaki satir-sonu kacislari (bir ya da daha fazla)
SON_KACIS = re.compile(r"(?:\\r|\\n)+$")


def _kacis_coklugu(s):
    """Kacis dizilerinin siralanmis listesi; \r sayilmaz (dogrula ile ayni olcut)."""
    return sorted(x for x in KACIS.findall(s) if x != "\\r")


def birlestir(ham):
    """Satirlari yeniden birlestirip {idx: metin} dondurur."""
    kayitlar, mevcut = [], None
    for satir in ham.split("\n"):
        m = BASLIK.match(satir)
        if m:
            if mevcut:
                kayitlar.append(mevcut)
            mevcut = [int(m.group(1)), satir[m.end():]]
        elif mevcut is not None:
            # onceki kaydin devami — arada gercek satir sonu vardi
            mevcut[1] += "\\n" + satir
    if mevcut:
        kayitlar.append(mevcut)
    return {i: t for i, t in kayitlar}


def onar(parti_adi, yaz=True):
    yol = os.path.join(CEVIRI, f"{parti_adi}.tsv")
    if not os.path.exists(yol):
        return "cikti yok", 0
    kaynak = oku_kaynak(parti_adi)
    # binary oku: yalin CR satir sonu SAYILMAZ, sadece LF boler
    ham = open(yol, "rb").read().decode("utf-8")
    if ham.endswith("\n"):
        ham = ham[:-1]

    kayitlar = birlestir(ham)

    # sondaki bos parcalar: "abc\\n" seklinde biten metinlerde son satir bos
    # kalabilir; kaynakta oyle bitmiyorsa temizle
    for i, t in list(kayitlar.items()):
        if i in kaynak and t.endswith("\\n") and not kaynak[i]["en"].endswith("\\n"):
            kayitlar[i] = t[:-2]

    eksik = set(kaynak) - set(kayitlar)
    if eksik:
        return f"onarilamadi: {len(eksik)} idx hala eksik", 0

    # 2. kural: SONDAKI satir sonu dusurulmus. Kaynak "...\\r\\n" ile bitip
    # ceviri bitmiyorsa, farkin tamami o son kacistan ibaretse geri ekle.
    # (Ajanlar bunu siklikla atliyor; satir sayisi tuttugu icin 1. kural
    #  yakalamiyor.)
    for i, t in list(kayitlar.items()):
        if i not in kaynak:
            continue
        en = kaynak[i]["en"]
        m = SON_KACIS.search(en)
        if not m:
            continue
        # cevirinin sonundaki satir sonlarini at, kaynagin sonunu aynen tak.
        # Kaynakta sonda birden fazla bos satir olabiliyor ("...\\r\\n\\r\\n"),
        # o yuzden tek bir sonu denemek yetmiyor.
        aday = SON_KACIS.sub("", t) + m.group(0)
        if _kacis_coklugu(en) == _kacis_coklugu(aday):
            kayitlar[i] = aday

    uyusmayan = [i for i in kaynak
                 if _kacis_coklugu(kaynak[i]["en"]) != _kacis_coklugu(kayitlar[i])]
    if uyusmayan:
        return (f"onarilamadi: {len(uyusmayan)} satirda kacis dizisi hala "
                f"tutmuyor {uyusmayan[:5]}"), 0

    if yaz:
        with io.open(yol, "w", encoding="utf-8") as f:
            for i in sorted(kayitlar):
                f.write(f"{i}\t{kayitlar[i]}\n")
    return "onarildi", len(kayitlar)


def main():
    yaz = "--kuru" not in sys.argv
    hedef = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not hedef:
        hedef = sorted(os.path.basename(p)[:-4]
                       for p in glob.glob(os.path.join(CEVIRI, "P*.tsv")))
    import dogrula_kspedia as dg
    for p in hedef:
        # Saglamlik olcutu SATIR SAYISI DEGIL kacis esitligi. Satir sayisina
        # bakmak sadece 1. kuralin (gercek satir sonu) hasarini gorur; sondaki
        # satir sonunu dusuren dosya satir sayisini korudugu icin "saglam"
        # sanilip onarilmadan geciyordu.
        if not os.path.exists(os.path.join(CEVIRI, f"{p}.tsv")):
            print(f"   {p}: cikti yok"); continue
        h, _ = dg.denetle(p)
        if not h:
            print(f"   {p}: zaten saglam ({len(oku_kaynak(p))} satir)")
            continue
        sonuc, n = onar(p, yaz)
        print(f"   {p}: {sonuc}" + (f" ({n} satir)" if n else ""))
    return 0


if __name__ == "__main__":
    if "--test" in sys.argv:
        # bilerek bozulmus girdi: gercek satir sonlari
        ham = ("10\tBirinci satir\nikinci satir\n"
               "11\tTek satirlik\n"
               "12\tUc\ndort\nbes")
        k = birlestir(ham)
        bekle = {10: "Birinci satir\\nikinci satir",
                 11: "Tek satirlik",
                 12: "Uc\\ndort\\nbes"}
        ok1 = k == bekle
        print(f"  {'OK ' if ok1 else 'YANLIS'} birlestirme")

        # SON_KACIS gercekten yakaliyor mu? (fazla kacirilmis regex sessizce
        # hicbir seyi yakalamaz — bu tuzaga bir kez dusuldu)
        ok2 = (SON_KACIS.search(r"metin\r\n\r\n") is not None
               and SON_KACIS.search(r"metin\r\n\r\n").group(0) == r"\r\n\r\n"
               and SON_KACIS.search("duz metin") is None)
        print(f"  {'OK ' if ok2 else 'YANLIS'} sondaki satir sonu yakalama")
        raise SystemExit(0 if (ok1 and ok2) else 1)
    raise SystemExit(main())
