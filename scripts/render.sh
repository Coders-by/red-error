#!/bin/zsh
# 一键出片：时间轴 → 音效 → 混音 → 4 路并行逐帧渲染 → 拼接 + 混流
# 用法：scripts/render.sh [out.mp4]   （默认 out/red-error-final.mp4）
set -e
cd "${0:a:h}/.."
OUT="${1:-out/red-error-final.mp4}"
SEG=$(mktemp -d /tmp/re-seg.XXXX)
node scripts/build-timeline.js | tail -1
python3 scripts/sfx.py >/dev/null
python3 scripts/mix.py | tail -1
TOTAL=$(python3 -c "import json,math;print(math.ceil(json.load(open('audio/timeline.json'))['TOTAL']))" | tr -cd '0-9')
TOTAL=${TOTAL:-528}
Q=$(( (TOTAL + 3) / 4 ))
for k in 0 1 2 3; do
  a=$((k * Q)); b=$(( k == 3 ? TOTAL : (k + 1) * Q ))
  node scripts/capture.js $a $b $SEG/s$k.mp4 $((9450 + k)) > $SEG/log$k.txt 2>&1 &
done
wait
printf "file '$SEG/s%d.mp4'\n" 0 1 2 3 > $SEG/list.txt
ffmpeg -v error -y -f concat -safe 0 -i $SEG/list.txt -i out/mix.wav -map 0:v -map 1:a \
  -c:v copy -c:a aac -b:a 256k -shortest "$OUT"
rm -rf $SEG
ffprobe -v error -show_entries format=duration,size -of csv=p=0 "$OUT"
echo "done $OUT"
