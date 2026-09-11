@echo off
rem ComfyUI2 启动（8189）：FLUX.2 klein 4B + MiniMax H3 主力实例
cd /d D:\GitHub\ComfyUI2
call .venv\Scripts\python.exe main.py --port 8189 --disable-async-offload --disable-pinned-memory
pause
