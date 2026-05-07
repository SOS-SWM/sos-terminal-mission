#!/usr/bin/env bash
# 子集化 SarasaTermSCNerd-Regular.ttf 为 woff2，仅包含剧本与源码用到的字符
# 依赖：python3 + fonttools + brotli（pip install fonttools brotli）
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SRC_TTF="$ROOT/Assets/Fonts/SarasaTermSCNerd-Regular.ttf"
OUT_DIR="$ROOT/Web/public/fonts"
OUT_WOFF2="$OUT_DIR/SarasaTermSCNerd-subset.woff2"

if [[ ! -f "$SRC_TTF" ]]; then
  echo "Source font not found: $SRC_TTF" >&2
  exit 1
fi

mkdir -p "$OUT_DIR"
TMP_TTF="$OUT_DIR/.src.ttf"
CHARSET="$OUT_DIR/.charset.txt"
cp "$SRC_TTF" "$TMP_TTF"

python3 - "$ROOT" <<'PY'
import sys, pathlib
root = pathlib.Path(sys.argv[1])
chars = set(chr(c) for c in range(32, 127))
chars.update('▉▍─█▌▎▏│┌┐└┘├┤┬┴┼∩∪∽×÷±°·…→←↑↓☆★♪♥♡♂♀※≪≫《》「」『』（）【】〈〉〔〕～―ー')
for f in (root / 'Engine' / 'books').glob('*.md'):
    chars.update(f.read_text(encoding='utf-8'))
for f in (root / 'Web' / 'src').rglob('*.ts'):
    chars.update(f.read_text(encoding='utf-8'))
chars = sorted(c for c in chars if c.isprintable() or c == ' ')
out = root / 'Web' / 'public' / 'fonts' / '.charset.txt'
out.write_text(''.join(chars), encoding='utf-8')
print(f'charset: {len(chars)} chars')
PY

cd "$OUT_DIR"
pyftsubset .src.ttf \
  --text-file=.charset.txt \
  --output-file=SarasaTermSCNerd-subset.woff2 \
  --flavor=woff2 \
  --no-hinting \
  --desubroutinize \
  --drop-tables=GSUB,GPOS,GDEF,kern,morx \
  --layout-features=''
rm -f .src.ttf .charset.txt
ls -lh "$OUT_WOFF2"
