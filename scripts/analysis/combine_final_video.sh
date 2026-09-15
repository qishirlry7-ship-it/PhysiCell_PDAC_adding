#!/bin/bash
# Final combined video: left = native PhysiCell 2D visualization (+ legend),
# right = population growth/division/death dynamics (annotated with
# domain-mean substrate concentrations) stacked above the 7-substrate
# concentration contour/heatmap panel.
set -e
cd /home/shirley/PhysiCell_PDAC_hybrid_v2/scripts/analysis

ffmpeg -y \
  -i native_viz.mp4 -i growth_video.mp4 -i field_panel.mp4 \
  -filter_complex "\
[0:v]scale=-2:1200[left]; \
[1:v]scale=1100:-2[g]; \
[2:v]scale=1100:-2[h]; \
[g][h]vstack=inputs=2[right0]; \
[right0]scale=-2:1200[right]; \
[left][right]hstack=inputs=2,format=yuv420p[out]" \
  -map "[out]" -c:v libx264 -crf 18 -shortest pdac_15day_combined.mp4

echo "done: $(du -h pdac_15day_combined.mp4)"
ffprobe -v error -select_streams v:0 -show_entries stream=width,height,duration,nb_frames -of default=noprint_wrappers=1 pdac_15day_combined.mp4
