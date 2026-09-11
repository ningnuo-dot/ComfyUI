#!/bin/bash
# MiniMax H3 权重下载脚本（hf-mirror 通道，断点续传）
# 用法: bash download_h3.sh   （重复运行只补缺失/不完整文件）
set -u
cd "$(dirname "$0")/models" || exit 1

# 目标相对路径 下载URL
FILES="
diffusion_models/minimax_h3_ref2va_pruned_w4a8_mixed.safetensors https://hf-mirror.com/Kijai/MiniMax-H3-experimental/resolve/main/minimax_h3_ref2va_pruned_w4a8_mixed.safetensors
diffusion_models/minimax_h3_fl2va_pruned_w4a8_mixed.safetensors https://hf-mirror.com/Kijai/MiniMax-H3-experimental/resolve/main/minimax_h3_fl2va_pruned_w4a8_mixed.safetensors
text_encoders/Qwen3-VL-32B-Instruct-MiniMax-H3-L0-49-UD-Q2_K_XL.gguf https://hf-mirror.com/nif0/Qwen3-VL-32B-Instruct-MiniMax-H3-GGUF/resolve/main/Qwen3-VL-32B-Instruct-MiniMax-H3-L0-49-UD-Q2_K_XL.gguf
text_encoders/Qwen3-VL-32B-Instruct-MiniMax-H3-L0-49-mmproj-BF16.gguf https://hf-mirror.com/nif0/Qwen3-VL-32B-Instruct-MiniMax-H3-GGUF/resolve/main/Qwen3-VL-32B-Instruct-MiniMax-H3-L0-49-mmproj-BF16.gguf
vae/minimax_h3_video_vae_int8_convrot.safetensors https://hf-mirror.com/Kijai/MiniMax-H3-experimental/resolve/main/minimax_h3_video_vae_int8_convrot.safetensors
vae/minimax_h3_audio_vae_fp32.safetensors https://hf-mirror.com/Comfy-Org/MiniMax-H3/resolve/main/vae/minimax_h3_audio_vae_fp32.safetensors
loras/MiniMax-H3-Ref2VA-Acc-8Step_pruned_comfy.safetensors https://hf-mirror.com/Kijai/MiniMax-H3-experimental/resolve/main/loras/MiniMax-H3-Ref2VA-Acc-8Step_pruned_comfy.safetensors
"

echo "=== H3 下载开始 $(date) ==="
echo "$FILES" | while read -r dest url; do
  [ -z "$dest" ] && continue
  echo "--- $dest"
  curl -L -C - -sS --retry 8 --retry-delay 5 --retry-all-errors --create-dirs -o "$dest" "$url"
  rc=$?
  if [ $rc -eq 0 ] && [ -f "$dest" ]; then
    echo "OK  $(du -h "$dest" | cut -f1)  $dest"
  else
    echo "FAIL rc=$rc  $dest"
  fi
done
echo "=== H3 下载结束 $(date) ==="
