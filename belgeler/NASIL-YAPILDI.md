# Nasıl yapıldı

Bu belge yamanın teknik hikâyesi. Kurmak için okuman gerekmiyor —
[README](../README.md) yeter. Merak edersen ya da katkı vereceksen buradasın.

---

## 1. Oyunun metni nerede duruyor

KSP metni merkezî bir sözlükte tutuyor:

```
GameData/Squad/Localization/dictionary.cfg
  Localization { en-us { #autoLOC_12345 = Stability Assist } }
```

Parça tanımları (`.cfg`) metni değil **anahtarı** referans veriyor
(`title = #autoLOC_500123`). Yani tek dosyayı çevirince oyunun tamamı çevriliyor.
Bu, işi 60 bin dosya taramaktan tek dosyaya indiriyor.

KSP'nin dil listesinde Türkçe yok, o yüzden `en-us` bloğunun içeriği
değiştiriliyor. Oyun bunu fark etmiyor; kendi dilini İngilizce sanmaya devam
ediyor ama Türkçe gösteriyor.

### Dosya biçimi kırılgan

- **UTF-8 BOM + CRLF** satır sonu. İkisi de korunmalı; LF'e çevirirsen oyun
  sözlüğü okumuyor.
- `\n`, `\t`, ` ` gibi diziler dosyada **yazı olarak** duruyor (gerçek
  karakter değil). Bir metin düzenleyicinin bunları gerçek karaktere çevirmesi
  dosyayı sessizce bozuyor.
- Yer tutucular: `<<1>>`, `<<n:1>>` (çokluk), `<<g:2,1>>` (cinsiyet),
  `<<1[Auto/Override]>>`. Köşeli parantez içi **kullanıcıya görünür** ve
  çevrilmeli; yapı ve seçenek sayısı korunmalı.

---

## 2. KSPedia bambaşka bir problem

KSPedia sayfaları Unity **asset bundle**'ı (`.ksp`):

- `flags=0x43` → blok bilgisi LZ4HC, veri blokları **LZMA**
  (ham: 5 bayt props + akış, boyut alanı yok — `lzma.FORMAT_ALONE` için araya
  8 baytlık boyut eklemek gerekiyor)
- Şifreleme yok
- **`enableTypeTree = True`** — Squad type tree'yi striplememiş. Bu kritik:
  UnityPy metin alanını okuyup **geri yazabiliyor**.

Kaydederken `packer="original"` şart; varsayılan kayıt LZMA yerine başka bir
sıkıştırma kullanıp dosyayı **27 katına** şişiriyor.

### Asıl kısıt font değil, düzen

Fontlarda Türkçe karakter eksiği yok (tofu çıkmıyor). Sorun şu: sayfa
düzenleri sabit tasarlanmış ve Türkçe ortalama %20 daha uzun. `Lift` (4
karakter) için çizilmiş 66 piksellik bir ok etiketine `Taşıma Kuvveti` (14
karakter) yazınca metin harf harf alt alta diziliyor.

**Çözüm: metni kısaltmak yerine düzeni uyarlamak.** Üç katman, sırayla:

1. **Otomatik yazı boyutu** (`m_enableAutoSizing`) — tavan mevcut punto, taban
   %70. Tavanı sabitlemek şart, yoksa TMP kısa etiketleri **büyütüyor** da.
   Vakaların ~%99'unu çözüyor.
2. **Kutu genişletme** (`m_SizeDelta.x`) — 16 nesnede gerekti. Genişleme, aynı
   ebeveyn altındaki komşu kutulara olan mesafeyle sınırlanıyor.
3. **Daha derin küçültme** (taban %45'e kadar) — 2 nesnede gerekti.

Sonuç: 226 sayfada **0 taşma**.

### TMP'nin gerçekte ne yaptığı

Ölçüm sırasında öğrenilenler:

- `m_overflowMode = 0` (Overflow) — metin **kırpılmıyor**, kutunun altına
  taşabiliyor. Dikey taşma tasarımca tolere edilmiş. Gerçek arıza yalnızca kutu
  **bir kelimeyi bile** alamayacak kadar darsa oluşuyor.
- `m_lineSpacing = -1.9` — satırlar puntodan **sıkışık**, aralarında fazladan
  boşluk yok.
- Zengin metin etiketleri (`<b>`, `<color=#ef2929>`) ekranda yer kaplamıyor;
  genişlik hesabına katılmamalı.

---

## 3. Çeviri: ajanlar + mekanik denetim

Metin partilere bölünüp yapay zeka ajanlarına dağıtıldı (sözlük ~12.7 bin
anahtar, KSPedia 33 parti). Ama **ajanın kendi beyanı denetim yerine geçmiyor.**

Somut örnek: KSPedia'da 11 ajanın yaklaşık yarısı `\n` kaçış dizisi yerine
**gerçek satır sonu** yazdı — ve çoğu raporunda "kaçış dizilerini doğruladım"
dedi. Kök neden Python string literal'i: `"...\n..."` yazınca Python onu gerçek
satır sonuna çeviriyor; `r"..."` gerekiyor.

Bu yüzden her parti mekanik denetimden geçti:

| Denetim | Ne yakalar |
|---|---|
| Bütünlük | eksik/fazla satır |
| Kaçış dizisi | `\n` sayısının kaynakla eşleşmemesi |
| Yer tutucu | `<<1>>` yapısının bozulması |
| Çevrilmemiş | İngilizce'nin aynen kalması |
| Klavye tuşu | `W`/`A`/`S`/`D` adının çevrilmesi |
| Uzunluk | kutuya sığmama riski |
| Ana menü | fontta olmayan `Ç Ğ ğ İ Ş ş` kullanımı |

**Her denetim, bilerek bozulmuş bir girdiyle test edildi.** Bu boşuna bir
formalite değil: bir kaçış-dizisi denetimi fazla kaçırılmış ters bölü yüzünden
hiçbir şey yakalamadan "temiz" raporluyordu. Aynı hata bu projede iki kez
yapıldı; ikisi de ancak testle ortaya çıktı.

Bozuk çıktılar deterministik olarak onarıldı: her veri satırı `<sayı><TAB>` ile
başlamak zorunda olduğundan, öyle başlamayan satır bir öncekinin devamıdır.
Onarım **ancak kaynağa karşı doğrulanırsa** yazılıyor — doğrulanmazsa dosyaya
dokunulmuyor. Bu kural bir kez, ajan hâlâ yazarken yarım okunan dosyayı bozmaktan
kurtardı.

---

## 4. Taşmayı oyun açmadan ölçmek

226 sayfayı elle gezmek yerine, sayfaları oyun dışında render eden bir
simülasyon yazıldı: bundle'dan arka plan görseli, kutu koordinatları ve punto
değerleri okunup TMP'nin otomatik küçültmesi taklit ediliyor.

**Ama simülasyona güvenmeden önce kalibre edildi:** önce **İngilizce kaynağa**
çalıştırıldı. Tasarımcılar metni kutuya sığdırmış olmalı, dolayısıyla kaynakta
çıkan her taşma modelin kendi hatasıdır.

İlk çalıştırmada 423 taşma çıktı ve üç model hatası ortaya döküldü:

1. Zengin metin etiketleri görünür karakter sayılıyordu
2. Satır aralığı çarpanı yanlıştı (gerçek değer negatif)
3. Otomatik küçültme yalnız yüksekliğe bakıyordu, kelime genişliğine bakmıyordu

Düzeltmelerden sonra İngilizce taban **0**'a indi. Sistem fontu ile oyun fontu
arasındaki genişlik farkı (0,86 katsayısı) da tahmin edilmedi, bu taramayla
ölçüldü: 1,00'de 63 kırık, 0,90'da 6, 0,86'da 0.

---

## 5. Depodaki dosyalar

```
yama/
  kur.sh, kaldir.sh          kurulum / kaldırma
  sozluk/*.cfg               Türkçe sözlükler (asıl ürün)
  kspedia/
    ceviri/P01..P33.tsv      KSPedia çevirisi
    parti/P01..P33.tsv       kaynak İngilizce (denetim için gerekli)
    benzersiz.json           idx -> kaynak metin eşlemesi
    uygula_kspedia.py        yamalayıcı
    otoboyut.py              otomatik yazı boyutu
    kutu.py                  kutu genişletme + komşu ölçümü
    onizleme.py              yerleşim simülasyonu
    dogrula_kspedia.py       mekanik denetim
    onar.py                  ajan çıktısı onarımı

gelistirme/
  sozluk.tsv                 proje sözlüğü (~200 terim)
  cikar_kspedia.py           bundle'lardan metin çıkarma
  onizleme_toplu.py          tüm sayfaları tarayıp taşma raporu
  talimat_kspedia.md         çeviri ajanlarına verilen talimat
  dogrula.py, kalite.py      sözlük denetimleri
```

## Yeniden üretmek

```bash
# metni yeniden çıkar (yedekten okur, oyundan değil)
python3 gelistirme/cikar_kspedia.py

# ceviri ciktilarini denetle
python3 yama/kspedia/dogrula_kspedia.py

# uygula
KSP_OYUN=... KSP_YEDEK=... python3 yama/kspedia/uygula_kspedia.py

# tum sayfalari tarayip tasma raporu al
python3 gelistirme/onizleme_toplu.py
```

Çıkarma aracı **daima yedekten okur**. Oyundan okumak, çeviri uygulandıktan
sonra Türkçe metni "İngilizce kaynak" sanmaya ve orijinali kalıcı olarak yok
etmeye yol açar.
