#!/bin/zsh
# 串行生成 prompts.tsv 中的图 → web/img/<id>.jpg（已存在且新于 STAMP 则跳过），再预处理到 web/imgx（2560×1088 锐化）
cd "${0:a:h}/.."
STYLE="cinematic film still, anamorphic widescreen, photorealistic, shot on ARRI Alexa 65, sharp focus, crisp fine detail, clean image without noise, natural color grading, volumetric light, Red Dead Redemption 2 inspired lighting, no text"
mkdir -p web/img web/imgx
touch -t 202609270000 /tmp/.stamp0
i=0
while IFS=$'\t' read -r id p; do
  i=$((i+1)); f="web/img/$id.jpg"
  if [[ -f "$f.v2" ]]; then continue; fi
  q=$(python3 -c 'import sys,urllib.parse;print(urllib.parse.quote(sys.argv[1]))' "$p, $STYLE")
  for try in 1 2 3 4 5; do
    code=$(curl -s -o /tmp/gen_$id.jpg -w "%{http_code}" --max-time 180 "https://image.pollinations.ai/prompt/$q?width=1176&height=500&nologo=true&model=flux&seed=$((${SEEDOFF:-100}+i))")
    if [[ "$code" == 200 ]] && ffprobe -v error /tmp/gen_$id.jpg >/dev/null 2>&1; then
      mv /tmp/gen_$id.jpg "$f"; touch "$f.v2"; echo "ok $id"; break
    fi
    echo "retry $id ($code)"; sleep 20
  done
  sleep 4
done < prompts.tsv
for f in web/img/*.jpg; do
  n=$(basename $f .jpg)
  ffmpeg -v error -y -i $f -vf "crop=iw-80:ih-34:40:0,scale=2560:1088:force_original_aspect_ratio=increase:flags=lanczos,crop=2560:1088,unsharp=5:5:0.75:3:3:0.3" -q:v 2 web/imgx/$n.jpg
done
echo ALLDONE
