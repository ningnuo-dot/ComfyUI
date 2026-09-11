#!/usr/bin/env python3
"""MiniMax H3 Ref2VA 第一臂（深度视频参考）运行脚本

实验 A（本脚本）：四视图 + 米兰场景 + 深度视频(24fps 帧序列) → 严格按深度分镜出片
实验 B（待原 RGB 视频路径）：同参数换原视频参考，A/B 对比深度 vs RGB 参考

参考接线（MiniMaxH3ReferenceToVideo）：<Picture 1>=四视图 <Picture 2>=米兰场景 <Video 1>=深度动作帧序列
"""
import json
import time
import urllib.request

HOST = "http://127.0.0.1:8189"
VRAM_FREE_MIN_MB = 9000

PROMPT = (
    "<Picture 1> is the same woman: long black hair, cream turtleneck sweater, long cream knit skirt, "
    "pearl pumps. <Picture 2> is the location: the Duomo square in Milan at golden-hour sunset, warm "
    "backlight, long shadows on the cobblestone, gothic cathedral facade and vintage lamp posts. "
    "<Video 1> is the strict motion, timing and shot reference.\n"
    "One continuous static shot, 9:16 vertical framing, subject centered. The woman from <Picture 1> "
    "stands in the square from <Picture 2> and performs exactly the action timeline of <Video 1>:\n"
    "0-2s: she faces the camera, then turns her head and shoulders to a three-quarter profile and takes "
    "out a folded paper map;\n"
    "2-5s: she unfolds the map and reads it while walking slowly forward as the camera gently pushes in;\n"
    "5-7s: she lowers the map to her waist, faces the camera and pauses;\n"
    "7-9s: she walks toward the camera, glancing down at the map in her hand;\n"
    "9-12s: she does a joyful spin, her long knit skirt flaring out and her black hair swinging with the turn;\n"
    "12-14s: she settles from the spin, faces the camera with a soft smile, end pose.\n"
    "Keep her identity, hairstyle and outfit exactly as <Picture 1>. Warm sunset backlight and long "
    "shadows from <Picture 2>. Natural realistic motion with pacing strictly matching <Video 1>."
)


def api(path, payload=None, timeout=30):
    url = HOST + path
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


def main():
    import subprocess
    free = int(subprocess.run(["nvidia-smi", "--query-gpu=memory.free", "--format=csv,noheader,nounits"],
                              capture_output=True, text=True).stdout.strip().splitlines()[0])
    if free < VRAM_FREE_MIN_MB:
        raise SystemExit(f"显存空闲 {free}MB < {VRAM_FREE_MIN_MB}MB，先腾显存")
    info = api("/object_info")
    need = ["UNETLoader", "LoraLoaderModelOnly", "CLIPLoaderGGUF", "LoadImage",
            "LoadVideo", "GetVideoComponents", "MiniMaxH3ReferenceToVideo", "RandomNoise",
            "KSamplerSelect", "BasicScheduler", "BasicGuider", "SamplerCustomAdvanced",
            "VAELoader", "VAEDecode", "VAEDecodeAudio", "CreateVideo", "SaveVideo"]
    missing = [n for n in need if n not in info]
    if missing:
        raise SystemExit(f"缺少节点: {missing}")

    g = {
        "1": {"class_type": "UNETLoader", "inputs": {
            "unet_name": "minimax_h3_ref2va_pruned_w4a8_mixed.safetensors", "weight_dtype": "default"}},
        "2": {"class_type": "LoraLoaderModelOnly", "inputs": {
            "model": ["1", 0], "lora_name": "MiniMax-H3-Ref2VA-Acc-8Step_pruned_comfy.safetensors",
            "strength_model": 1.0}},
        "3": {"class_type": "CLIPLoaderGGUF", "inputs": {
            "clip_name": "Qwen3-VL-32B-Instruct-MiniMax-H3-L0-49-UD-Q2_K_XL.gguf",
            "type": "minimax", "device": "cpu"}},
        "4": {"class_type": "LoadImage", "inputs": {"image": "h3_fourview.png"}},
        "5": {"class_type": "LoadImage", "inputs": {"image": "h3_milan_duomo.png"}},
        "6": {"class_type": "LoadVideo", "inputs": {"file": "h3_depth_ref_24fps.mp4"}},
        "19": {"class_type": "GetVideoComponents", "inputs": {"video": ["6", 0]}},
        "7": {"class_type": "MiniMaxH3ReferenceToVideo", "inputs": {
            "clip": ["3", 0], "vae": ["13", 0], "audio_vae": ["14", 0],
            "prompt": PROMPT, "width": 480, "height": 864, "length": 340,
            "ref_image_size": "match",
            "ref_images.ref_image_1": ["4", 0], "ref_images.ref_image_2": ["5", 0],
            "ref_videos.ref_video_1": ["19", 0]}},
        "8": {"class_type": "RandomNoise", "inputs": {"noise_seed": 1, "control": "fixed"}},
        "9": {"class_type": "KSamplerSelect", "inputs": {"sampler_name": "res_multistep"}},
        "10": {"class_type": "BasicScheduler", "inputs": {
            "model": ["2", 0], "scheduler": "simple", "steps": 8, "denoise": 1.0}},
        "11": {"class_type": "BasicGuider", "inputs": {"model": ["2", 0], "conditioning": ["7", 0]}},
        "12": {"class_type": "SamplerCustomAdvanced", "inputs": {
            "noise": ["8", 0], "guider": ["11", 0], "sampler": ["9", 0],
            "sigmas": ["10", 0], "latent_image": ["7", 1]}},
        "13": {"class_type": "VAELoader", "inputs": {"vae_name": "minimax_h3_video_vae_int8_convrot.safetensors"}},
        "14": {"class_type": "VAELoader", "inputs": {"vae_name": "minimax_h3_audio_vae_fp32.safetensors"}},
        "15": {"class_type": "VAEDecode", "inputs": {"samples": ["12", 0], "vae": ["13", 0]}},
        "16": {"class_type": "VAEDecodeAudio", "inputs": {"samples": ["12", 0], "vae": ["14", 0]}},
        "17": {"class_type": "CreateVideo", "inputs": {"images": ["15", 0], "fps": 24, "audio": ["16", 0]}},
        "18": {"class_type": "SaveVideo", "inputs": {
            "video": ["17", 0], "filename_prefix": "video/MiniMax_H3/ref2va_depthA",
            "format": "auto", "codec": "auto"}},
    }
    t0 = time.time()
    resp = api("/prompt", {"prompt": g, "client_data": ""})
    pid = resp["prompt_id"]
    print(f"[提交] prompt_id={pid}")
    while True:
        time.sleep(10)
        h = api(f"/history/{pid}")
        if pid in h:
            st = h[pid].get("status", {})
            if st.get("completed"):
                break
            if st.get("status_str") == "error":
                print(json.dumps(h[pid], ensure_ascii=False)[:3000])
                raise SystemExit("生成失败")
        print(f"[等待] {time.time()-t0:.0f}s ...")
    outs = []
    for node_out in h[pid]["outputs"].values():
        for files in node_out.values():
            if isinstance(files, list):
                outs.extend(f.get("filename", "") for f in files if isinstance(f, dict))
    print(f"[完成] {time.time()-t0:.0f}s 输出: {outs}")


if __name__ == "__main__":
    main()
