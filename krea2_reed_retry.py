# 重试 v5/v6：串行提交，间隔等待降内存压力
import json, time, urllib.request, urllib.parse
base = "http://127.0.0.1:8189"
CORE = ("深秋金黄色芦苇荡，一条狭窄的泥土小径从前景延伸向远方，镜头迎着低角度午后阳光逆光拍摄，"
        "芦苇花絮被逆光打透呈半透明金绒色，干土路上散落草籽，边缘草叶带轮廓光，暖橙色雾霭，空气透视，"
        "细腻胶片颗粒，35mm 胶片摄影，Kodak Portra 400 色调，平视站姿视角，"
        "画面中央小径空地留白供人物站立，无人，无文字，无水印，"
        "candid travel photo, photographic realism, no CGI look, no plastic texture, no vignetting")
STYLE = ", golden hour backlight, warm orange haze, film grain"
VARIANTS = [
    ("reed_v5_sky",  CORE + "，开阔天空占比更大，太阳清晰可见悬在地平线上方", 2026091105),
    ("reed_v6_dusk", CORE.replace("午后阳光", "傍晚贴着地平线的落日") + "，整体色调更橙更浓", 2026091106),
]
g = json.load(open(r"D:\GitHub\ComfyUI\models\krea2_first_test.json", encoding="utf-8"))
g["5"]["inputs"]["width"] = 1600
g["5"]["inputs"]["height"] = 900
import requests
for slug, prompt, seed in VARIANTS:
    g["6"]["inputs"]["text"] = prompt + STYLE
    g["3"]["inputs"]["seed"] = seed
    g["8"]["inputs"]["filename_prefix"] = "krea2_scenes/" + slug
    req = urllib.request.Request(base + "/prompt", data=json.dumps({"prompt": g}).encode(), headers={"Content-Type": "application/json"})
    pid = json.load(urllib.request.urlopen(req, timeout=30))["prompt_id"]
    t0 = time.time()
    while time.time() - t0 < 180:
        time.sleep(5)
        h = json.load(urllib.request.urlopen(f"{base}/history/{pid}", timeout=15))
        e = h.get(pid)
        if e and e.get("status", {}).get("status_str") in ("success", "error"):
            if e["status"]["status_str"] != "success":
                print("仍失败:", slug, flush=True); break
            for nid, out in e.get("outputs", {}).items():
                for img in out.get("images", []):
                    u = f"{base}/view?filename={urllib.parse.quote(img['filename'])}&subfolder={urllib.parse.quote(img.get('subfolder',''))}&type={img['type']}"
                    dst = "D:/GitHub/ComfyUI/output/" + img.get("subfolder", "") + "/" + img["filename"]
                    open(dst, "wb").write(urllib.request.urlopen(u, timeout=60).read())
            print("完成:", slug, f"{time.time()-t0:.0f}s", flush=True)
            break
    time.sleep(8)
print("RETRY DONE")
