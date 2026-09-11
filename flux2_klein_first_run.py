# FLUX.2 klein 4B fp8 首测脚本（ComfyUI / 8189）：提交工作流→轮询→取回成图（改提示词复用）
# 骨架复用 krea2_first_run.py；图结构来自官方模板 blueprints/Image Edit (Flux.2 Klein 4B).json
# 蒸馏版参数：4 步 + cfg 1.0（官方编辑模板用 base 版 20 步 cfg5，蒸馏版不等价）
import json, time, urllib.request, urllib.parse, sys

SIZE = int(sys.argv[1]) if len(sys.argv) > 1 else 1024
base = "http://127.0.0.1:8189"

graph = {
    "10": {"class_type": "UNETLoader", "inputs": {"unet_name": "flux-2-klein-4b-fp8.safetensors", "weight_dtype": "default"}},
    "11": {"class_type": "CLIPLoader", "inputs": {"clip_name": "qwen_3_4b.safetensors", "type": "flux2", "device": "default"}},
    "12": {"class_type": "VAELoader", "inputs": {"vae_name": "flux2-vae.safetensors"}},
    "6": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["11", 0], "text": "Full-body fashion photography of a young woman in a flowing crimson dress standing on a Santorini terrace at golden hour, whitewashed walls and blue domes behind her, soft warm natural light, 85mm lens, shallow depth of field, photorealistic, editorial quality"}},
    "13": {"class_type": "ConditioningZeroOut", "inputs": {"conditioning": ["6", 0]}},
    "20": {"class_type": "CFGGuider", "inputs": {"model": ["10", 0], "positive": ["6", 0], "negative": ["13", 0], "cfg": 1.0}},
    "21": {"class_type": "KSamplerSelect", "inputs": {"sampler_name": "euler"}},
    "22": {"class_type": "Flux2Scheduler", "inputs": {"steps": 4, "width": SIZE, "height": SIZE}},
    "23": {"class_type": "RandomNoise", "inputs": {"noise_seed": 20260911}},
    "5": {"class_type": "EmptyFlux2LatentImage", "inputs": {"width": SIZE, "height": SIZE, "batch_size": 1}},
    "3": {"class_type": "SamplerCustomAdvanced", "inputs": {"noise": ["23", 0], "guider": ["20", 0], "sampler": ["21", 0], "sigmas": ["22", 0], "latent_image": ["5", 0]}},
    "7": {"class_type": "VAEDecode", "inputs": {"samples": ["3", 0], "vae": ["12", 0]}},
    "8": {"class_type": "SaveImage", "inputs": {"images": ["7", 0], "filename_prefix": "flux2_klein_first_test"}},
}

req = urllib.request.Request(base + "/prompt", data=json.dumps({"prompt": graph}).encode(), headers={"Content-Type": "application/json"})
t0 = time.time()
try:
    resp = json.load(urllib.request.urlopen(req, timeout=30))
except Exception as e:
    print("提交失败:", e)
    raise SystemExit(1)
pid = resp.get("prompt_id")
if not pid:
    print("提交失败:", resp)
    raise SystemExit(1)
print("prompt_id:", pid, "| 已提交", f"{SIZE}x{SIZE} 4步")

outputs, ok = None, None
while time.time() - t0 < 600:
    time.sleep(3)
    try:
        h = json.load(urllib.request.urlopen(f"{base}/history/{pid}", timeout=15))
    except Exception as e:
        print("轮询异常:", e)
        continue
    entry = h.get(pid)
    if not entry:
        continue
    st = entry.get("status", {})
    if st.get("status_str") in ("success", "error"):
        ok = st.get("status_str")
        outputs = entry.get("outputs", {})
        print("状态:", ok, "| 耗时:", round(time.time() - t0, 1), "s")
        if ok == "error":
            print(json.dumps(st.get("messages", []), ensure_ascii=False)[:3000])
        break

if outputs and ok == "success":
    for nid, out in outputs.items():
        for img in out.get("images", []):
            url = f"{base}/view?filename={urllib.parse.quote(img['filename'])}&subfolder={urllib.parse.quote(img.get('subfolder',''))}&type={img['type']}"
            data = urllib.request.urlopen(url, timeout=60).read()
            dst = "D:/GitHub/ComfyUI/output/" + img["filename"]
            open(dst, "wb").write(data)
            print("成图已取回:", dst, f"({len(data)} bytes)")
else:
    print("无输出（超时或失败）")
