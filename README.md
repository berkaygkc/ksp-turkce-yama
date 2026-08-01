# Kerbal Space Program — Türkçe Yama

Kerbal Space Program 1.12.5'in **tamamını** Türkçeleştiren yama. Menüler, ayarlar,
parça adları, bilim raporları, sözleşmeler, uyarılar — ve oyun içi ansiklopedi
**KSPedia** dahil.

> **macOS'ta yapıldı ve test edildi.** Kurulum betikleri macOS için yazıldı.
> Windows/Linux için aşağıda [elle kurulum](#windows--linux) var; çeviri
> dosyaları her platformda aynı şekilde çalışır.

---

## Ne kadarı Türkçe?

| Bölüm | Durum |
|---|---|
| Oyun arayüzü (sözlük) | **12.656 metnin tamamı işlendi** — %93,8'i Türkçe, %6,2'si kasıtlı İngilizce |
| KSPedia (ansiklopedi) | **1.642 metnin tamamı** — %100 |
| Toplam | **~817.000 karakter** |

**Kasıtlı İngilizce kalanlar** (%6,2): gezegen ve karakter adları (Kerbin, Mun,
Jebediah), roket motoru takma adları ("Terrier", "Poodle"), ölçü birimleri
(m/s, kN), model kodları (LV-909, Mk1) ve yerleşik teknik terimler — bunları
çevirmek oyuncuyu İngilizce kaynaklardan, wiki'den ve mod'lardan koparırdı.

### Terim yaklaşımı

Havacılık ve yörünge mekaniğinin yerleşik terimleri İngilizce bırakıldı, gerisi
Türkçeleştirildi:

- **İngilizce kalanlar:** `delta-v`, `apoapsis`, `periapsis`, `SAS`, `RCS`,
  `EVA`, `CommNet`, `TWR`, `Isp`, `prograde`, `retrograde`
- **Parça adları:** model kodu ve takma ad korunur, tür adı çevrilir →
  `LV-909 "Terrier" Sıvı Yakıt Motoru`, `Mk1 Kumanda Kapsülü`

---

## Kurulum

### macOS (önerilen)

1. Sağ üstteki yeşil **Code** düğmesi → **Download ZIP**
2. İnen dosyaya çift tıkla, klasör açılsın
3. Klasörün içindeki **`KUR.command`** dosyasına **çift tıkla**
4. Bitti. Oyunu başlat.

**"Geliştirici doğrulanamadı" uyarısı çıkarsa** (macOS indirilen dosyalara
bunu yapar): `KUR.command` dosyasına **sağ tıkla → Aç** de, sonra çıkan
pencerede yine **Aç**'a bas. Bir kez yapman yeterli.

Yama oyunu kendi bulur. Bulamazsa sana ne yapacağını söyler.

### Terminal'i tercih edersen

```bash
git clone https://github.com/berkaygkc/ksp-turkce-yama.git
cd ksp-turkce-yama
./KUR.command
```

Oyun alışılmadık bir yerdeyse yolu kendin ver:

```bash
bash yama/kur.sh "/oyunun/tam/yolu/Kerbal Space Program"
```

### Kaldırmak için

**`KALDIR.command`** dosyasına çift tıkla. Oyun İngilizce'ye döner.

---

## Kurulum ne yapıyor?

Üç adım, hepsi geri alınabilir:

1. **Yedek alır.** Orijinal İngilizce dosyalar oyunun içindeki
   `_ksp-tr-yedek/` klasörüne kopyalanır. Yama tekrar kurulsa bile bu yedeğin
   **üstüne asla yazılmaz** — İngilizce'ye dönüş yolu kalıcıdır.
2. **Sözlüğü kurar.** `dictionary.cfg` dosyalarını Türkçe sürümleriyle değiştirir.
   Oyunun bütün arayüzü budur.
3. **KSPedia'yı yamalar.** Ansiklopedi sayfaları Unity asset bundle'ı olduğu için
   metin doğrudan değiştirilemiyor; yama bunu senin kendi dosyalarının üzerinde
   yapar (aşağıda [neden](#neden-kspedia-hazır-gelmiyor)).

**Bu adım için Python gerekiyor.** Yoksa yama onu atlar ve söyler — oyunun geri
kalanı yine de Türkçe olur. Python'u kurmak için Terminal'de:

```bash
xcode-select --install
```

Sonra `KUR.command`'a tekrar çift tıkla. Gereken paketler (UnityPy, Pillow)
oyunun içindeki ayrı bir klasöre kurulur, sistemine bulaşmaz.

---

## Sık sorulanlar

**Oyun güncellenirse ne olur?**
Steam güncellemesi dosyaların üstüne yazar ve yama silinir. `KUR.command`'a
tekrar çift tıkla, düzelir.

**Kayıtlı oyunlarım bozulur mu?**
Hayır. Yama yalnızca metin gösterimini değiştirir; kayıt dosyalarına dokunmaz.
Yamayı kaldırsan da kayıtların durur.

**Çok oyunculu / mod'larla çalışır mı?**
Mod'larla sorun yok. Mod'ların kendi metinleri İngilizce kalır.

**Yanlış/kötü bir çeviri gördüm.**
[Issue aç](https://github.com/berkaygkc/ksp-turkce-yama/issues) — ekran
görüntüsü çok yardımcı olur.

**Ana menüde bazı harfler tuhaf mı duruyor?**
Ana menünün nokta-matris yazı tipinde `Ç Ğ ğ İ Ş ş` karakterleri **yok**.
Oyunun kendi fontu bu, değiştiremiyoruz. Bu yüzden ana menü metinleri
o harflere ihtiyaç duymayacak kelimelerle yazıldı.

---

## Neden KSPedia hazır gelmiyor?

KSPedia sayfaları Unity asset bundle'ı: metin, diyagram çizimleri ve
texture'lar aynı dosyanın içinde. Yamalı hallerini depoya koymak, oyunun
**64 MB'lık grafik varlıklarını yeniden dağıtmak** olurdu. Onun yerine burada
yalnızca çeviri metni (~200 KB) ve yamalayıcı var; yamalayıcı senin kendi
kurulumunun üzerinde çalışıyor.

---

## Windows / Linux

Kurulum betikleri macOS için yazıldı ama **çeviri dosyaları platformdan
bağımsız.** Elle kurmak için:

**1. Sözlük** (asıl iş — arayüzün tamamı)

Önce orijinalleri bir yere kopyala, sonra değiştir:

| Bu dosyayı | Şununla değiştir |
|---|---|
| `GameData/Squad/Localization/dictionary.cfg` | `yama/sozluk/squad-dictionary.cfg` |
| `GameData/SquadExpansion/Serenity/Localization/dictionary.cfg` | `yama/sozluk/serenity-dictionary.cfg` |

Bu kadarı oyunun arayüzünü Türkçeleştirir.

**2. KSPedia** (isteğe bağlı)

```bash
python3 -m pip install UnityPy Pillow

# .ksp dosyalarını once yedekle, yedegi su yapida diz:
#   <yedek>/Squad/            <- GameData/Squad/KSPedia/*.ksp
#   <yedek>/MakingHistory/    <- GameData/SquadExpansion/MakingHistory/KSPedia/*.ksp
#   <yedek>/Serenity/         <- GameData/SquadExpansion/Serenity/KSPedia/*.ksp
#   <yedek>/SquadRoot/        <- GameData/Squad/*.ksp

KSP_OYUN="/oyunun/yolu" KSP_YEDEK="/yedegin/yolu" \
  python3 yama/kspedia/uygula_kspedia.py
```

Yamalayıcı **daima yedekten okur**, oyundan değil — böylece iki kez
çalıştırmak Türkçe'yi kaynak sanıp orijinali yok etmez.

---

## Nasıl yapıldı

Ayrıntı: [belgeler/NASIL-YAPILDI.md](belgeler/NASIL-YAPILDI.md)

Kısaca: çeviri yapay zeka ajanlarıyla parti parti yapıldı, ama her parti
**mekanik denetimden** geçti — eksik satır, bozulmuş biçim kodu, çevrilmemiş
metin, klavye tuşu adının çevrilmesi, kutuya sığmama. KSPedia'nın sayfa düzeni
sabit olduğu ve Türkçe ~%20 uzun olduğu için metni kısaltmak yerine **düzen
uyarlandı**: yazı tipi otomatik küçülüyor, gerekirse metin kutusu genişliyor.
226 sayfanın tamamında taşma yok — bu, sayfaları oyun dışında render eden bir
simülasyonla ölçüldü ve simülasyon önce İngilizce kaynağa çalıştırılarak
kalibre edildi.

---

## Katkı

Çeviri düzeltmeleri memnuniyetle. `gelistirme/sozluk.tsv` proje sözlüğüdür —
terim tutarlılığı oradan yürüyor. Bir terimi değiştireceksen önce oraya bak.

---

## Lisans ve haklar

Çeviri metinleri [CC BY 4.0](LICENSE) ile paylaşılıyor — kullan, değiştir,
dağıt; kaynağı belirtmen yeterli.

Kerbal Space Program'ın kendisi ve orijinal İngilizce metinleri
**Squad / Private Division / Intercept Games**'e aittir. Bu depo oyunun
hiçbir dosyasını dağıtmaz; yalnızca Türkçe metin ve onu senin kendi
kurulumuna uygulayan araçları içerir. Oyunun bir kopyasına sahip olman gerekir.

Bu resmî bir yama değildir, oyunun geliştiricileriyle bir bağı yoktur.
