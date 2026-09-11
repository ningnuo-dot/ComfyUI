# 芦苇荡逆光横版 6 连拍（A 方向：奶油针织女装背景）
import json, time, urllib.request, urllib.parse

base = "http://127.0.0.1:8189"
CORE = ("深秋金黄色芦苇荡，一条狭窄的泥土小径从前景延伸向远方，镜头迎着低角度午后阳光逆光拍摄，"
        "芦苇花絮被逆光打透呈半透明金绒色，干土路上散落草籽，边缘草叶带轮廓光，暖橙色雾霭，空气透视，"
        "细腻胶片颗粒，35mm 胶片摄影，Kodak Portra 400 色调，平视站姿视角，"
        "画面中央小径空地留白供人物站立，无人，无文字，无水印，"
        "candid travel photo, photographic realism, no CGI look, no plastic texture, no vignetting")
STYLE = ", golden hour backlight, warm orange haze, film grain"

VARIANTS = [
    ("reed_v1_straight", CORE + "，小径笔直居中延伸至地平线，太阳光晕在小径尽头", 2026091101),
    ("reed_v2_curve",    CORE + "，小径呈 S 形弯曲穿过芦苇荡", 2026091102),
    ("reed_v3_immersive", CORE + "，两侧芦苇高过人头，贴近镜头，沉浸式纵深", 2026091103),
    ("reed_v4_tree",     CORE + "，小径旁一棵孤树的深色剪影作为视觉锚点", 2026091104),
    ("reed_v5_sky",      CORE + "，开阔天空占比更大，太阳清晰可见悬在地平线上方", 2026091105),
    ("reed_v6_dusk",     CORE.replace("午后阳光", "傍晚贴着地平线的落日") + "，整体色调更橙更浓", 2026091106),
]

g = json.load(open(r"D:\GitHub\ComfyUI2\models\krea2_first_test.json", encoding="utf-8"))
g["5"]["inputs"]["width"] = 1600
g["5"]["inputs"]["height"] = 900

pids, t0 = {}, time.time()
for slug, prompt, seed in VARIANTS:
    g["6"]["inputs"]["text"] = prompt + STYLE
    g["3"]["inputs"]["seed"] = seed
    g["8"]["inputs"]["filename_prefix"] = "krea2_scenes/" + slug
    req = urllib.request.Request(base + "/prompt", data=json.dumps({"prompt": g}).encode(), headers={"Content-Type": "application/json"})
    pids[slug] = json.load(urllib.request.urlopen(req, timeout=30))["prompt_id"]
    print("已提交:", slug, flush=True)
    time.sleep(0.3)

done = {}
while len(done) < len(pids) and time.time() - t0 < 900:
    time.sleep(5)
    for slug, pid in pids.items():
        if slug in done: continue
        try:
            h = json.load(urllib.request.urlopen(f"{base}/history/{pid}", timeout=15))
        except Exception as e:
            continue
        e = h.get(pid)
        if e and e.get("status", {}).get("status_str") in ("success", "error"):
            done[slug] = (e["status"]["status_str"], e.get("outputs", {}))

ok = 0
for slug, (st, outs) in done.items():
    if st != "success":
        print("失败:", slug, flush=True); continue
    for nid, out in outs.items():
        for img in out.get("images", []):
            u = f"{base}/view?filename={urllib.parse.quote(img['filename'])}&subfolder={urllib.parse.quote(img.get('subfolder',''))}&type={img['type']}"
            data = urllib.request.urlopen(u, timeout=60).read()
            dst = "D:/GitHub/ComfyUI2/output/" + img.get("subfolder", "") + "/" + img["filename"]
            open(dst, "wb").write(data)
            ok += 1
            print("完成:", slug, dst, f"({len(data)//1024} KB)", flush=True)
print(f"总结: {ok}/{len(VARIANTS)} 张成功, 总耗时 {round(time.time()-t0,1)}s", flush=True)
