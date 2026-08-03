#!/bin/bash
set -e
cd /home/shirley/PhysiCell_PDAC_hybrid_v2/scripts/analysis/field_frames/oxygen
rm -f *.png
n=0
for f in $(ls frame_*.ppm | sort); do
    idx=$(printf "%04d" $n)
    t=$((n * 60))
    convert "$f" -filter point -resize 500x500 \
        -gravity North -background white -splice 0x60 \
        -pointsize 22 -annotate +0+15 "oxygen (mmHg), t=${t} min" \
        "frame_${idx}.png"
    n=$((n+1))
done
ffmpeg -y -framerate 8 -i frame_%04d.png -vf "format=yuv420p" -c:v libx264 -crf 18 ../../oxygen_heatmap.mp4
echo "done: $(du -h ../../oxygen_heatmap.mp4)"
