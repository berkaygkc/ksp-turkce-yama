#!/usr/bin/env python3
"""Ceviri partilerini denetler. Hata varsa uygula.py calistirilmamali.

Denetimler:
  1. <<n>> yer tutucularinin kumesi birebir ayni mi
  2. Zengin metin etiketleri (<color>, <b>, <i>, <sprite>) dengeli ve ayni sayida mi
  3. \n satir sonu sayisi ayni mi
  4. Ana menu anahtarlarinda yasakli glyph (Ç Ğ ğ İ Ş ş) var mi
  5. Bos / cevrilmemis satir var mi
  6. Asiri uzama (tasma riski) - uyari
"""
import io
import os
import re
import sys
from collections import Counter

KOK = os.path.dirname(os.path.abspath(__file__))
YASAKLI_GLYPH = set("ÇĞğİŞş")
# Kucuk c-cedilla ve i ana menu fontunda MEVCUT (ekran goruntusuyle dogrulandi:
# "Eklentiler ve Modlar" nokta-matris fontta sorunsuz render oldu).
# Risk sadece UI'nin BUYUK HARFE cevirdigi metinlerde: i->Ist, ç->Ç eksik harfe doner.
# Simdilik yalnizca Cikis butonunun buyultuldugu kanitlandi.
YASAKLI_BUYUK = set("çi")
BUYUK_ANAHTARLAR = {"autoLOC_1900252"}

# KSP'nin yer tutucu dilbilgisi sadece <<1>> degil: <<n:1>> (sayi uyumu),
# <<g:2,1>> (cinsiyet), <<P:1>>, <<1^n>>, <<1[Auto/Override]>> gibi bicimler de
# var. Dar bir regex bunlarin 143 tanesini denetim disinda birakiyordu.
PH = re.compile(r"<<[^<>]*?>>")
TAGLIKE = re.compile(r"<\s*/?[a-zA-Z]")
# KSP arama etiketi sozdizimi: token basindaki "(" bir isarettir
# ("(poodle", "(air", "(elev"). Cevirmen kelimeyi cevirirken parantezi
# dusurunce oyun ici arama bozulur. Kaynakta 618 gecisi var.
TAG_PAREN = re.compile(r"(?:^|\s)\(")
# Kontrol SADECE gercek etiket satirlarina uygulanir. Duz metinde Turkce
# cevirmen mesru olarak parantez ekleyebilir/bosluk koyabilir
# ("<<1>>(<<2>>)" -> "<<1>> (<<2>>)"), bu hata degildir.
# Etiket satiri: bastan sona kucuk harf, cumle noktalamasi yok, 3+ token.
TAG_SATIRI = re.compile(r"^[a-z0-9()?\-_/,& ]+$")


def tag_satiri_mi(en):
    return (TAG_SATIRI.match(en) is not None
            and len(en.split()) >= 3
            and "(" in en)
PH_SECENEK = re.compile(r"^<<([^\[\]]*)\[(.*)\]>>$", re.S)


def ph_norm(p):
    """Yer tutucuyu YAPISINA indirger; secenek metnini disarida birakir.

    <<1[On/Off]>>  -> <<1[#2]>>      (indeks 1, iki secenek)
    <<n:1[a/b/c]>> -> <<n:1[#3]>>
    <<g:2,1>>      -> <<g:2,1>>      (secenek yok, aynen)

    Boylece secenek metninin cevrilmesi hata sayilmaz, ama indeks/degistirici
    degisirse veya secenek SAYISI tutmazsa (oyun bozulur) yakalanir.
    """
    m = PH_SECENEK.match(p)
    if not m:
        return p
    bas, ic = m.groups()
    return f"<<{bas}[#{ic.count('/') + 1}]>>"
ETIKET = re.compile(r"</?(color|b|i|size|sprite|align|indent|u|s)\b[^>]*>", re.I)
# Sozlukte \n disinda \u0020 gibi literal kacis dizileri de var;
# hepsinin sayisi birebir korunmali.
KACIS = re.compile(r"\\u[0-9a-fA-F]{4}|\\[a-zA-Z]")


def harita_yukle():
    h = {}
    yol = os.path.join(KOK, "harita.tsv")
    with io.open(yol, encoding="utf-8") as f:
        next(f)
        for satir in f:
            p = satir.rstrip("\n").split("\t")
            if len(p) >= 5:
                h[p[0]] = {"anahtar": p[1], "dosya": p[2],
                           "bayrak": p[3], "oncelik": p[4]}
    return h


def kaynak_yukle():
    k = {}
    d = os.path.join(KOK, "partiler/kaynak")
    for ad in sorted(os.listdir(d)):
        if not ad.endswith(".tsv"):
            continue
        with io.open(os.path.join(d, ad), encoding="utf-8") as f:
            for satir in f:
                if "\t" not in satir:
                    continue
                i, v = satir.rstrip("\n").split("\t", 1)
                k[i] = v
    return k


def denetle(idx, en, tr, bayrak, anahtar):
    hatalar = []

    if not tr.strip():
        hatalar.append("bos ceviri")
        return hatalar

    # 1. yer tutucular — YAPI karsilastirilir, secenek METNI degil.
    #    <<1[On/Off]>> bicimindeki koseli parantez icerigi kullaniciya gosterilen
    #    metindir ve CEVRILMELIDIR ("<<2[N/S]>>" -> "<<2[K/G]>>"). Denetim indeks,
    #    degistirici ve secenek SAYISI uzerinden yapilir.
    a, b = Counter(map(ph_norm, PH.findall(en))), \
           Counter(map(ph_norm, PH.findall(tr)))
    if a != b:
        eksik = list((a - b).elements()) or "-"
        fazla = list((b - a).elements()) or "-"
        hatalar.append(f"yer tutucu uyusmuyor (eksik={eksik} fazla={fazla})")

    # 2. zengin metin etiketleri
    ea, eb = Counter(x.lower() for x in ETIKET.findall(en)), \
             Counter(x.lower() for x in ETIKET.findall(tr))
    if ea != eb:
        hatalar.append(f"etiket sayisi uyusmuyor ({dict(ea)} -> {dict(eb)})")
    # Duz "<" / ">" sayimi YAPMA: metinde "->", ">>", "Sol<->Sag" gibi mesru
    # oklar var ve sayim onlari hatali sanip ajanlarin metni gereksiz
    # degistirmesine yol aciyor. Sadece bozuk ETIKET ara: yer tutucular ve
    # taninan etiketler cikarildiktan sonra kalan "<harf" bir tag kalintisidir.
    # Kaynakta da bulunan mesru "<something>" gibi ifadeleri suclamamak icin
    # TR'yi tek basina degil, EN ile KARSILASTIRARAK denetle.
    kalan_tr = ETIKET.sub("", PH.sub("", tr))
    kalan_en = ETIKET.sub("", PH.sub("", en))
    if len(TAGLIKE.findall(kalan_tr)) != len(TAGLIKE.findall(kalan_en)):
        hatalar.append("taninmayan/bozuk etiket")

    # 2b. KSP etiket sozdizimi: token basi '(' korunmali
    if tag_satiri_mi(en) and \
            len(TAG_PAREN.findall(en)) != len(TAG_PAREN.findall(tr)):
        hatalar.append(
            f"token basi '(' sayisi uyusmuyor "
            f"({len(TAG_PAREN.findall(en))} -> {len(TAG_PAREN.findall(tr))})")

    # 3. kacis dizileri (\n, \u0020, \t ...)
    ka, kb = Counter(KACIS.findall(en)), Counter(KACIS.findall(tr))
    if ka != kb:
        hatalar.append(f"kacis dizisi uyusmuyor ({dict(ka)} -> {dict(kb)})")

    # 4. ana menu glyph kisiti
    if bayrak == "ANAMENU":
        kotu = set(tr) & YASAKLI_GLYPH
        if anahtar in BUYUK_ANAHTARLAR:      # UI bu metni buyultuyor
            kotu |= set(tr) & YASAKLI_BUYUK
        if kotu:
            hatalar.append(f"ana menu fontunda olmayan harf: {sorted(kotu)}")

    return hatalar


def main():
    # --faz=P1 gibi bir filtre verilirse sadece o fazin partileri denetlenir.
    # Paralel calisan baska fazlarin yarim isi, biten fazin yazilmasini
    # engellemesin diye.
    faz = None
    for a in sys.argv[1:]:
        if a.startswith("--faz="):
            faz = a.split("=", 1)[1]

    def kapsamda(ad):
        return (not faz) or ad.startswith(faz + "-")

    harita = harita_yukle()
    kaynak = kaynak_yukle()
    d = os.path.join(KOK, "partiler/ceviri")
    if not os.path.isdir(d):
        print("ceviri klasoru yok"); return 1

    toplam = hatali = uyari = 0
    hata_listesi, uyari_listesi = [], []

    # 0. EKSIKSIZLIK: bir parti cevrildiyse kaynaktaki TUM idx'ler bulunmali.
    #    (ajanlar satir dusurebiliyor ve kendi bildirdikleri sayi guvenilmez)
    kd = os.path.join(KOK, "partiler/kaynak")
    for ad in sorted(os.listdir(d)):
        if not ad.endswith(".tsv") or not kapsamda(ad):
            continue
        kyol = os.path.join(kd, ad)
        if not os.path.exists(kyol):
            hata_listesi.append(f"{ad} kaynak dosyasi yok")
            hatali += 1
            continue
        k_idx = {s.split("\t")[0] for s in io.open(kyol, encoding="utf-8")
                 if "\t" in s}
        c_idx = {s.split("\t")[0] for s in io.open(os.path.join(d, ad),
                                                   encoding="utf-8")
                 if "\t" in s}
        eksik, uydurma = k_idx - c_idx, c_idx - k_idx
        if eksik:
            hatali += 1
            ornek = sorted(eksik, key=int)[:12]
            hata_listesi.append(
                f"{ad} EKSIK {len(eksik)} satir -> idx {ornek}"
                f"{' ...' if len(eksik) > 12 else ''}")
        if uydurma:
            hatali += 1
            hata_listesi.append(
                f"{ad} UYDURMA {len(uydurma)} satir -> "
                f"idx {sorted(uydurma, key=int)[:12]}")

    for ad in sorted(os.listdir(d)):
        if not ad.endswith(".tsv") or not kapsamda(ad):
            continue
        with io.open(os.path.join(d, ad), encoding="utf-8") as f:
            for no, satir in enumerate(f, 1):
                if "\t" not in satir:
                    continue
                i, tr = satir.rstrip("\n").split("\t", 1)
                if i not in kaynak:
                    hata_listesi.append(f"{ad}:{no} idx {i} kaynakta yok")
                    hatali += 1
                    continue
                toplam += 1
                en = kaynak[i]
                bayrak = harita.get(i, {}).get("bayrak", "-")
                anahtar = harita.get(i, {}).get("anahtar", "")
                h = denetle(i, en, tr, bayrak, anahtar)
                if h:
                    hatali += 1
                    for x in h:
                        hata_listesi.append(f"{ad}:{no} [{i}] {x}")
                # tasma uyarisi
                if len(en) <= 25 and len(tr) > len(en) * 1.8 + 4:
                    uyari += 1
                    uyari_listesi.append(
                        f"{ad}:{no} [{i}] uzama {len(en)}->{len(tr)} "
                        f"| {en[:30]} -> {tr[:30]}")

    for x in hata_listesi[:60]:
        print("HATA  " + x)
    if len(hata_listesi) > 60:
        print(f"      ... +{len(hata_listesi)-60} hata daha")
    for x in uyari_listesi[:20]:
        print("uyari " + x)
    if len(uyari_listesi) > 20:
        print(f"      ... +{len(uyari_listesi)-20} uyari daha")

    print(f"\ndenetlenen {toplam}, hatali {hatali}, tasma uyarisi {uyari}")
    if hatali:
        print("!! Hata var - uygula.py CALISTIRMA.")
        return 1
    print("OK - uygula.py calistirilabilir.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
