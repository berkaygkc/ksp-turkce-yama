#!/bin/bash
# Kerbal Space Program Türkçe Yama — kurulum
#
# Ne yapar:
#   1. Oyunun nerede kurulu olduğunu bulur
#   2. Orijinal dosyaların yedeğini alır (bir kez, asla üzerine yazmaz)
#   3. Türkçe sözlüğü kurar
#   4. İsteğe bağlı: KSPedia'yı (oyun içi ansiklopedi) yamalar
#
# Her adım geri alınabilir: ./kaldir.sh

set -uo pipefail

KOK="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
YEDEK_ADI="_ksp-tr-yedek"

# ——— renkler (terminal desteklemiyorsa boş) ———
if [ -t 1 ]; then
  K="\033[1;36m"; Y="\033[1;32m"; U="\033[1;33m"; H="\033[1;31m"; S="\033[0m"
else
  K=""; Y=""; U=""; H=""; S=""
fi
baslik() { printf "\n${K}%s${S}\n" "$1"; }
ok()     { printf "  ${Y}✓${S} %s\n" "$1"; }
uyari()  { printf "  ${U}!${S} %s\n" "$1"; }
hata()   { printf "\n${H}✗ %s${S}\n" "$1"; }

# ——————————————————————————————————————————————
# 1. Oyunu bul
# ——————————————————————————————————————————————
oyunu_bul() {
  # Kullanıcı elle verdiyse ona saygı duy
  if [ $# -ge 1 ] && [ -n "${1:-}" ]; then echo "$1"; return; fi
  if [ -n "${KSP_DIR:-}" ]; then echo "$KSP_DIR"; return; fi

  local adaylar=(
    "$HOME/Library/Application Support/Steam/steamapps/common/Kerbal Space Program"
    "/Applications/Kerbal Space Program"
    "$HOME/Applications/Kerbal Space Program"
    "$HOME/Library/Application Support/Steam/steamapps/common/KSP"
    "/Applications/KSP"
  )
  # Steam kütüphaneleri başka diskte olabilir
  local vdf="$HOME/Library/Application Support/Steam/steamapps/libraryfolders.vdf"
  if [ -f "$vdf" ]; then
    while IFS= read -r yol; do
      adaylar+=("$yol/steamapps/common/Kerbal Space Program")
    done < <(grep -o '"path"[[:space:]]*"[^"]*"' "$vdf" 2>/dev/null | sed 's/.*"\([^"]*\)"$/\1/')
  fi

  local a
  for a in "${adaylar[@]}"; do
    if [ -d "$a/GameData/Squad/Localization" ]; then echo "$a"; return; fi
  done
  echo ""
}

baslik "Kerbal Space Program Türkçe Yama"
echo "  Oyunu arıyorum..."

OYUN="$(oyunu_bul "${1:-}")"

if [ -z "$OYUN" ]; then
  hata "Kerbal Space Program bulunamadı."
  cat <<'YARDIM'

  Oyunun klasörünü kendin gösterebilirsin. İki yolu var:

  1) Bu betiği klasör yolunu vererek çalıştır:
       ./kur.sh "/oyunun/tam/yolu/Kerbal Space Program"

  2) Ya da Finder'da oyun klasörünü bul, Terminal'e sürükle-bırak:
       ./kur.sh <buraya sürükle>

  Doğru klasör, içinde "GameData" adında bir klasör olandır.
  Steam'de bulmak için: Steam > Kütüphane > KSP'ye sağ tık >
  Yönet > Yerel dosyalara göz at
YARDIM
  exit 1
fi

if [ ! -f "$OYUN/GameData/Squad/Localization/dictionary.cfg" ]; then
  hata "Bu klasör KSP gibi görünmüyor: $OYUN"
  echo "  İçinde GameData/Squad/Localization/dictionary.cfg bulunmalı."
  exit 1
fi

ok "Oyun bulundu:"
echo "     $OYUN"

SURUM="$(cat "$OYUN/readme.txt" 2>/dev/null | grep -m1 -o 'Version [0-9.]*' || echo '')"
[ -n "$SURUM" ] && echo "     $SURUM"

YEDEK="$OYUN/$YEDEK_ADI"
mkdir -p "$YEDEK/kspedia"

# ——————————————————————————————————————————————
# 2. Yedek al  (yalnızca ilk kurulumda — sonra asla dokunma)
# ——————————————————————————————————————————————
baslik "1/4  Orijinal dosyalar yedekleniyor"

# Yedek YALNIZCA yoksa alınır. Yama kurulu bir oyunun üstüne tekrar kurulunca
# Türkçe dosyaları "orijinal" diye kaydetmek felaket olurdu — İngilizce'ye
# dönüş yolu kalıcı olarak kaybolurdu.
YENI=0; VAR=0
yedekle() {   # yedekle <kaynak> <yedek-yolu>
  [ -f "$1" ] || return
  if [ -f "$2" ]; then VAR=$((VAR+1)); return; fi
  mkdir -p "$(dirname "$2")"
  cp -p "$1" "$2" && YENI=$((YENI+1))
}

yedekle "$OYUN/GameData/Squad/Localization/dictionary.cfg" \
        "$YEDEK/squad-dictionary.cfg"
yedekle "$OYUN/GameData/SquadExpansion/Serenity/Localization/dictionary.cfg" \
        "$YEDEK/serenity-dictionary.cfg"
if [ "$YENI" -gt 0 ]; then ok "Sözlük yedeklendi ($YENI dosya)"
else ok "Sözlük yedeği zaten vardı, korundu"; fi

YENI=0; VAR=0
n=0
for d in "GameData/Squad/KSPedia" \
         "GameData/SquadExpansion/MakingHistory/KSPedia" \
         "GameData/SquadExpansion/Serenity/KSPedia" \
         "GameData/Squad"; do
  [ -d "$OYUN/$d" ] || continue
  alt="$(echo "$d" | sed 's|GameData/SquadExpansion/||; s|GameData/||; s|/KSPedia||; s|^Squad$|SquadRoot|')"
  [ "$d" = "GameData/Squad/KSPedia" ] && alt="Squad"
  mkdir -p "$YEDEK/kspedia/$alt"
  for f in "$OYUN/$d"/*.ksp; do
    [ -e "$f" ] || continue
    yedekle "$f" "$YEDEK/kspedia/$alt/$(basename "$f")"
    n=$((n+1))
  done
done
if [ "$YENI" -gt 0 ]; then ok "KSPedia yedeklendi ($YENI dosya)"
else ok "KSPedia yedeği zaten vardı, korundu ($VAR dosya)"; fi
echo "     Yedek yeri: $YEDEK"
echo "     Bu klasörü silme — İngilizce'ye dönmenin tek yolu."

# ——————————————————————————————————————————————
# 3. Sözlüğü kur  (asıl iş — oyunun tüm arayüzü)
# ——————————————————————————————————————————————
baslik "2/4  Türkçe sözlük kuruluyor"

cp "$KOK/sozluk/squad-dictionary.cfg" \
   "$OYUN/GameData/Squad/Localization/dictionary.cfg"
ok "Ana sözlük kuruldu (12.656 metin)"

if [ -d "$OYUN/GameData/SquadExpansion/Serenity/Localization" ]; then
  cp "$KOK/sozluk/serenity-dictionary.cfg" \
     "$OYUN/GameData/SquadExpansion/Serenity/Localization/dictionary.cfg"
  ok "Breaking Ground sözlüğü kuruldu"
else
  uyari "Breaking Ground kurulu değil, atlandı"
fi

# ——————————————————————————————————————————————
# 4. Türk bayrağı
# Kendi GameData klasörüne konur; oyunun dosyalarına dokunulmaz, Steam
# doğrulaması bozmaz. Kaldırırken bu klasörü silmek yeterli.
# ——————————————————————————————————————————————
baslik "3/4  Türk bayrağı"

mkdir -p "$OYUN/GameData/TurkceYama/Flags"
cp "$KOK/bayrak/TurkBayragi.png" "$OYUN/GameData/TurkceYama/Flags/"
ok "Bayrak eklendi"
echo "     Oyunda: Uzay Merkezi > Yönetim Binası, ya da araç yaparken"
echo "     bayrak parçasına sağ tık > Bayrak Seç"

# ——————————————————————————————————————————————
# 5. KSPedia  (isteğe bağlı — Python gerektiriyor)
# ——————————————————————————————————————————————
baslik "4/4  KSPedia (oyun içi ansiklopedi)"

if [ "${KSPEDIA:-evet}" = "hayir" ]; then
  uyari "Atlandı (KSPEDIA=hayir dendi)"
  echo ""; ok "Kurulum tamam. İyi uçuşlar!"
  exit 0
fi

if ! command -v python3 >/dev/null 2>&1; then
  uyari "Python 3 bulunamadı — KSPedia atlanıyor."
  cat <<'PY_YOK'
     Oyunun geri kalanı yine de Türkçe. KSPedia'yı da istersen:
       1. Terminal'de şunu çalıştır:  xcode-select --install
       2. Sonra bu betiği tekrar çalıştır.
PY_YOK
  echo ""; ok "Kurulum tamam (KSPedia hariç). İyi uçuşlar!"
  exit 0
fi

VENV="$YEDEK/python-ortami"
if [ ! -x "$VENV/bin/python3" ]; then
  echo "  KSPedia'yı yamalamak için iki Python paketi gerekiyor."
  echo "  Bunları oyunun içine, ayrı bir klasöre kuruyorum (sisteme bulaşmaz)."
  python3 -m venv "$VENV" >/dev/null 2>&1 || {
    uyari "Python ortamı kurulamadı — KSPedia atlanıyor."
    echo ""; ok "Kurulum tamam (KSPedia hariç). İyi uçuşlar!"; exit 0; }
fi

echo "  Paketler indiriliyor (ilk seferde ~1 dakika)..."
"$VENV/bin/pip" install --quiet --disable-pip-version-check UnityPy Pillow 2>&1 | tail -3
if ! "$VENV/bin/python3" -c "import UnityPy, PIL" 2>/dev/null; then
  uyari "Paketler kurulamadı (internet?) — KSPedia atlanıyor."
  echo ""; ok "Kurulum tamam (KSPedia hariç). İyi uçuşlar!"
  exit 0
fi
ok "Python ortamı hazır"

echo "  226 sayfa yamalanıyor, birkaç dakika sürebilir..."
if KSP_OYUN="$OYUN" KSP_YEDEK="$YEDEK/kspedia" \
   "$VENV/bin/python3" "$KOK/kspedia/uygula_kspedia.py" 2>&1 | sed 's/^/     /'; then
  ok "KSPedia Türkçeleştirildi"
else
  uyari "KSPedia yamalanamadı — oyunun geri kalanı yine de Türkçe."
fi

baslik "Kurulum tamamlandı"
cat <<'SON'
  Oyunu başlat, her şey Türkçe olmalı.

  Beğenmediysen geri almak için:   ./kaldir.sh
SON
