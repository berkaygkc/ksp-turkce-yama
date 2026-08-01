#!/usr/bin/env python3
"""TextMeshPro otomatik boyutlandirma — Turkce uzamasini anlam kaybetmeden emmek.

KSPedia sayfalari sabit tasarim; Turkce metin ~%15-25 uzun. Metni kisaltmak
anlam kaybettiriyor. Bunun yerine TMP'nin kendi ozelligini aciyoruz: metin
kutuya sigmazsa yazi tipi kucululur.

Tuzak: m_fontSizeMax kaynakta mevcut boyuttan BUYUK (or. 40 iken 72). Oylece
acilirsa TMP metni BUYUTUR de — kisa etiketler devasa olur. O yuzden tavani
mevcut boyuta sabitliyoruz; sadece kucule bilir.
"""

# Yazi tipi en fazla bu orana kadar kuculur. 0.70 = %30 kucul.
# Daha asagisi okunabilirligi bozar; ~%43 genislik kazanci saglar.
ALT_ORAN = 0.70


def otoboyut_ac(d):
    """TMP typetree sozlugunde otomatik boyutlandirmayi acar.

    Doner: (degisti_mi, aciklama)
    """
    if "m_enableAutoSizing" not in d or "m_fontSize" not in d:
        return False, "TMP alanlari yok"

    mevcut = float(d.get("m_fontSize") or 0)
    if mevcut <= 0:
        return False, "fontSize okunamadi"

    zaten = bool(d.get("m_enableAutoSizing"))
    tavan_once = float(d.get("m_fontSizeMax") or 0)

    d["m_enableAutoSizing"] = 1
    # TAVAN: mevcut boyut. Boylece metin asla BUYUMEZ, sadece kuculur.
    d["m_fontSizeMax"] = mevcut
    # TABAN: mevcut boyutun ALT_ORAN kati, ama kaynagin kendi tabaninin
    # altina inme (tasarimci oraya bir sinir koyduysa ona saygi duy).
    kaynak_taban = float(d.get("m_fontSizeMin") or 0)
    d["m_fontSizeMin"] = max(round(mevcut * ALT_ORAN, 1), kaynak_taban)

    return True, (f"fontSize={mevcut:g} tavan {tavan_once:g}->{mevcut:g} "
                  f"taban->{d['m_fontSizeMin']:g}"
                  + (" (zaten aciktu)" if zaten else ""))
