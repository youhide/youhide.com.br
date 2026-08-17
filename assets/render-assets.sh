#!/usr/bin/env bash
# Regenerate the raster assets in site/ from the sources in this directory.
# macOS only: uses sips and qlmanage, both built in. Run from the repo root.
#
#   ./assets/render-assets.sh
#
# qlmanage quirk: it always writes a SQUARE thumbnail and scales the SVG by its
# intrinsic width/height, so a 1200x630 source gets cropped. The workaround is
# to wrap the art in a 1200x1200 square, render that, then crop the band back
# out with sips.

set -euo pipefail
cd "$(dirname "$0")/.."

tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

echo "==> avatar"
# The source is a circular crop with an alpha channel, but CSS clips it to a
# circle anyway — so JPEG is safe here and roughly 6x smaller than PNG.
sips -Z 400 -s format jpeg -s formatOptions 80 \
     assets/avatar-source.png --out site/img/avatar.jpg >/dev/null

echo "==> favicons"
sed 's|width="64" height="64"|width="512" height="512"|' site/favicon.svg > "$tmp/fav512.svg"
qlmanage -t -s 512 -o "$tmp" "$tmp/fav512.svg" >/dev/null 2>&1
sips -Z 180 "$tmp/fav512.svg.png" --out site/apple-touch-icon.png >/dev/null
sips -Z 32  "$tmp/fav512.svg.png" --out site/favicon-32x32.png    >/dev/null

echo "==> open graph image"
python3 - "$tmp/og-square.svg" <<'PY'
import sys
src = open('assets/og.svg').read()
sq = src.replace('viewBox="0 0 1200 630" width="1200" height="630"',
                 'viewBox="0 0 1200 1200" width="1200" height="1200"')
sq = sq.replace('</defs>',
                '</defs>\n  <rect width="1200" height="1200" fill="#282a36"/>'
                '\n  <g transform="translate(0,285)">')
sq = sq.rsplit('</svg>', 1)[0] + '  </g>\n</svg>\n'
open(sys.argv[1], 'w').write(sq)
PY
qlmanage -t -s 1200 -o "$tmp" "$tmp/og-square.svg" >/dev/null 2>&1
sips -c 630 1200 "$tmp/og-square.svg.png" --out site/img/og.png >/dev/null

echo
ls -la site/img site/favicon-32x32.png site/apple-touch-icon.png
