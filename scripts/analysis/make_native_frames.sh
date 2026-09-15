#!/bin/bash
# Native PhysiCell 2D visualization panel: each snapshotNNNNNNNN.svg
# (built-in PhysiCell rendering) side-by-side with the auto-generated
# legend.svg (cell-type -> color key, from my_coloring_function). Rasterized
# via rsvg-convert (no cairosvg in this environment), then encoded to
# native_viz.mp4.
set -e
cd /home/shirley/PhysiCell_PDAC_hybrid_v2/scripts/analysis
rm -rf native_frames; mkdir -p native_frames

# legend is static across the whole run -- render once at a fixed height
# matching the snapshot's target height so they align side by side.
# -b white: legend.svg has no background rect (transparent); without this,
# ffmpeg's format=yuv420p later drops the alpha channel and turns the
# transparent area (and the black legend text sitting on it) invisible.
SNAP_H=1070
rsvg-convert -b white -h $SNAP_H -o native_frames/legend.png ../../outputs/pdac_therapy/legend.svg

n=0
for f in $(ls ../../outputs/pdac_therapy/snapshot*.svg | sort); do
    idx=$(printf "%04d" $n)
    rsvg-convert -b white -h $SNAP_H -o native_frames/snap_tmp.png "$f"
    convert native_frames/snap_tmp.png native_frames/legend.png +append \
        -background white -gravity North -splice 0x50 \
        native_frames/frame_${idx}.png
    n=$((n+1))
done
rm -f native_frames/snap_tmp.png native_frames/legend.png

echo "wrote $n native-viz frames"
ffmpeg -y -framerate 8 -i native_frames/frame_%04d.png -vf "scale=trunc(iw/2)*2:trunc(ih/2)*2,format=yuv420p" -c:v libx264 -crf 18 native_viz.mp4
echo "done: $(du -h native_viz.mp4)"
