#!/bin/bash
set -e
cd /home/shirley/PhysiCell_PDAC_hybrid/outputs/pdac_therapy
rm -rf _frames; mkdir -p _frames

n=0
for f in $(ls snapshot*.svg | sort); do
    idx=$(printf "%04d" $n)
    convert -density 150 -background white "$f" "_frames/frame_${idx}.png"
    n=$((n+1))
done

frame_h=$(identify -format "%h" "_frames/frame_0000.png")
legend_h=$(( frame_h * 32 / 100 ))
convert -density 150 -background white legend.svg -trim +repage -resize x${legend_h} "_frames/legend.png"

y_offset=$(( frame_h * 8 / 100 ))
for f in _frames/frame_*.png; do
    convert "$f" "_frames/legend.png" -gravity northeast -geometry +15+${y_offset} -compose over -composite "$f"
done

ffmpeg -y -framerate 6 -i _frames/frame_%04d.png \
    -vf "scale=-2:800:flags=lanczos,format=yuv420p" \
    -c:v libx264 -pix_fmt yuv420p -crf 18 \
    ../../smoke_test_timelapse.mp4

rm -rf _frames
echo "done: $(du -h ../../smoke_test_timelapse.mp4)"
