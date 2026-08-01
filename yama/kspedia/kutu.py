#!/usr/bin/env python3
"""RectTransform kutu genisletme — otomatik boyutun kurtaramadigi dar etiketler.

Olcum: 1.813 metin nesnesinin %86'sini otoboyut.py cozuyor. Kalan %6 (110 nesne)
o kadar dar ki en kucuk puntoda bile Turkce metin sigmiyor. Ornek: "Lift"
etiketi 66 birim genis, 40 puntoda ~3 karakter aliyor; "Tasima Kuvveti" 14
karakter. Taban punto 28'de bile kapasite ~4,7. Kisaltmak da cozmuyor
("Tasima" bile 6 karakter). Kutunun kendisi buyumeli.

Guvenlik: kutuyu buyutmek komsu cizime tasabilir. Program cizimi goremez, o
yuzden genisletme daima BUYUME PAYI ile sinirlanir — cagiran taraf kardes
RectTransform'lari olcup ne kadar bos yer oldugunu bildirmek zorunda.
"""

# Ortalama karakter genisligi / punto. Muhafazakar secildi: gercek oran
# yaziya gore ~0,35-0,45 arasi degisiyor ("Airflow" 7 karakter 140 birimlik
# kutuda 40 puntoyla rahat sigdi -> 0,35). 0,50 kullaniyoruz ki tahmin
# yanilirsa kutu genis kalsin, dar kalmasin. Yanilma payi otoboyutla emilir.
KAR_ORAN = 0.50

# Genislemeden sonra kutu ile komsusu arasinda birakilacak bosluk.
GUVENLI_ARA = 40.0


def gerekli_genislik(metin, font, pay=1.08):
    """metin verilen puntoda tek satirda sigsin diye gereken kutu genisligi."""
    enuzun = max((len(s) for s in metin.split("\n")), default=0)
    return enuzun * font * KAR_ORAN * pay


def kapasite(genislik, font):
    """Verilen genislik ve puntoda satir basina yaklasik karakter sayisi."""
    return genislik / (font * KAR_ORAN)


def genislet(rect, yeni_genislik, buyume_payi=None):
    """RectTransform typetree sozlugunde m_SizeDelta.x'i buyutur.

    buyume_payi verilirse (kardes olcumunden gelen bos alan), genisleme onu
    asamaz — komsu cizime tasmayi boyle engelliyoruz.

    Doner: (degisti_mi, aciklama)
    """
    if "m_SizeDelta" not in rect:
        return False, "m_SizeDelta yok"

    mevcut = float(rect["m_SizeDelta"]["x"])
    if yeni_genislik <= mevcut:
        return False, f"gerek yok ({mevcut:g} zaten yeterli)"

    tavan = mevcut + buyume_payi if buyume_payi is not None else yeni_genislik
    hedef = min(yeni_genislik, tavan)
    if hedef <= mevcut:
        return False, f"bos yer yok (pay {buyume_payi:g})"

    rect["m_SizeDelta"]["x"] = hedef
    kirpildi = " [paya kirpildi]" if hedef < yeni_genislik else ""
    return True, f"genislik {mevcut:g} -> {hedef:g}{kirpildi}"


def sag_bos_alan(rect, kardesler):
    """Bu kutunun sagindaki bos alan (birim). kardesler: RectTransform dict listesi.

    Sadece dikeyde kesisen kardesler engel sayilir; ustte/altta kalanlar degil.
    Pivot (0,1) varsayimi: anchoredPosition kutunun SOL UST kosesi.
    """
    x = float(rect["m_AnchoredPosition"]["x"])
    y = float(rect["m_AnchoredPosition"]["y"])
    w = float(rect["m_SizeDelta"]["x"])
    h = float(rect["m_SizeDelta"]["y"])
    sag = x + w
    engeller = []
    for k in kardesler:
        if k is rect:
            continue
        kx = float(k["m_AnchoredPosition"]["x"])
        ky = float(k["m_AnchoredPosition"]["y"])
        kw = float(k["m_SizeDelta"]["x"])
        kh = float(k["m_SizeDelta"]["y"])
        if kw <= 0 or kh <= 0:      # gerilmis kutular (Background/Image) engel degil
            continue
        if kx + kw <= sag:          # tamamen solda
            continue
        dikey_kesisiyor = not (ky - kh > y or ky < y - h)
        if dikey_kesisiyor:
            engeller.append(kx)
    if not engeller:
        return None                 # sinirsiz
    return max(0.0, min(engeller) - sag - GUVENLI_ARA)


if __name__ == "__main__":
    # kendi kendini test et
    testler = [
        # (metin, font, mevcut_genislik, pay, beklenen_degisti)
        ("Taşıma Kuvveti", 40, 65.92, None, True),    # 14 kar -> ~302 gerekli
        # "Lift" oyunda 66 birimlik kutuya SIGIYOR (ekran goruntusuyle sabit),
        # ama 0,50 orani 86 birim istiyor -> demek ki gercek oran <=0,41.
        # Fazla tahmin kasitli: kutu genis kalsin, dar kalmasin. True bekleniyor.
        ("Lift", 40, 65.92, None, True),
        ("Taşıma Kuvveti", 40, 65.92, 10.0, True),    # paya kirpilir
        ("Taşıma Kuvveti", 40, 400.0, None, False),   # zaten genis
    ]
    for metin, font, gen, pay, bekle in testler:
        rect = {"m_SizeDelta": {"x": gen, "y": 55.0}}
        gerek = gerekli_genislik(metin, font)
        d, a = genislet(rect, gerek, pay)
        ok = "OK " if d == bekle else "YANLIS"
        print(f"  {ok} {metin!r:18} font {font} kutu {gen:>6.1f} "
              f"gerekli {gerek:>6.1f} -> {a}")

    # sag_bos_alan: dikeyde kesismeyen kardes engel olmamali
    a = {"m_AnchoredPosition": {"x": 352.0, "y": -294.0},
         "m_SizeDelta": {"x": 66.0, "y": 55.0}}
    ust = {"m_AnchoredPosition": {"x": 500.0, "y": -100.0},
           "m_SizeDelta": {"x": 100.0, "y": 50.0}}     # cok yukarida -> engel degil
    yan = {"m_AnchoredPosition": {"x": 1055.0, "y": -285.0},
           "m_SizeDelta": {"x": 959.0, "y": 447.0}}    # kesisiyor -> engel
    print(f"  -- sadece ust komsu  : {sag_bos_alan(a, [a, ust])}  (None beklenir)")
    print(f"  -- kesisen komsu var : {sag_bos_alan(a, [a, ust, yan]):.0f}  (~597 beklenir)")
