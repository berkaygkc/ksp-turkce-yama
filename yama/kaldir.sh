#!/bin/bash
# Kerbal Space Program Türkçe Yama — kaldırma
#
# Yedekten orijinal İngilizce dosyaları geri koyar. Yedek klasörü yerinde
# kalır; istersen sonra tekrar kurabilirsin.

set -uo pipefail
KOK="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
YEDEK_ADI="_ksp-tr-yedek"

if [ -t 1 ]; then
  K="\033[1;36m"; Y="\033[1;32m"; U="\033[1;33m"; H="\033[1;31m"; S="\033[0m"
else K=""; Y=""; U=""; H=""; S=""; fi
baslik(){ printf "\n${K}%s${S}\n" "$1"; }
ok(){ printf "  ${Y}✓${S} %s\n" "$1"; }
uyari(){ printf "  ${U}!${S} %s\n" "$1"; }
hata(){ printf "\n${H}✗ %s${S}\n" "$1"; }

oyunu_bul() {
  if [ $# -ge 1 ] && [ -n "${1:-}" ]; then echo "$1"; return; fi
  if [ -n "${KSP_DIR:-}" ]; then echo "$KSP_DIR"; return; fi
  local adaylar=(
    "$HOME/Library/Application Support/Steam/steamapps/common/Kerbal Space Program"
    "/Applications/Kerbal Space Program"
    "$HOME/Applications/Kerbal Space Program"
  )
  local vdf="$HOME/Library/Application Support/Steam/steamapps/libraryfolders.vdf"
  if [ -f "$vdf" ]; then
    while IFS= read -r yol; do
      adaylar+=("$yol/steamapps/common/Kerbal Space Program")
    done < <(grep -o '"path"[[:space:]]*"[^"]*"' "$vdf" 2>/dev/null | sed 's/.*"\([^"]*\)"$/\1/')
  fi
  local a; for a in "${adaylar[@]}"; do
    if [ -d "$a/$YEDEK_ADI" ]; then echo "$a"; return; fi
  done
  echo ""
}

baslik "Türkçe yamayı kaldır"
OYUN="$(oyunu_bul "${1:-}")"

if [ -z "$OYUN" ]; then
  hata "Yedek klasörü olan bir KSP kurulumu bulunamadı."
  echo "  Yolu elle verebilirsin:  ./kaldir.sh \"/oyunun/yolu/Kerbal Space Program\""
  exit 1
fi
YEDEK="$OYUN/$YEDEK_ADI"
[ -d "$YEDEK" ] || { hata "Yedek yok: $YEDEK"; echo "  Yama zaten kurulu değil ya da yedek silinmiş."; exit 1; }

ok "Oyun: $OYUN"

geri() {   # geri <yedek> <hedef>
  [ -f "$1" ] || return 1
  mkdir -p "$(dirname "$2")"; cp -p "$1" "$2"
}

geri "$YEDEK/squad-dictionary.cfg" \
     "$OYUN/GameData/Squad/Localization/dictionary.cfg" && ok "Ana sözlük geri alındı"
geri "$YEDEK/serenity-dictionary.cfg" \
     "$OYUN/GameData/SquadExpansion/Serenity/Localization/dictionary.cfg" \
     && ok "Breaking Ground sözlüğü geri alındı"

n=0
for alt in Squad MakingHistory Serenity SquadRoot; do
  case "$alt" in
    Squad)         hedef="GameData/Squad/KSPedia" ;;
    MakingHistory) hedef="GameData/SquadExpansion/MakingHistory/KSPedia" ;;
    Serenity)      hedef="GameData/SquadExpansion/Serenity/KSPedia" ;;
    SquadRoot)     hedef="GameData/Squad" ;;
  esac
  [ -d "$YEDEK/kspedia/$alt" ] || continue
  for f in "$YEDEK/kspedia/$alt"/*.ksp; do
    [ -e "$f" ] || continue
    geri "$f" "$OYUN/$hedef/$(basename "$f")" && n=$((n+1))
  done
done
[ "$n" -gt 0 ] && ok "KSPedia geri alındı ($n dosya)"

# Bayrak yamanın kendi klasöründe; oyunun dosyası değil, silmek güvenli.
if [ -d "$OYUN/GameData/TurkceYama" ]; then
  rm -rf "$OYUN/GameData/TurkceYama"
  ok "Türk bayrağı kaldırıldı"
fi

baslik "Yama kaldırıldı"
echo "  Oyun tekrar İngilizce."
echo "  Yedek klasörü duruyor; istersen ./kur.sh ile tekrar kurabilirsin."
