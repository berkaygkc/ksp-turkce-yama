#!/bin/bash
# Bu dosyaya ÇİFT TIKLA — Türkçe yamayı kurar.
# (Terminal açılır, işlem bitince kapatabilirsin.)
cd "$(dirname "$0")" || exit 1
bash yama/kur.sh "$@"
durum=$?
echo ""
echo "───────────────────────────────────────────────"
echo "Bu pencereyi kapatabilirsin.  (Cmd+W)"
echo ""
exit $durum
