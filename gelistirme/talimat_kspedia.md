# KSPedia çeviri görevi

Kerbal Space Program'ın oyun içi ansiklopedisini (KSPedia) Türkçeye çeviriyorsun.
Bu metinler oyuncunun oyunu öğrendiği asıl dokümantasyon — anlam doğruluğu
her şeyden önce gelir.

## Girdi / çıktı

Girdi: `_kspedia/parti/PXX.tsv` — başlık satırı + veri satırları:

```
idx	kutu_w	font	kapasite	EN
```

Çıktı: `_kspedia/ceviri/PXX.tsv` — **başlık yok**, sadece:

```
idx	TR
```

Her girdi satırı için tam bir çıktı satırı. Ne eksik ne fazla. `idx` girdideki
sayının **aynısı** olacak.

---

## ⚠️ İki tuzak — daha önce iki ajan ikisine de düştü

**1. Read aracının satır numarası `idx` DEĞİLDİR.**
Read dosyayı gösterirken her satırın başına kendi numarasını ekler (`1→`, `2→`).
Bu numara dosyanın içeriği değildir. Gerçek `idx`, TAB'dan önceki **ilk
sütundur**. Satırları 1,2,3… diye yeniden numaralandırırsan çeviri yanlış
metinlere bağlanır ve tüm parti çöp olur.

**2. Çıktı dosyasını Edit/Write aracıyla yazma — Python ile yaz.**
Edit/Write'ın JSON katmanı `\n` yazısını gerçek satır sonuna çevirir ve dosyayı
sessizce bozar. Çıktıyı şöyle yaz:

```python
satirlar = [(12, "Çeviri metni"), (13, "Başka çeviri\\ndevamı")]
with open(yol, "w", encoding="utf-8") as f:
    for idx, tr in satirlar:
        f.write(f"{idx}\t{tr}\n")
```

`\n` dizisini Python string'inde `\\n` olarak yazdığına dikkat et — dosyada
iki karakter (ters bölü + n) olarak durmalı.

---

## Kaçış dizileri — birebir korunacak

Kaynakta gerçek satır sonu `\n`, sekme `\t` olarak **kaçırılmıştır**. Bunlar
metnin içinde iki karakterlik yazı olarak durur. Sayfa düzeni bunlara bağlı:

- Kaynakta kaç tane `\n` varsa çeviride de **aynı sayıda** olacak.
- Yerleri anlamlı: satır sonu nerede bölüyorsa çeviride de benzer yerde bölmeli.
- Baştaki/sondaki boşlukları koru. Liste maddelerindeki girintiyi (` 1. `,
  `     ve `) aynen bırak.

Örnek:

```
girdi : 42	Wings generate lift.\nDrag slows you down.
çıktı : 42	Kanatlar taşıma kuvveti üretir.\nSürüklenme seni yavaşlatır.
```

---

## Terim tutarlılığı — iki başvuru dosyası

**`_ceviri/sozluk.tsv`** — proje sözlüğü. Önce buna bak.

Kararlaştırılmış çizgi: **teknik terimler İngilizce kalır**, gerisi Türkçe.
İngilizce kalacaklar: `delta-v`, `apoapsis`, `periapsis`, `SAS`, `RCS`, `EVA`,
`CommNet`, `KSC`, `VAB`, `SPH`, `TWR`, `Isp`, `Monopropellant`, `prograde`,
`retrograde`, gök cisimleri (Kerbin, Mun, Minmus, Duna…), `Kerbal`, `Kerman`
ve karakter adları.

**`_kspedia/ui_terimler.tsv`** — oyunun arayüzünde ne yazdığının EN→TR listesi
(6.063 satır). KSPedia sürekli arayüzden bahsediyor; oradaki yazıyla birebir
aynı olmak zorunda. Kullanmadan önce **grep'le**:

```bash
grep -iP "^Construction Interface\t" _kspedia/ui_terimler.tsv
#   -> Construction Interface	Yapım Arayüzü
```

Bir arayüz öğesi, buton, sekme ya da ekran adı geçiyorsa mutlaka bak. Kendi
karşılığını uydurma — oyunda başka yazıyorsa oyuncu kaybolur.

---

## Parça adları

Model kodu ve takma ad korunur, tür adı çevrilir:

- `LV-909 "Terrier" Liquid Fuel Engine` → `LV-909 "Terrier" Sıvı Yakıt Motoru`
- `Mk1 Command Pod` → `Mk1 Kumanda Kapsülü`

## Sayılar

Ondalık ayırıcı virgül olur: `RWA = 2.0` → `RWA = 2,0`. Binlik ayırıcıya
dokunma, birim simgelerini (`m/s`, `kN`, `km`) çevirme.

## Klavye tuşları

`W`, `A`, `S`, `D`, `Shift`, `Ctrl` gibi tuş adları **asla** çevrilmez. Metin
içinde tuştan bahsediyorsa tuş adı İngilizce kalır: "W tuşuna bas".

---

## Uzunluk

`kapasite` sütunu, o kutuya mevcut puntoda satır başına kaç karakter sığdığını
söyler. Çevirinin **her satırı** bu değerin altında kalırsa iyi olur.

Ama: anlamı bunun için feda etme. Arkanda iki katman var — yazı tipi otomatik
küçülüyor (~%43 ek yer) ve gerekirse kutu genişletiliyor. Doğal ve doğru
Türkçe yaz; gereksiz uzatma da yapma. `kapasite` 0 ise kutu ölçüsü yok, serbestsin.

---

## Üslup

- Oyuncuya "sen" diye hitap et (oyunun kendi üslubu böyle).
- KSP'nin esprili tonunu koru, ama teknik açıklamada netlikten şaşma.
- Başlıklarda gereksiz büyük harf kullanma; Türkçe yazım kurallarına uy.
- Türkçe karakterleri eksiksiz kullan: `ç ğ ı İ ö ş ü`. ASCII'ye düşürme.

## Bitirince

Çıktı dosyasını yazdıktan sonra satır sayısını kaynakla karşılaştır ve
`\n` sayılarının tuttuğunu kontrol et. Rapor olarak sadece şunu döndür:
işlenen parti adı, satır sayısı, kaynakla eşleşip eşleşmediği.
