#!/bin/bash
set -e
cd /home/shirley/PhysiCell_PDAC_hybrid_v2/scripts/analysis/field_frames
N_FRAMES=$(ls oxygen/frame_*.ppm | wc -l)
rm -rf panel; mkdir -p panel

for sub in oxygen glucose lactate ECM TGF_beta IFN_gamma; do
    n=0
    for f in $(ls $sub/frame_*.ppm | sort); do
        idx=$(printf "%04d" $n)
        convert "$f" -filter point -resize 300x300 \
            -gravity North -background white -splice 0x36 \
            -pointsize 16 -annotate +0+8 "$sub" \
            "$sub/panel_${idx}.png"
        n=$((n+1))
    done
done

n=0
while [ $n -lt $N_FRAMES ]; do
    idx=$(printf "%04d" $n)
    t=$((n * 60))
    convert \( oxygen/panel_${idx}.png glucose/panel_${idx}.png lactate/panel_${idx}.png +append \) \
            \( ECM/panel_${idx}.png TGF_beta/panel_${idx}.png IFN_gamma/panel_${idx}.png +append \) \
            -append -gravity North -background white -splice 0x40 \
            -pointsize 22 -annotate +0+10 "t = ${t} min" \
            "panel/frame_${idx}.png"
    n=$((n+1))
done

ffmpeg -y -framerate 8 -i panel/frame_%04d.png -vf "format=yuv420p" -c:v libx264 -crf 18 ../field_panel.mp4
echo "done: $(du -h ../field_panel.mp4)"
