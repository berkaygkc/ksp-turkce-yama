#!/usr/bin/env python3
"""Katman 1 - deterministik kalite denetimi (0 token).

dogrula.py mekanik butunlugu denetler (yer tutucu, etiket, glyph).
kalite.py ANLAM/TUTARLILIK tarafina bakar ve model denetimine gidecek
satirlari bayraklar.

Denetimler:
  1. Sozluk uyumu       EN'de 'thrust' var, TR'de 'itki' yok
  2. Tutarlilik         ayni EN string'i farkli cevrilmis
  3. Cevrilmemis        TR == EN (cok kelimeli EN icin)
  4. Ingilizce sizinti  TR icinde the/your/with gibi kalintilar
  5. Sayi butunlugu     EN'deki sayilar TR'de yok
  6. Format kirilmasi   TR icinde TAB (dosya formatini bozar)

Cikti: bayrak.tsv  ->  Katman 2 (model denetimi) sadece bunu okur.
"""
import io
import os
import re
import sys
from collections import Counter, defaultdict

KOK = os.path.dirname(os.path.abspath(__file__))

# TR icinde gorulmemesi gereken yaygin Ingilizce kelimeler
INGILIZCE = {
    "the", "and", "your", "with", "from", "this", "that", "will", "have",
    "which", "when", "where", "there", "these", "those", "been", "were",
    "about", "would", "could", "should", "their", "them", "than", "then",
    "into", "over", "before", "after", "while", "during", "between",
}
# cevrilmemesi normal olan kelimeler (ozel ad / topluluk terimi)
BEYAZ_LISTE = set()

SAYI = re.compile(r"\d+(?:[.,]\d+)?")
# Katman 2 turunda olculdu: bayraklarin ~%98'i yanlis pozitifti. Asagidaki
# filtreler ajanlarin gerekcelerinden turetildi; amac gercek sorunlari
# kaybetmeden gurultuyu kesmek.

# Cok anlamli kisa terimler: sozluk karsiligi baglama gore degisir, denetime
# sokmak yanlis pozitif uretir ("Next Camera" -> "Sonraki Kamera" dogru,
# sozlukteki next->ileri sadece diyalog butonu icindi).
# SADECE ajanlarin olculmus yanlis pozitif gerekcelerinden gelenler.
# "toggle/target/crew" gibi tek anlamli terimler LISTEDE YOK: onlarda sozluk
# denetimi gercek hata yakaladi (Toggle Movement Mode -> "Degistir" yanlisti).
SOZLUK_MUAF = {
    "next", "back", "close", "report", "transfer", "stage", "part", "level",
    "data", "light", "node", "sort", "hold", "track", "advance",
}
# Cevrilmesi beklenmeyen dizeler: birim, teknik kimlik, salt yer tutucu
TEKNIK = re.compile(
    r"^(?:[A-Z][A-Z0-9_]{2,}|[a-zA-Z]{1,3}/[a-zA-Z]{1,3}|"
    r"(?:<[^>]*>|<<[^<>]*>>|\\[a-zA-Z]|\s)+)$")
KELIME = re.compile(r"[A-Za-zÇĞİÖŞÜçğıöşü]+")


def tr_kucult(s):
    """Turkce'ye dogru kucuk harf. Python'un .lower() metodu 'I'->'i' ve
    'İ'->'i̇' (birlesik noktali) yapar; ikisi de Turkce icin yanlistir."""
    return s.replace("İ", "i").replace("I", "ı").lower()


def kok_norm(s):
    """Kok karsilastirmasi icin gevsetilmis bicim.

    Turkce'de ek alinca son unsuz yumusar: araç->aracı, kilit->kilidi,
    kitap->kitabi. Duz alt-dize aramasi bu yuzden yanlis pozitif uretir.
    Yumusayan ciftleri tek bicime indirerek eslesmeyi toleransli yapiyoruz.
    """
    s = tr_kucult(s)
    for a, b in (("ç", "c"), ("ğ", "g"), ("k", "g"), ("p", "b"), ("t", "d")):
        s = s.replace(a, b)
    return s


def sozluk_yukle():
    """(ingilizce, turkce, degismeyecek_mi) listesi."""
    terimler = []
    yol = os.path.join(KOK, "sozluk.tsv")
    degismeyecek_bolum = False
    with io.open(yol, encoding="utf-8") as f:
        for satir in f:
            s = satir.rstrip("\n")
            if s.startswith("#"):
                if "DEĞİŞMEYECEKLER" in s:
                    degismeyecek_bolum = True
                elif s.startswith("# ==="):
                    degismeyecek_bolum = False
                continue
            if "\t" not in s:
                continue
            p = s.split("\t")
            en, tr = p[0].strip(), p[1].strip()
            if not en or not tr:
                continue
            # "Degismeyecekler" BOLUMUNDE olmak yetmez; gercekten ayni mi diye
            # bak. Sozlukte 'biome -> biyom' o bolume yanlislikla yazilmis ve
            # denetim "korunmali" diye yanlis bayrak atiyordu.
            degismez = tr_kucult(en) == tr_kucult(tr)
            terimler.append((en, tr, degismez))
            if en == tr:
                BEYAZ_LISTE.add(en.lower())
    return terimler


def harita_yukle():
    h = {}
    with io.open(os.path.join(KOK, "harita.tsv"), encoding="utf-8") as f:
        next(f)
        for satir in f:
            p = satir.rstrip("\n").split("\t")
            if len(p) >= 5:
                h[p[0]] = {"anahtar": p[1], "oncelik": p[4]}
    return h


def kaynak_yukle(harita):
    """Kaynak metni BOZULMAMIS yedekten okur, parti dosyalarindan degil.

    Parti dosyalari canli sozlukten uretilmisti; pilotta cevrilmis ~112 satir
    orada Ingilizce yerine Turkce duruyor. Ajan onlari aynen kopyalayinca
    TR == EN olup 'CEVRILMEMIS' yanlis pozitifi ureniyordu. Yedekten okuyunca
    karsilastirma gercek Ingilizce metne karsi yapiliyor.
    """
    OYUN = os.path.dirname(KOK)
    YEDEK = os.path.join(OYUN, "_ksp-tr-yedek")
    anahtar_deger = {}
    for ad in ("dictionary.cfg.orijinal", "serenity-dictionary.cfg.orijinal"):
        yol = os.path.join(YEDEK, ad)
        if not os.path.exists(yol):
            continue
        with io.open(yol, encoding="utf-8", newline="") as f:
            for satir in f:
                m = re.match(r"^\s*#([A-Za-z0-9_]+)\s*=\s*(.*?)\r?\n?$", satir)
                if m:
                    anahtar_deger[m.group(1)] = m.group(2)

    # hangi idx hangi parti dosyasinda -> raporda yer gostermek icin
    idx_dosya = {}
    d = os.path.join(KOK, "partiler/kaynak")
    for ad in sorted(os.listdir(d)):
        if not ad.endswith(".tsv"):
            continue
        with io.open(os.path.join(d, ad), encoding="utf-8") as f:
            for satir in f:
                p = satir.rstrip("\n").split("\t")
                if len(p) >= 2:
                    idx_dosya[p[0]] = ad

    k = {}
    for i, bilgi in harita.items():
        deger = anahtar_deger.get(bilgi["anahtar"])
        if deger is not None:
            k[i] = (deger, idx_dosya.get(i, "?"))
    return k


def ceviri_yukle():
    c = {}
    d = os.path.join(KOK, "partiler/ceviri")
    if not os.path.isdir(d):
        return c
    for ad in sorted(os.listdir(d)):
        if not ad.endswith(".tsv"):
            continue
        with io.open(os.path.join(d, ad), encoding="utf-8") as f:
            for no, satir in enumerate(f, 1):
                p = satir.rstrip("\n").split("\t")
                if len(p) >= 2 and p[1].strip():
                    c[p[0]] = (p[1], ad, no)
    return c


def main():
    terimler = sozluk_yukle()
    harita = harita_yukle()
    kaynak = kaynak_yukle(harita)
    ceviri = ceviri_yukle()
    if not ceviri:
        print("henuz ceviri yok"); return 0

    bayraklar = []          # (idx, tur, aciklama)
    sayac = Counter()

    # --- 2. tutarlilik: ayni EN -> farkli TR
    en_to_tr = defaultdict(set)
    for i, (tr, _, _) in ceviri.items():
        if i in kaynak:
            en_to_tr[kaynak[i][0]].add(tr)
    tutarsiz = {en: trs for en, trs in en_to_tr.items()
                if len(trs) > 1 and len(KELIME.findall(en)) >= 2}

    for i, (tr, dosya, no) in sorted(ceviri.items(), key=lambda x: int(x[0])):
        if i not in kaynak:
            continue
        en = kaynak[i][0]
        yer = f"{dosya}:{no}"

        # 6. format
        if "\t" in tr:
            bayraklar.append((i, "FORMAT", f"{yer} TR icinde TAB var"))
            sayac["FORMAT"] += 1

        # 3. cevrilmemis
        # Ozel ad iceren satirlar (Jebediah Kerman, Mystery Goo...) zaten
        # cevrilmemeli; EN'in herhangi bir kelimesi beyaz listedeyse atla.
        en_kelimeler = {tr_kucult(w) for w in KELIME.findall(en)}
        if tr == en and len(KELIME.findall(en)) > 1 \
                and tr_kucult(en) not in BEYAZ_LISTE \
                and not (en_kelimeler & BEYAZ_LISTE) \
                and not TEKNIK.match(en.strip()):
            bayraklar.append((i, "CEVRILMEMIS", f"{yer} | {en[:60]}"))
            sayac["CEVRILMEMIS"] += 1

        # 4. ingilizce sizinti
        kelimeler = {tr_kucult(w) for w in KELIME.findall(tr)}
        sizinti = kelimeler & INGILIZCE
        if sizinti:
            bayraklar.append((i, "SIZINTI",
                              f"{yer} {sorted(sizinti)} | {tr[:50]}"))
            sayac["SIZINTI"] += 1

        # 5. sayi butunlugu
        sa, sb = Counter(SAYI.findall(en)), Counter(SAYI.findall(tr))
        if sa != sb:
            bayraklar.append((i, "SAYI",
                              f"{yer} {sorted(sa.elements())} -> "
                              f"{sorted(sb.elements())}"))
            sayac["SAYI"] += 1

        # 1. sozluk uyumu
        en_low = " " + tr_kucult(en) + " "
        for e, t, degismez in terimler:
            if len(e) < 5 or tr_kucult(e) in SOZLUK_MUAF:
                continue
            el = tr_kucult(e)
            if f" {el} " not in en_low and f" {el}s " not in en_low:
                continue
            if degismez:
                # aynen korunmali
                if tr_kucult(e) not in tr_kucult(tr):
                    bayraklar.append((i, "SOZLUK",
                                      f"{yer} '{e}' korunmali | {tr[:50]}"))
                    sayac["SOZLUK"] += 1
            else:
                tn = kok_norm(t)
                kok = tn[:max(4, len(tn) - 3)]
                if kok not in kok_norm(tr):
                    bayraklar.append((i, "SOZLUK",
                                      f"{yer} '{e}'->'{t}' bekleniyordu | "
                                      f"{tr[:50]}"))
                    sayac["SOZLUK"] += 1
            break   # satir basina tek sozluk bayragi yeter

        # 2. tutarlilik
        if en in tutarsiz:
            bayraklar.append((i, "TUTARSIZ",
                              f"{yer} '{en[:35]}' -> {sorted(tutarsiz[en])}"))
            sayac["TUTARSIZ"] += 1

    with io.open(os.path.join(KOK, "bayrak.tsv"), "w", encoding="utf-8") as f:
        f.write("idx\ttur\taciklama\n")
        for i, tur, acik in bayraklar:
            f.write(f"{i}\t{tur}\t{acik}\n")

    print(f"denetlenen satir : {len(ceviri):,}")
    print(f"bayraklanan      : {len(bayraklar):,} "
          f"(%{100*len(bayraklar)/max(len(ceviri),1):.1f})")
    for tur, n in sayac.most_common():
        print(f"   {tur:<14}{n:>6}")
    if bayraklar:
        print(f"\nornekler:")
        for i, tur, acik in bayraklar[:15]:
            print(f"   [{tur}] {acik}")
        print(f"\n-> bayrak.tsv yazildi (Katman 2 sadece bunlari okuyacak)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
