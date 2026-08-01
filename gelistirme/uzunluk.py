#!/usr/bin/env python3
"""KSPedia uzunluk butcesi denetimi.

Pilot gosterdi ki KSPedia'da asil kisit font degil UZUNLUK: sayfa duzenleri
sabit, kutular dar. "Lift" (4 karakter) icin tasarlanmis bir ok etiketine
"Tasima Kuvveti" (14) yazilinca metin harf harf alt alta diziliyor.

Kural: cevirinin HER SATIRI, kaynagin EN UZUN satirindan uzun olamaz; ayrica
satir SAYISI artamaz. Cok dar kutularda (<=10 kar) daha siki davraniriz.
"""


def satir_olcu(t):
    satirlar = t.split("\n")
    return len(satirlar), max((len(s) for s in satirlar), default=0)


def butce(en):
    """Kaynak metne gore izin verilen (satir_sayisi, maks_satir_uzunlugu)."""
    n, u = satir_olcu(en)
    if u <= 10:
        # Cok dar etiket. Pay +3: "Airflow"(7) -> "Hava Akisi"(10) oyunda
        # sorunsuz render oldu (ekran goruntusuyle dogrulandi), ama
        # "Lift"(4) -> "Tasima Kuvveti"(14) harf harf alt alta dizildi.
        return n, u + 3
    if u <= 20:
        return n, int(u * 1.15)
    # Genis kutular: kaynagin en uzun satirini asma
    return n, u


def denetle(en, tr):
    """Sorun listesi dondurur; bos liste = temiz."""
    hn, hu = butce(en)
    n, u = satir_olcu(tr)
    sorun = []
    if n > hn:
        sorun.append(f"satir sayisi {hn} -> {n}")
    if u > hu:
        uzun = max(tr.split("\n"), key=len)
        sorun.append(f"en uzun satir {u} > butce {hu}: {uzun[:46]!r}")
    return sorun


if __name__ == "__main__":
    # kendi kendini test et: dogru kabul edilmesi/reddedilmesi gerekenler
    t = [
        ("Lift", "Taşıma Kuvveti", False),      # 4 -> 14, reddedilmeli
        ("Lift", "Taşıma", True),               # 4 -> 6, kabul (pay 2)
        ("Airflow", "Hava Akışı", True),        # 7 -> 10, oyunda sorunsuz render oldu
        ("Getting a Lift Up", "Havalanmak", True),
        ("bir\niki", "bir\niki\nuc", False),    # satir sayisi artti
    ]
    for en, tr, temiz_olmali in t:
        s = denetle(en, tr)
        ok = (not s) == temiz_olmali
        print(f"  {'OK ' if ok else 'YANLIS'}  {en[:18]!r:22}-> {tr[:18]!r:22} {s or 'temiz'}")
