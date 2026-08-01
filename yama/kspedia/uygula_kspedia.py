#!/usr/bin/env python3
"""KSPedia cevirisini 226 bundle'a uygular.

Akis (her bundle icin):
  1. YEDEKTEN oku (oyun klasorunden asla — bir kez yazdiktan sonra oradaki
     metin Turkce olur ve "kaynak" sanilirsa orijinal kaybolur)
  2. m_text'leri cevir
  3. otoboyut_ac(): yazi tipi kutuya sigmazsa kuculsun (tavan mevcut boyut)
  4. Sigmayan varsa kutuyu genislet — ne kadar gerektigini YERLESIM
     SIMULASYONU soyluyor (onizleme.py, ingilizce kaynakla kalibre edildi),
     kaba karakter sayimi degil. Genisleme komsu kutuya kadar sinirli.
  5. Geri okuyup dogrula, ancak ondan sonra oyuna yaz

--kuru ile hicbir sey yazilmaz, sadece rapor cikar.
"""
import glob
import io
import json
import os
import sys
import UnityPy
from PIL import Image, ImageDraw

from otoboyut import otoboyut_ac
from kutu import genislet, sag_bos_alan
from sabit import SABIT, degismez_mi
from onizleme import yerlestir, CANVAS

KOK = os.path.dirname(os.path.abspath(__file__))
# Dagitimda yamalayici oyunun icinde degil, ayri bir klasorde durur; oyun ve
# yedek yollari disaridan verilir. Ortam degiskeni yoksa gelistirme
# yerlesimine (yamalayici oyunun icinde) duser.
OYUN = os.environ.get("KSP_OYUN") or os.path.dirname(KOK)
YEDEK = os.environ.get("KSP_YEDEK") or os.path.join(KOK, "yedek")
CEVIRI_D = os.path.join(KOK, "ceviri")

# yedek alt dizini -> oyundaki hedef dizin
HEDEF_DIZIN = {
    "Squad":         "GameData/Squad/KSPedia",
    "MakingHistory": "GameData/SquadExpansion/MakingHistory/KSPedia",
    "Serenity":      "GameData/SquadExpansion/Serenity/KSPedia",
    "SquadRoot":     "GameData/Squad",
}

# Kutu en fazla bu kadar katina cikabilir. Cok buyuk buyume, kardes olcumunun
# goremedigi arka plan cizimine tasma riskini artirir.
AZAMI_KAT = 4.0


def coz(s):
    """cikar_kspedia.kacir()'in tersi."""
    out, i = [], 0
    while i < len(s):
        if s[i] == "\\" and i + 1 < len(s):
            c = s[i + 1]
            out.append({"n": "\n", "t": "\t", "r": "\r",
                        "\\": "\\"}.get(c, "\\" + c))
            i += 2
        else:
            out.append(s[i]); i += 1
    return "".join(out)


def harita_yukle():
    """{ingilizce_metin: turkce_metin} — ajan ciktilari + onayli sabitler."""
    kaynak = json.load(open(os.path.join(KOK, "benzersiz.json"), encoding="utf-8"))
    harita, eksik_parti = dict(SABIT), []
    for p in sorted(glob.glob(os.path.join(CEVIRI_D, "P*.tsv"))):
        with open(p, "rb") as f:
            for ham in f.read().split(b"\n"):
                satir = ham.decode("utf-8")
                if not satir.strip():
                    continue
                parcalar = satir.split("\t", 1)
                if len(parcalar) < 2 or not parcalar[0].strip().isdigit():
                    continue
                idx = parcalar[0].strip()
                if idx not in kaynak:
                    continue
                harita[coz(kaynak[idx])] = coz(parcalar[1])
    beklenen = {os.path.basename(p)[:-4]
                for p in glob.glob(os.path.join(KOK, "parti", "P*.tsv"))}
    gelen = {os.path.basename(p)[:-4] for p in glob.glob(os.path.join(CEVIRI_D, "P*.tsv"))}
    eksik_parti = sorted(beklenen - gelen)
    return harita, eksik_parti


def gereken_genislik(m, tavan):
    """Metnin sigmasi icin gereken en kucuk kutu genisligi (ikili arama).

    m: yerlestir()'in bekledigi sozluk. tavan: izin verilen azami genislik.
    Sigdiramiyorsa None doner.
    """
    dr = ImageDraw.Draw(Image.new("RGB", (8, 8)))
    deneme = dict(m)
    deneme["w"] = tavan
    if yerlestir(dr, deneme)[2]:
        return None                      # tavanda bile sigmiyor
    alt, ust = m["w"], tavan
    for _ in range(12):                  # ~0.02 hassasiyet yeter
        orta = (alt + ust) / 2
        deneme["w"] = orta
        if yerlestir(dr, deneme)[2]:
            alt = orta
        else:
            ust = orta
    return ust * 1.04                    # kucuk emniyet payi


def _gvenli_typetree(o):
    try:
        return o.read_typetree()
    except Exception:
        return None


def bundle_isle(yol, harita, dr):
    env = UnityPy.load(yol)
    rect, cocuk_haritasi = {}, {}
    for o in env.objects:
        if o.type.name == "RectTransform":
            d = o.read_typetree()
            rect[d["m_GameObject"]["m_PathID"]] = (o, d)
    pid2d = {o.path_id: d for o, d in rect.values()}

    ist = {"cevrilen": 0, "atlanan": 0, "otoboyut": 0,
           "genisletilen": 0, "tasan": [], "metin_sayisi": 0,
           "derin_kucultme": 0}

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
        ist["metin_sayisi"] += 1

        tr = harita.get(t)
        if tr is None:
            if not degismez_mi(t):
                ist["atlanan"] += 1
            continue
        d["m_text"] = tr
        ist["cevrilen"] += 1

        degisti, _ = otoboyut_ac(d)
        if degisti:
            ist["otoboyut"] += 1

        girdi = rect.get(d["m_GameObject"]["m_PathID"])
        if girdi is None:
            o.save_typetree(d)
            continue
        rnesne, rd = girdi
        m = {"metin": tr, "font": float(d.get("m_fontSize") or 0),
             "taban": float(d.get("m_fontSizeMin") or 0),
             "w": float(rd["m_SizeDelta"]["x"]),
             "h": float(rd["m_SizeDelta"]["y"])}
        if m["font"] <= 0 or m["w"] <= 0 or m["h"] <= 0:
            o.save_typetree(d)
            continue

        if yerlestir(dr, m)[2]:                       # otoboyut yetmedi
            ebeveyn = rd["m_Father"]["m_PathID"]
            kardesler = []
            if ebeveyn in pid2d:
                kardesler = [pid2d[c["m_PathID"]]
                             for c in pid2d[ebeveyn].get("m_Children", [])
                             if c["m_PathID"] in pid2d]
            pay = sag_bos_alan(rd, kardesler)
            tavan = m["w"] * AZAMI_KAT
            if pay is not None:
                tavan = min(tavan, m["w"] + pay)
            tavan = min(tavan, CANVAS[0] - float(rd["m_AnchoredPosition"]["x"]))
            gerek = gereken_genislik(m, tavan) if tavan > m["w"] else None
            if gerek:
                ok, _ = genislet(rd, gerek, pay)
                if ok:
                    rnesne.save_typetree(rd)
                    ist["genisletilen"] += 1
                    m["w"] = float(rd["m_SizeDelta"]["x"])

            # 3. catare: kutu genisleyemediyse (komsu cizim engelliyor) yaziyi
            # daha fazla kucult. Dar diyagram etiketleri boyle: "Wing/Lift"
            # kutusu 113 birim, saginda 9 birim bosluk var — ama 25 puntoda
            # "Kanat/Tasimasi" rahat siginca anlami bozmaya gerek kalmiyor.
            if yerlestir(dr, m)[2]:
                for oran in (0.60, 0.50, 0.45):
                    aday = round(m["font"] * oran, 1)
                    m["taban"] = aday
                    if not yerlestir(dr, m)[2]:
                        d["m_fontSizeMin"] = aday
                        ist["derin_kucultme"] += 1
                        break
                else:
                    ist["tasan"].append(tr.split("\n")[0][:40])

        o.save_typetree(d)
    return env, ist


def onceden_denetle():
    """Ajan ciktilarini onar ve dogrula. Hatali cikti varsa uygulama durur.

    Ajanlarin bir kismi `\\n` kacis dizisi yerine GERCEK satir sonu yazdi ve
    bunu yaptigini fark etmeden "dogruladim" diye raporladi. O yuzden ajan
    beyanina degil, bu mekanik gecise guveniyoruz.
    """
    import onar
    import dogrula_kspedia as dg

    onarilan = []
    for yol in sorted(glob.glob(os.path.join(CEVIRI_D, "P*.tsv"))):
        p = os.path.basename(yol)[:-4]
        kaynak = dg.oku_kaynak(p)
        ham = open(yol, "rb").read().decode("utf-8").rstrip("\n")
        if len(ham.split("\n")) != len(kaynak):
            sonuc, n = onar.onar(p, yaz=True)
            onarilan.append(f"{p}:{sonuc}")
    if onarilan:
        print(f"onarim: {', '.join(onarilan)}")

    hatali = []
    for yol in sorted(glob.glob(os.path.join(CEVIRI_D, "P*.tsv"))):
        p = os.path.basename(yol)[:-4]
        h, _ = dg.denetle(p)
        if h:
            hatali.append((p, h))
    if hatali:
        print(f"!! {len(hatali)} partide HATA var, oyuna yazilmaz:")
        for p, h in hatali[:6]:
            print(f"   {p}: {h[0]}")
    return not hatali


def main():
    kuru = "--kuru" in sys.argv
    if not onceden_denetle() and not kuru:
        return 1
    harita, eksik = harita_yukle()
    print(f"ceviri haritasi: {len(harita):,} metin")
    if eksik:
        print(f"!! eksik parti: {', '.join(eksik)} — bunlarin metinleri "
              f"INGILIZCE kalir")
        if not kuru:
            print("   eksik parti varken oyuna yazilmaz. --kuru ile rapor alabilirsin.")
            return 1

    dr = ImageDraw.Draw(Image.new("RGB", (8, 8)))
    toplam = {"cevrilen": 0, "atlanan": 0, "otoboyut": 0, "genisletilen": 0,
              "derin_kucultme": 0}
    tasan_sayfalar = []
    yazilan = 0

    for yol in sorted(glob.glob(os.path.join(YEDEK, "*", "*.ksp"))):
        alt = os.path.basename(os.path.dirname(yol))
        ad = os.path.basename(yol)
        try:
            env, ist = bundle_isle(yol, harita, dr)
        except Exception as e:
            print(f"   !! {alt}/{ad}: {e}")
            continue
        for k in toplam:
            toplam[k] += ist[k]
        if ist["tasan"]:
            tasan_sayfalar.append((f"{alt}/{ad}", ist["tasan"]))
        if not ist["cevrilen"] or kuru:
            continue

        veri = env.file.save(packer="original")

        # GERI OKUYUP DOGRULA, ancak ondan sonra oyuna yaz. Bozuk bir bundle
        # oyunu kirar; yazdiktan sonra fark etmek gec olur.
        try:
            kontrol = UnityPy.load(io.BytesIO(veri))
            metinler = [d for o in kontrol.objects if o.type.name == "MonoBehaviour"
                        for d in [_gvenli_typetree(o)]
                        if isinstance(d, dict) and isinstance(d.get("m_text"), str)
                        and d["m_text"].strip()]
        except Exception as e:
            print(f"   !! {alt}/{ad}: geri okuma basarisiz ({e}) — YAZILMADI")
            continue
        if len(metinler) != ist["metin_sayisi"]:
            print(f"   !! {alt}/{ad}: metin sayisi {ist['metin_sayisi']} -> "
                  f"{len(metinler)} — YAZILMADI")
            continue

        hedef = os.path.join(OYUN, HEDEF_DIZIN[alt], ad)
        with open(hedef, "wb") as f:
            f.write(veri)
        yazilan += 1

    print(f"\ncevrilen metin nesnesi : {toplam['cevrilen']:,}")
    print(f"cevirisi bulunamayan   : {toplam['atlanan']:,}")
    print(f"otoboyut acilan        : {toplam['otoboyut']:,}")
    print(f"kutusu genisletilen    : {toplam['genisletilen']:,}")
    print(f"derin kucultulen       : {toplam['derin_kucultme']:,}")
    print(f"hala tasan             : {sum(len(x[1]) for x in tasan_sayfalar):,} "
          f"({len(tasan_sayfalar)} sayfada)")
    if tasan_sayfalar:
        for sayfa, liste in tasan_sayfalar[:15]:
            print(f"   {sayfa}: {liste[:2]}")
    print(f"\noyuna yazilan bundle   : {yazilan}" if not kuru
          else "\n(kuru calisma — hicbir dosya yazilmadi)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
