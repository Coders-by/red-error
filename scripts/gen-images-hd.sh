#!/bin/zsh
# 用 gemini-3-pro-image-preview 原生 21:9 / 2K 重做底图 → web/img_hd/<id>.<ext>，再缩小到 web/imgx_hd/<id>.jpg（2560×1088，只缩不放）
# 用法：IMAGE_KEY=... scripts/gen-images-hd.sh [id ...]   不带参数则生成 prompts.tsv 全部；已存在的跳过（FORCE=1 强制重做）
cd "${0:a:h}/.."
setopt null_glob
: ${IMAGE_KEY:?IMAGE_KEY not set}
BASE="${IMAGE_BASE:-https://deepkey.top}"
STYLE="cinematic film still, anamorphic widescreen, photorealistic, shot on ARRI Alexa 65, sharp focus, crisp fine detail, clean image without noise, natural color grading, volumetric light, Red Dead Redemption 2 inspired lighting, no text"
mkdir -p web/img_hd web/imgx_hd
want=("$@")
while IFS=$'\t' read -r id p; do
  (( ${#want} )) && (( ! ${want[(Ie)$id]} )) && continue
  existing=(web/img_hd/$id.*)
  if [[ -z "$FORCE" ]] && (( ${#existing} )); then echo "skip $id"; continue; fi
  body=$(jq -n --arg t "$p, $STYLE" '{contents:[{role:"user",parts:[{text:$t}]}],generationConfig:{responseModalities:["IMAGE"],imageConfig:{aspectRatio:"21:9",imageSize:"2K"}}}')
  for try in 1 2 3; do
    code=$(curl -s -m 300 -o /tmp/gen_$id.json -w "%{http_code}" -X POST "$BASE/v1beta/models/gemini-3-pro-image-preview:generateContent" \
      -H "Authorization: Bearer $IMAGE_KEY" -H "Content-Type: application/json" -d "$body")
    part=$(jq -c '[.candidates[0].content.parts[]? | select(.inlineData and (.thought | not))] | last // empty' /tmp/gen_$id.json 2>/dev/null)
    if [[ "$code" == 200 && -n "$part" ]]; then
      ext=${$(jq -r '.inlineData.mimeType' <<<"$part")#image/}; [[ $ext == jpeg ]] && ext=jpg
      rm -f web/img_hd/$id.*
      jq -r '.inlineData.data' <<<"$part" | base64 -d > web/img_hd/$id.$ext
      if ffprobe -v error web/img_hd/$id.$ext >/dev/null 2>&1; then
        echo "ok $id $(ffprobe -v error -select_streams v:0 -show_entries stream=width,height -of csv=p=0:s=x web/img_hd/$id.$ext)"; break
      fi
    fi
    echo "retry $id ($code) $(head -c 200 /tmp/gen_$id.json)"; sleep 15
  done
  rm -f /tmp/gen_$id.json
done < prompts.tsv
for f in web/img_hd/*.*(N); do
  n=${${f:t}%.*}
  [[ -f web/imgx_hd/$n.jpg && web/imgx_hd/$n.jpg -nt $f ]] && continue
  ffmpeg -v error -y -i $f -vf "scale=2560:1088:force_original_aspect_ratio=increase:flags=lanczos,crop=2560:1088" -q:v 2 web/imgx_hd/$n.jpg
done
echo ALLDONE
