#!/bin/bash
# 模板6 深度/姿态控制所需模型（hf-mirror，断点续传）
set -u
cd /d/GitHub/ComfyUI/models
FILES="
model_patches/minimax_h3_fun_controlnet_union_pruned_int8_convrot.safetensors https://hf-mirror.com/Comfy-Org/MiniMax-H3/resolve/main/model_patches/minimax_h3_fun_controlnet_union_pruned_int8_convrot.safetensors
diffusion_models/rt_detr_v4-x-hgnet_fp16.safetensors https://hf-mirror.com/Comfy-Org/SDPose/resolve/main/diffusion_models/rt_detr_v4-x-hgnet_fp16.safetensors
checkpoints/sdpose_wholebody_fp16.safetensors https://hf-mirror.com/Comfy-Org/SDPose/resolve/main/checkpoints/sdpose_wholebody_fp16.safetensors
"
echo "=== ctrl 模型下载开始 $(date) ==="
echo "$FILES" | while read -r dest url; do
  [ -z "$dest" ] && continue
  echo "--- $dest"
  curl -L -C - -sS --retry 8 --retry-delay 5 --retry-all-errors --create-dirs -o "$dest" "$url" \
    && echo "OK $(du -h "$dest" | cut -f1) $dest" || echo "FAIL $dest"
done
cd /d/GitHub/ComfyUI/input
echo "--- dancer_field_pose.mp4"
curl -L -C - -sS --retry 5 --retry-all-errors -o dancer_field_pose.mp4 "https://gh-proxy.com/https://raw.githubusercontent.com/Comfy-Org/workflow_templates/refs/heads/main/input/dancer_field_pose.mp4" \
  && echo "OK $(du -h dancer_field_pose.mp4 | cut -f1)" || echo "FAIL video"
echo "=== 结束 $(date) ==="
