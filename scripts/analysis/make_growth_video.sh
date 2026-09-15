#!/bin/bash
set -e
cd /home/shirley/PhysiCell_PDAC_hybrid_v2/scripts/analysis
ffmpeg -y -framerate 8 -i growth_frames/frame_%04d.png -vf "format=yuv420p" -c:v libx264 -crf 18 growth_video.mp4
echo "done: $(du -h growth_video.mp4)"
