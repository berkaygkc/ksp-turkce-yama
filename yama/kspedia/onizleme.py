#!/usr/bin/env python3
"""KSPedia sayfa onizlemesi — oyunu acmadan tasma gormek.

Sayfa arka plani bundle icinde Sprite olarak duruyor; metin kutulari ise
RectTransform + TextMeshPro. Ikisini birlestirip sayfanin nasil gorunecegini
PIL ile ciziyoruz. Amac guzel bir resim degil, TASMA TESPITI.

Kalibrasyon: once INGILIZCE kaynagi cizdirip bakiyoruz. Tasarimcilar metni
kutuya sigdirmis olmali; ingilizce cizimde tasma cikiyorsa model yanlistir,
Turkce sonucuna guvenilmez. Bu yuzden --kaynak ile yedegi cizdirmek sart.

Kisit: oyunun kendi yazi tipi degil sistem yazi tipi kullaniliyor, harf
genislikleri birebir ayni degil. Bu yuzden cikti UYARI seviyesindedir; "sinirda"
sonuclar oyunda dogrulanmali.

Koordinat uzayi: sayfa kok RectTransform'u 2048x1536. Arka plan Image'i
ebeveyne gerilmis (anchor 0,0 - 1,1), yani sprite 2048x1536'ya esnetiliyor.
Metin koordinatlari ve punto degerleri de bu uzayda. O yuzden sprite'i
2048x1536'ya buyutup her seyi ham canvas biriminde ciziyoruz.
"""
import os
import re
import sys
import UnityPy
from PIL import Image, ImageDraw, ImageFont

# TMP zengin metin etiketleri: <b>, <i>, <color=#ef2929>, <size=120%>, <sprite>...
# Bunlar EKRANDA GORUNMEZ, bicim komutudur. Olcerken sayilirsa metin oldugundan
# cok daha genis gorunur — ingilizce kaynakta 423 yanlis alarmin ana sebebi buydu.
ZENGIN = re.compile(r"</?[a-zA-Z][^<>]*>")

# Oyunun KSPedia yazi tipi, olcumde kullandigimiz Arial'den dar. Carpan
# ingilizce kaynak taranarak olculdu (tasarimcilar metni sigdirmis olmali,
# yani kaynakta cikan her "kirik" modelin kendi hatasidir):
#     carpan 1.00 -> 63 kirik    0.90 -> 6    0.86 -> 0    0.80 -> 0
# Kanitin izin verdigi EN SIKI deger 0.86. Daha dusugu modeli gevsetir ve
# Turkce'deki gercek sorunlari kacirmaya baslar.
GENISLIK_CARPANI = 0.86


def gorunur(t):
    """Ekranda gercekten yer kaplayan metin."""
    return ZENGIN.sub("", t).replace("\r", "")

KOK = os.path.dirname(os.path.abspath(__file__))
CIKTI = os.environ.get("KSP_ONIZLEME") or os.path.join(KOK, "onizleme")

# Turkce glyph tasiyan sistem yazi tipi
YAZI_TIPI = "/System/Library/Fonts/Supplemental/Arial Unicode.ttf"
if not os.path.exists(YAZI_TIPI):
    YAZI_TIPI = "/System/Library/Fonts/Supplemental/Arial.ttf"

CANVAS = (2048, 1536)


def sayfa_oku(yol):
    """bundle'dan (sprite, [metin nesnesi]) dondurur."""
    env = UnityPy.load(yol)
    sprite = None
    rect = {}
    for o in env.objects:
        if o.type.name == "Sprite" and sprite is None:
            try:
                sprite = o.read().image.convert("RGBA")
            except Exception:
                pass
        elif o.type.name == "RectTransform":
            d = o.read_typetree()
            rect[d["m_GameObject"]["m_PathID"]] = d

    metinler = []
    for o in env.objects:
        if o.type.name != "MonoBehaviour":
            continue
        try:
            d = o.read_typetree()
        except Exception:
            continue
        if not isinstance(d, dict):
            continue
        t = d.get("m_text")
        if not isinstance(t, str) or not t.strip():
            continue
        r = rect.get(d["m_GameObject"]["m_PathID"])
        if r is None:
            continue
        metinler.append({
            "metin": t,
            "font": float(d.get("m_fontSize") or 0),
            "taban": float(d.get("m_fontSizeMin") or 0) if d.get("m_enableAutoSizing") else None,
            "renk": d.get("m_fontColor"),
            "x": float(r["m_AnchoredPosition"]["x"]),
            "y": -float(r["m_AnchoredPosition"]["y"]),
            "w": float(r["m_SizeDelta"]["x"]),
            "h": float(r["m_SizeDelta"]["y"]),
        })
    return sprite, metinler


def olc(dr, s, fnt):
    """Metnin ekranda kaplayacagi genislik (oyun yazi tipine gore duzeltilmis)."""
    return dr.textlength(s, font=fnt) * GENISLIK_CARPANI


def sar(dr, metin, fnt, genislik):
    """Kelime bazli satir sarma; kaynaktaki gercek satir sonlarina saygi duyar."""
    cikti = []
    for parca in gorunur(metin).split("\n"):
        if not parca.strip():
            cikti.append("")
            continue
        satir = ""
        for kelime in parca.split(" "):
            deneme = (satir + " " + kelime).strip() if satir else kelime
            if olc(dr, deneme, fnt) <= genislik or not satir:
                satir = deneme
            else:
                cikti.append(satir)
                satir = kelime
        cikti.append(satir)
    return cikti


# Satir yuksekligi / punto. Kaynakta m_lineSpacing = -1.9 (negatif, yani
# satirlar puntodan SIKISIK). Ilk modelde 1.15 kullanilmisti; o yuzden
# ingilizce kaynakta ~100 sahte yukseklik tasmasi cikiyordu.
SATIR_YUKSEKLIGI = 1.0


def yerlestir(dr, m):
    """TMP yerlesimini taklit et.

    Kutular m_overflowMode=0 (Overflow) — metin KIRPILMAZ, kutunun altina
    tasabilir; tasarim bunu tolere ediyor. Dolayisiyla gercek arıza yukseklik
    degil GENISLIK: kutu bir kelimeyi bile alamayacak kadar darsa TMP kelimeyi
    harf harf alt alta dizer. "Lift" -> "Tasima Kuvveti" boyle patlamisti.

    Doner: (yazi_tipi, satirlar, kirik_mi, yukseklik_orani)
      kirik_mi        : en uzun KELIME en kucuk puntoda bile sigmiyor
      yukseklik_orani : gereken yukseklik / kutu yuksekligi (1'den buyukse tasar)
    """
    tavan = m["font"]
    taban = m["taban"] if m["taban"] else tavan
    kelimeler = [k for s in gorunur(m["metin"]).split("\n") for k in s.split(" ") if k]

    boy = tavan
    fnt = satirlar = None
    kirik = True
    while boy >= taban:
        fnt = ImageFont.truetype(YAZI_TIPI, int(round(boy)))
        satirlar = sar(dr, m["metin"], fnt, m["w"])
        yukseklik = (len(satirlar) - 1) * boy * SATIR_YUKSEKLIGI + boy
        # TMP otomatik boyut hem YUKSEKLIGE hem de bolunemeyen kelimenin
        # GENISLIGINE bakar. Ilk modelde yalniz yuksekligi kontrol ediyordum;
        # o yuzden tabani indirmek dar etiketlerde hicbir sey degistirmiyordu.
        en_uzun_kelime = max((olc(dr, k, fnt) for k in kelimeler), default=0)
        if yukseklik <= m["h"] and en_uzun_kelime <= m["w"]:
            kirik = False
            break
        boy -= 1
    if kirik:
        boy = taban
        fnt = ImageFont.truetype(YAZI_TIPI, int(round(boy)))
        satirlar = sar(dr, m["metin"], fnt, m["w"])
        # tabanda bile kelime sigmiyorsa gercekten kirik; sadece yukseklik
        # tasiyorsa degil (overflowMode=Overflow, dikey tasma tolere ediliyor)
        en_uzun_kelime = max((olc(dr, k, fnt) for k in kelimeler), default=0)
        kirik = en_uzun_kelime > m["w"]

    yukseklik = (len(satirlar) - 1) * boy * SATIR_YUKSEKLIGI + boy
    return fnt, satirlar, kirik, yukseklik / m["h"] if m["h"] else 0.0


def ciz(yol, cikti_adi, kutu_goster=True):
    sprite, metinler = sayfa_oku(yol)
    zemin = Image.new("RGBA", CANVAS, (255, 255, 255, 255))
    if sprite is not None:
        zemin = Image.alpha_composite(zemin, sprite.resize(CANVAS, Image.LANCZOS))
    im = zemin.convert("RGB")
    dr = ImageDraw.Draw(im)

    tasan = []
    for m in metinler:
        fnt, satirlar, tasti, _oran = yerlestir(dr, m)
        if m["renk"]:
            c = tuple(int(255 * float(m["renk"][k])) for k in "rgb")
        else:
            c = (30, 30, 30)
        boy = fnt.size
        for i, s in enumerate(satirlar):
            dr.text((m["x"], m["y"] + i * boy * 1.15), s, font=fnt, fill=c)
        if kutu_goster:
            dr.rectangle([m["x"], m["y"], m["x"] + m["w"], m["y"] + m["h"]],
                         outline=(255, 0, 0) if tasti else (120, 200, 120), width=3)
        if tasti:
            tasan.append((m["metin"].split("\n")[0][:34], m["w"], m["h"], len(satirlar)))

    p = cikti_adi if os.path.isabs(cikti_adi) else os.path.join(CIKTI, cikti_adi)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    im.resize((1280, 960), Image.LANCZOS).save(p)
    return p, tasan, len(metinler)


if __name__ == "__main__":
    adi = sys.argv[1] if len(sys.argv) > 1 else "kspedia_aircraftbasicslift.ksp"
    OYUN = os.path.dirname(KOK)
    hedefler = [
        ("KAYNAK (ingilizce)", os.path.join(KOK, "yedek", adi), "onizleme_en.png"),
        ("TURKCE (uygulanmis)", os.path.join(OYUN, "GameData/Squad/KSPedia", adi), "onizleme_tr.png"),
    ]
    for etiket, yol, ad in hedefler:
        if not os.path.exists(yol):
            print(f"{etiket}: dosya yok, atlandi"); continue
        p, tasan, n = ciz(yol, ad)
        print(f"\n{etiket}  ({n} metin nesnesi)  -> {p}")
        if tasan:
            print(f"   TASAN {len(tasan)}:")
            for t, w, h, sn in tasan:
                print(f"      kutu {w:>6.0f}x{h:<5.0f} {sn:>2} satir  {t!r}")
        else:
            print("   tasma yok")
