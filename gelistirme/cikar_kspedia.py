#!/usr/bin/env python3
"""KSPedia tam olcekli metin cikarimi — 226 bundle, ceviri partilerine bolerek.

DAIMA _kspedia/yedek/ altindaki bozulmamis kopyalardan okur. Oyun klasorunden
okumak, ceviri uygulandiktan sonra Turkce metni "ingilizce kaynak" sanmaya ve
orijinali yok etmeye yol acar (sozluk isinde bu tuzaga bir kez yaklastik).

Cikti:
  metinler.tsv   — her metin NESNESI (dosya + path_id + kutu olculeri)
  parti/PXX.tsv  — ceviri ajanlarina verilecek benzersiz metinler

TSV'de gercek satir sonu olamaz; kaynak newline'lari "\\n" olarak KACIRILIR.
Uygulama tarafi geri cevirir. Kaynakta ters bolu olmadigi dogrulanir.
"""
import glob
import json
import os
import UnityPy
from sabit import SABIT, degismez_mi

KOK = os.path.dirname(os.path.abspath(__file__))
YEDEK = os.path.join(KOK, "yedek")
PARTI_DIZIN = os.path.join(KOK, "parti")

PARTI_KARAKTER = 3500     # ajan basina kaynak metin butcesi
KAR_ORAN = 0.50           # kutu.py ile ayni


def kacir(s):
    # \r de kacirilmali: kaynak metinlerde CRLF kalintisi yalin CR baytlari var
    # ("...\r\n..."). Kacirilmazsa TSV'ye ham 0x0D olarak girer ve Python metin
    # modu universal-newline ceviriyle onu satir sonu sayip kaydi ortadan boler.
    return (s.replace("\\", "\\\\").replace("\r", "\\r")
             .replace("\n", "\\n").replace("\t", "\\t"))


def coz(s):
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


def bundle_oku(yol):
    """(nesne listesi) dondurur; her nesne bir TMP metni + kutusu."""
    env = UnityPy.load(yol)
    rect, adlar = {}, {}
    for o in env.objects:
        if o.type.name == "RectTransform":
            d = o.read_typetree()
            rect[d["m_GameObject"]["m_PathID"]] = d
        elif o.type.name == "GameObject":
            adlar[o.path_id] = o.read_typetree().get("m_Name", "")
    out = []
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
        out.append({
            "path_id": o.path_id,
            "metin": t,
            "font": float(d.get("m_fontSize") or 0),
            "w": float(r["m_SizeDelta"]["x"]) if r else 0.0,
            "h": float(r["m_SizeDelta"]["y"]) if r else 0.0,
            "ad": adlar.get(d["m_GameObject"]["m_PathID"], ""),
        })
    return out


def main():
    os.makedirs(PARTI_DIZIN, exist_ok=True)
    dosyalar = sorted(glob.glob(os.path.join(YEDEK, "*", "*.ksp")))
    print(f"{len(dosyalar)} bundle taraniyor...")

    nesneler = []
    bos_bundle = []
    for yol in dosyalar:
        rel = os.path.relpath(yol, YEDEK)
        try:
            liste = bundle_oku(yol)
        except Exception as e:
            print(f"   !! okunamadi {rel}: {e}")
            continue
        if not liste:
            bos_bundle.append(rel)
        for n in liste:
            n["dosya"] = rel
            nesneler.append(n)

    if bos_bundle:
        print(f"   metin icermeyen {len(bos_bundle)} bundle: "
              f"{', '.join(bos_bundle[:4])}{' ...' if len(bos_bundle) > 4 else ''}")

    # ters bolu kontrolu — kacis semasinin guvenli oldugunu dogrula
    tersbolu = [n for n in nesneler if "\\" in n["metin"]]
    print(f"kaynakta ters bolu iceren metin: {len(tersbolu)}"
          + (" (kacis semasi yine de dogru calisir)" if tersbolu else ""))

    # benzersiz metinler; her biri icin EN DAR kutuyu (en sikisik yer) tut
    benzersiz = {}
    for n in nesneler:
        t = n["metin"]
        b = benzersiz.setdefault(t, {"metin": t, "sayi": 0, "w": 1e9, "font": 0,
                                     "h": 1e9, "dosyalar": set()})
        b["sayi"] += 1
        b["dosyalar"].add(n["dosya"])
        if n["w"] and n["w"] < b["w"]:
            b["w"], b["h"], b["font"] = n["w"], n["h"], n["font"]

    print(f"\n{len(nesneler):,} metin nesnesi -> {len(benzersiz):,} benzersiz metin")

    # ajana gitmeyecekler: kendiliginden degismezler + onayli pilot cevirileri
    atlanan_degismez = [t for t in benzersiz if degismez_mi(t)]
    atlanan_sabit = [t for t in benzersiz if t in SABIT and not degismez_mi(t)]
    for t in atlanan_degismez + atlanan_sabit:
        del benzersiz[t]
    print(f"   ajana gitmeyecek: {len(atlanan_degismez)} degismez "
          f"(tus adi/sayi) + {len(atlanan_sabit)} onayli pilot cevirisi")

    toplam_kar = sum(len(t) for t in benzersiz)
    print(f"cevrilecek: {len(benzersiz):,} metin, {toplam_kar:,} karakter")

    # tam envanter
    with open(os.path.join(KOK, "metinler.tsv"), "w", encoding="utf-8") as f:
        f.write("dosya\tpath_id\tad\tfont\tkutu_w\tkutu_h\tmetin\n")
        for n in sorted(nesneler, key=lambda x: (x["dosya"], x["path_id"])):
            f.write(f"{n['dosya']}\t{n['path_id']}\t{n['ad']}\t{n['font']:g}\t"
                    f"{n['w']:g}\t{n['h']:g}\t{kacir(n['metin'])}\n")

    # partilere bol: ayni SAYFAdaki metinler bir arada kalsin (baglam)
    sirali = sorted(benzersiz.values(),
                    key=lambda b: (sorted(b["dosyalar"])[0], -len(b["metin"])))
    partiler, simdi, boyut = [], [], 0
    for b in sirali:
        if simdi and boyut + len(b["metin"]) > PARTI_KARAKTER:
            partiler.append(simdi); simdi, boyut = [], 0
        simdi.append(b); boyut += len(b["metin"])
    if simdi:
        partiler.append(simdi)

    for eski in glob.glob(os.path.join(PARTI_DIZIN, "*.tsv")):
        os.remove(eski)

    idx = 0
    dizin = []
    for i, p in enumerate(partiler, 1):
        ad = f"P{i:02d}"
        yol = os.path.join(PARTI_DIZIN, f"{ad}.tsv")
        with open(yol, "w", encoding="utf-8") as f:
            f.write("idx\tkutu_w\tfont\tkapasite\tEN\n")
            for b in p:
                idx += 1
                b["idx"] = idx
                kap = int(b["w"] / (b["font"] * KAR_ORAN)) if b["font"] else 0
                f.write(f"{idx}\t{b['w']:g}\t{b['font']:g}\t{kap}\t{kacir(b['metin'])}\n")
        dizin.append({"parti": ad, "satir": len(p),
                      "karakter": sum(len(b["metin"]) for b in p)})

    # uygulama tarafinin ihtiyaci: idx -> kaynak metin
    with open(os.path.join(KOK, "benzersiz.json"), "w", encoding="utf-8") as f:
        json.dump({str(b["idx"]): b["metin"] for p in partiler for b in p},
                  f, ensure_ascii=False, indent=0)

    print(f"\n{len(partiler)} parti yazildi -> {PARTI_DIZIN}/")
    print(f"   parti basina ort. {toplam_kar // len(partiler):,} karakter, "
          f"{len(benzersiz) // len(partiler)} satir")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
