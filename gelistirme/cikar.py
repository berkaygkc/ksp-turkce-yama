#!/usr/bin/env python3
"""KSP sozlugunu oncelikli parti dosyalarina cikarir.

Cikti:
  harita.tsv              idx <TAB> anahtar <TAB> dosya <TAB> bayrak
  partiler/kaynak/*.tsv   idx <TAB> ingilizce      (okunacak)
  partiler/ceviri/*.tsv   idx <TAB> turkce         (yazilacak - bos olusturulmaz)

Anahtar adi yerine kisa idx kullaniliyor: ~170k token tasarruf.
"""
import io
import os
import re
import sys

KOK = os.path.dirname(os.path.abspath(__file__))
OYUN = os.path.dirname(KOK)
GD = os.path.join(OYUN, "GameData")

# KRITIK: kaynak metin DAIMA bozulmamis yedekten okunur, canli sozlukten DEGIL.
# Canli sozlukten okunursa, ceviri uygulandiktan sonraki her yeniden cikarma
# "ingilizce kaynak" yerine kendi turkce ciktimizi okur ve asil metin kaybolur.
YEDEK = os.path.join(OYUN, "_ksp-tr-yedek")
SOZLUKLER = [
    ("squad",    os.path.join(YEDEK, "dictionary.cfg.orijinal")),
    ("serenity", os.path.join(YEDEK, "serenity-dictionary.cfg.orijinal")),
]
for _e, _y in SOZLUKLER:
    if not os.path.exists(_y):
        raise SystemExit(f"Bozulmamis yedek yok: {_y}\n"
                         f"Once orijinal dictionary.cfg dosyalarini "
                         f"{YEDEK} altina kopyala.")

# Ana menu fontunda Ç Ğ ğ İ Ş ş YOK -> bu anahtarlar kisitli
ANA_MENU = {f"autoLOC_{n}" for n in range(1900240, 1900257)} | {
    "autoLOC_8003364", "autoLOC_8003366"}

PARTI_KARAKTER = 4000   # parti basina ingilizce karakter butcesi
PARTI_SATIR    = 110    # parti basina satir tavani (ajan satir dusurmesin)


def cfg_referanslari():
    """Hangi anahtar hangi cfg ailesinden referanslaniyor."""
    ref = {}
    for kok, _, dosyalar in os.walk(GD):
        for f in dosyalar:
            if not f.endswith(".cfg"):
                continue
            yol = os.path.join(kok, f)
            if "Localization" in yol:
                continue
            try:
                s = io.open(yol, encoding="utf-8", errors="ignore").read()
            except OSError:
                continue
            low = yol.lower()
            if "/parts/" in low or "zdeprecated" in low:
                kat = "parca"
            elif "/resources" in low:
                kat = "kaynak"
            else:
                kat = "diger"
            for m in re.findall(r"=\s*#(autoLOC_[0-9]+)", s):
                ref.setdefault(m, set()).add(kat)
    return ref


def oncelik(anahtar, deger, ref):
    """P1 = kisa arayuz etiketi, P2 = parca/kaynak, P3 = uzun anlatim."""
    if anahtar in ref:
        return "P2"
    return "P1" if len(deger) <= 40 else "P3"


def main():
    ref = cfg_referanslari()
    kayitlar = []
    idx = 0

    for etiket, yol in SOZLUKLER:
        with io.open(yol, "r", encoding="utf-8", newline="") as f:
            for satir in f:
                m = re.match(r"^\s*#([A-Za-z0-9_]+)\s*=\s*(.*?)\r?\n?$", satir)
                if not m:
                    continue
                anahtar, deger = m.groups()
                if not deger.strip():
                    continue
                idx += 1
                bayrak = "ANAMENU" if anahtar in ANA_MENU else "-"
                kayitlar.append({
                    "idx": idx, "anahtar": anahtar, "dosya": etiket,
                    "deger": deger, "bayrak": bayrak,
                    "oncelik": oncelik(anahtar, deger, ref),
                })

    os.makedirs(os.path.join(KOK, "partiler/kaynak"), exist_ok=True)
    os.makedirs(os.path.join(KOK, "partiler/ceviri"), exist_ok=True)

    with io.open(os.path.join(KOK, "harita.tsv"), "w", encoding="utf-8") as f:
        f.write("idx\tanahtar\tdosya\tbayrak\toncelik\n")
        for k in kayitlar:
            f.write(f"{k['idx']}\t{k['anahtar']}\t{k['dosya']}\t"
                    f"{k['bayrak']}\t{k['oncelik']}\n")

    ozet = {}
    for p in ("P1", "P2", "P3"):
        # ORIJINAL SOZLUK SIRASI korunur: ardisik anahtarlar ayni alt sistemden
        # gelir, boylece "s" saniye mi guney mi komsularindan anlasilir.
        grup = [k for k in kayitlar if k["oncelik"] == p]
        parti, butce, n = [], 0, 0
        def yaz(parti, n):
            ad = f"{p}-{n:03d}.tsv"
            with io.open(os.path.join(KOK, "partiler/kaynak", ad),
                         "w", encoding="utf-8") as f:
                for k in parti:
                    # cok kisa metinlerde anahtar adini ipucu olarak ekle
                    ipucu = f"\t#{k['anahtar']}" if len(k["deger"]) <= 3 else ""
                    if k["bayrak"] == "ANAMENU":
                        ipucu += "\t#ANAMENU"
                    # satir sonlari literal "\n" olarak zaten kacisli
                    f.write(f"{k['idx']}\t{k['deger']}{ipucu}\n")
            return ad
        dosya_sayisi = 0
        for k in grup:
            parti.append(k)
            butce += len(k["deger"])
            if butce >= PARTI_KARAKTER or len(parti) >= PARTI_SATIR:
                n += 1
                yaz(parti, n)
                dosya_sayisi += 1
                parti, butce = [], 0
        if parti:
            n += 1
            yaz(parti, n)
            dosya_sayisi += 1
        ozet[p] = (len(grup), sum(len(k["deger"]) for k in grup), dosya_sayisi)

    print(f"{'faz':<5}{'anahtar':>9}{'karakter':>11}{'parti':>8}")
    print("-" * 33)
    for p in ("P1", "P2", "P3"):
        n, kar, d = ozet[p]
        print(f"{p:<5}{n:>9}{kar:>11,}{d:>8}")
    print("-" * 33)
    print(f"{'TOP':<5}{sum(o[0] for o in ozet.values()):>9}"
          f"{sum(o[1] for o in ozet.values()):>11,}"
          f"{sum(o[2] for o in ozet.values()):>8}")
    anamenu = sum(1 for k in kayitlar if k["bayrak"] == "ANAMENU")
    print(f"\nana menu kisitli anahtar: {anamenu}")


if __name__ == "__main__":
    sys.exit(main())
