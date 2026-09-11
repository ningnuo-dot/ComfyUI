# 孤树方向真实感加强 4 连拍（种子锁构图 + 文字管细节）
import json, time, urllib.request, urllib.parse
base = "http://127.0.0.1:8189"
CORE = ("深秋金黄色芦苇荡，一条泥土小径通向远处一棵大树的深色剪影，镜头迎着低角度午后阳光逆光拍摄，"
        "芦苇花絮被打透呈半透明金绒色，风吹芦苇轻微摇曳、高低错落不整齐，空气中漂浮干草粉尘，"
        "丁达尔光束穿过薄雾，干土路有脚印和路边杂草，树皮粗糙纹理，"
        "真实抓拍感，未经修图的原片，Canon EOS R5 实拍，50mm 定焦 f/2.8，Kodak Portra 400 胶片色调，"
        "细腻胶片颗粒，轻微镜头色差，平视站姿视角，画面中央小径留白供人物站立，"
        "无人，无文字，无水印，documentary photography, unedited RAW photo, natural imperfections, "
        "no CGI look, no plastic texture, no over-smoothing, no vignetting")
STYLE = ", golden hour backlight, warm haze, film grain"
VARIANTS = [
    ("v4r1_lock",  CORE, 2026091104),
    ("v4r2_close", CORE + "，大树更近更大，占画面右侧三分之一", 2026091104),
    ("v4r3_left",  CORE + "，大树在小径左侧，小径向右弯曲延伸", 2026091107),
    ("v4r4_dusk",  CORE.replace("午后阳光", "傍晚贴着地平线的落日") + "，整体色调更橙更浓", 2026091108),
]
g = json.load(open(r"D:\GitHub\ComfyUI2\models\krea2_first_test.json", encoding="utf-8"))
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
    while time.time() - t0 < 200:
        time.sleep(5)
        h = json.load(urllib.request.urlopen(f"{base}/history/{pid}", timeout=15))
        e = h.get(pid)
        if e and e.get("status", {}).get("status_str") in ("success", "error"):
            if e["status"]["status_str"] != "success":
                print("失败:", slug, flush=True); break
            for nid, out in e.get("outputs", {}).items():
                for img in out.get("images", []):
                    u = f"{base}/view?filename={urllib.parse.quote(img['filename'])}&subfolder={urllib.parse.quote(img.get('subfolder',''))}&type={img['type']}"
                    dst = "D:/GitHub/ComfyUI2/output/" + img.get("subfolder", "") + "/" + img["filename"]
                    open(dst, "wb").write(urllib.request.urlopen(u, timeout=60).read())
            print("完成:", slug, f"{time.time()-t0:.0f}s", flush=True)
            break
    time.sleep(6)
print("V4R DONE")
