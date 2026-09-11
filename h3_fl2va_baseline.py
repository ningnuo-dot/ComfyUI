#!/usr/bin/env python3
"""MiniMax H3 FL2VA 基线首跑脚本（ComfyUI2 / 8189 端口）

基线参数（对齐计划书 Phase 1 + 官方模板 video_minimax_h3_t2v）：
- 模型：Kijai w4a8 pruned + FL2VA-Acc-8Step pruned LoRA（官方模板同款用法）
- 编码器：nif0 qwen3vl-32b Q2_K_XL GGUF（CLIPLoaderGGUF type=minimax）
- 864x480 @ 124 帧（约 5.2s，H3 训练范围下限 124-362 帧）
- steps=8，scheduler=simple，sampler=res_multistep，种子固定

用法：先腾显存（≥11.5GB 空闲）并启动 ComfyUI2，再运行本脚本。
启动：.venv/Scripts/python.exe main.py --port 8189 --disable-async-offload --disable-pinned-memory
"""
import json
import time
import urllib.request

HOST = "http://127.0.0.1:8189"
VRAM_FREE_MIN_MB = 9000  # 12GB 卡需与桌面应用共存：9GB+ 时模型部分驻留显存、其余走卸载（--disable-async-offload 已在启动参数固化）

PROMPT = (
    "Static camera, medium shot. A young woman in a simple white t-shirt and jeans "
    "stands in a bright plain studio with a light gray background. She smiles softly, "
    "shifts her weight, and waves her right hand at the camera in a natural greeting. "
    "Even studio lighting, realistic skin texture, smooth natural motion."
)


def api(path, payload=None, timeout=30):
    url = HOST + path
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


def preflight_vram():
    """其他进程占用的显存无法从 torch 读取，改走 nvidia-smi；不足则直接拒绝开跑。"""
    import subprocess
    out = subprocess.run(
        ["nvidia-smi", "--query-gpu=memory.free", "--format=csv,noheader,nounits"],
        capture_output=True, text=True).stdout.strip().splitlines()[0]
    free_mb = int(out)
    if free_mb < VRAM_FREE_MIN_MB:
        raise SystemExit(f"显存空闲 {free_mb}MB < 需要的 {VRAM_FREE_MIN_MB}MB。"
                         "请先关闭老 ComfyUI(8188)/壁纸引擎/NVIDIA Broadcast 后重试。")
    print(f"[预检] 显存空闲 {free_mb}MB，通过")


def build_prompt():
    g = {
        "1": {"class_type": "UNETLoader", "inputs": {
            "unet_name": "minimax_h3_fl2va_pruned_w4a8_mixed.safetensors", "weight_dtype": "default"}},
        "2": {"class_type": "LoraLoaderModelOnly", "inputs": {
            "model": ["1", 0], "lora_name": "MiniMax-H3-FL2VA-Acc-8Step_pruned_comfy.safetensors",
            "strength_model": 1.0}},
        "3": {"class_type": "CLIPLoaderGGUF", "inputs": {
            "clip_name": "Qwen3-VL-32B-Instruct-MiniMax-H3-L0-49-UD-Q2_K_XL.gguf",
            "type": "minimax", "device": "cpu"}},
        "4": {"class_type": "CLIPTextEncode", "inputs": {"text": PROMPT, "clip": ["3", 0]}},
        "5": {"class_type": "EmptyMiniMaxH3LatentAV", "inputs": {"width": 864, "height": 480, "length": 124}},
        "6": {"class_type": "RandomNoise", "inputs": {"noise_seed": 1, "control": "fixed"}},
        "7": {"class_type": "KSamplerSelect", "inputs": {"sampler_name": "res_multistep"}},
        "8": {"class_type": "BasicScheduler", "inputs": {
            "model": ["2", 0], "scheduler": "simple", "steps": 8, "denoise": 1.0}},
        "9": {"class_type": "BasicGuider", "inputs": {"model": ["2", 0], "conditioning": ["4", 0]}},
        "10": {"class_type": "SamplerCustomAdvanced", "inputs": {
            "noise": ["6", 0], "guider": ["9", 0], "sampler": ["7", 0],
            "sigmas": ["8", 0], "latent_image": ["5", 0]}},
        "11": {"class_type": "VAELoader", "inputs": {"vae_name": "minimax_h3_video_vae_int8_convrot.safetensors"}},
        "12": {"class_type": "VAELoader", "inputs": {"vae_name": "minimax_h3_audio_vae_fp32.safetensors"}},
        "13": {"class_type": "VAEDecode", "inputs": {"samples": ["10", 0], "vae": ["11", 0]}},
        "14": {"class_type": "VAEDecodeAudio", "inputs": {"samples": ["10", 0], "vae": ["12", 0]}},
        "15": {"class_type": "CreateVideo", "inputs": {"images": ["13", 0], "fps": 24, "audio": ["14", 0]}},
        "16": {"class_type": "SaveVideo", "inputs": {
            "video": ["15", 0], "filename_prefix": "video/MiniMax_H3/fl2va_baseline",
            "format": "auto", "codec": "auto"}},
    }
    return {"prompt": g, "client_data": ""}


def main():
    preflight_vram()
    # 确认关键节点都已注册（GGUF/子图模板节点改名时会在这里报错，快速失败）
    info = api("/object_info")
    need = ["UNETLoader", "LoraLoaderModelOnly", "CLIPLoaderGGUF", "CLIPTextEncode",
            "EmptyMiniMaxH3LatentAV", "RandomNoise", "KSamplerSelect", "BasicScheduler",
            "BasicGuider", "SamplerCustomAdvanced", "VAELoader", "VAEDecode",
            "VAEDecodeAudio", "CreateVideo", "SaveVideo"]
    missing = [n for n in need if n not in info]
    if missing:
        raise SystemExit(f"缺少节点: {missing}")

    t0 = time.time()
    resp = api("/prompt", build_prompt())
    pid = resp["prompt_id"]
    print(f"[提交] prompt_id={pid}")
    while True:
        time.sleep(5)
        h = api(f"/history/{pid}")
        if pid in h:
            status = h[pid].get("status", {})
            if status.get("completed"):
                break
            if status.get("status_str") == "error":
                print(json.dumps(h[pid], ensure_ascii=False)[:2000])
                raise SystemExit("生成失败，详见上方历史输出")
        print(f"[等待] {time.time()-t0:.0f}s ...")

    outs = []
    for node_out in h[pid]["outputs"].values():
        for key, files in node_out.items():
            if isinstance(files, list):
                outs.extend(f.get("filename", "") for f in files if isinstance(f, dict))
    print(f"[完成] {time.time()-t0:.0f}s，输出: {outs}")
    print("目录: D:\\GitHub\\ComfyUI2\\output\\video\\MiniMax_H3\\")


if __name__ == "__main__":
    main()
