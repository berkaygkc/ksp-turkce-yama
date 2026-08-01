#!/bin/bash
# Bu dosyaya ÇİFT TIKLA — Türkçe yamayı kaldırır, oyun İngilizce'ye döner.
cd "$(dirname "$0")" || exit 1
bash yama/kaldir.sh "$@"
durum=$?
echo ""
echo "───────────────────────────────────────────────"
echo "Bu pencereyi kapatabilirsin.  (Cmd+W)"
echo ""
exit $durum
