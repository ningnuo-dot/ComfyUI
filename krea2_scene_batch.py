# Krea-2 场景库重绘批量脚本（一次性，可复用）：8 地点 × 无人物干净钢板
import json, time, urllib.request, urllib.parse

base = "http://127.0.0.1:8189"
STYLE = ", no people, empty scene, clean travel photography, photorealistic, high detail"
SCENES = [
    ("aegean_sunset",    "Santorini caldera at golden sunset, whitewashed cliff-top village with blue-domed churches overlooking the Aegean Sea, warm light on white walls, empty terraces and stairways" + STYLE, 20260911),
    ("colosseum_dawn",   "The Roman Colosseum at dawn, empty ancient stone amphitheater under a soft pink-and-blue morning sky, light mist on the ground" + STYLE, 20260912),
    ("swiss_autumn",     "Lauterbrunnen valley in autumn, Swiss Alps, snow-capped peaks behind golden larch forests, wooden chalets and a winding country road, crisp morning light" + STYLE, 20260913),
    ("iceland_black",    "Reynisfjara black sand beach in Iceland, dramatic basalt columns and jagged sea stacks rising from dark surf, moody overcast sky" + STYLE, 20260914),
    ("faroe_cliffs",     "Faroe Islands sea cliffs with grass-roofed cottages, deep green fjords under drifting fog, wild North Atlantic light" + STYLE, 20260915),
    ("tekapo_morning",   "Lake Tekapo New Zealand, turquoise glacial lake with a small stone church on the shore, snow-capped Southern Alps across the water, clear morning light" + STYLE, 20260916),
    ("darcy_autumn",     "English countryside estate in deep autumn, a golden tree-lined avenue leading to a classic stone manor house, fallen leaves on the gravel drive, soft overcast light" + STYLE, 20260917),
    ("shanghai_bluehour","The Bund in Shanghai at blue hour, historic stone buildings along the waterfront, the futuristic Pudong skyline glowing across the Huangpu river" + STYLE, 20260918),
]

g = json.load(open(r"D:\GitHub\ComfyUI\models\krea2_first_test.json", encoding="utf-8"))
g["5"]["inputs"]["width"] = 1216
g["5"]["inputs"]["height"] = 832

pids, t0 = {}, time.time()
for slug, prompt, seed in SCENES:
    g["6"]["inputs"]["text"] = prompt
    g["3"]["inputs"]["seed"] = seed
    g["8"]["inputs"]["filename_prefix"] = "krea2_scenes/" + slug
    req = urllib.request.Request(base + "/prompt", data=json.dumps({"prompt": g}).encode(), headers={"Content-Type": "application/json"})
    pids[slug] = json.load(urllib.request.urlopen(req, timeout=30))["prompt_id"]
    print("已提交:", slug, flush=True)
    time.sleep(0.3)

done = {}
while len(done) < len(pids) and time.time() - t0 < 560:
    time.sleep(4)
    for slug, pid in pids.items():
        if slug in done:
            continue
        try:
            h = json.load(urllib.request.urlopen(f"{base}/history/{pid}", timeout=15))
        except Exception as e:
            print("轮询异常:", slug, e, flush=True)
            continue
        e = h.get(pid)
        if e and e.get("status", {}).get("status_str") in ("success", "error"):
            done[slug] = (e["status"]["status_str"], e.get("outputs", {}))

ok = 0
for slug, (st, outs) in done.items():
    if st != "success":
        print("失败:", slug, flush=True)
        continue
    for nid, out in outs.items():
        for img in out.get("images", []):
            u = f"{base}/view?filename={urllib.parse.quote(img['filename'])}&subfolder={urllib.parse.quote(img.get('subfolder',''))}&type={img['type']}"
            d = urllib.request.urlopen(u, timeout=60).read()
            dst = "D:/GitHub/ComfyUI/output/" + img.get("subfolder", "") + "/" + img["filename"]
            open(dst, "wb").write(d)
            ok += 1
            print("完成:", slug, dst, f"({len(d)} bytes)", flush=True)
print(f"总结: {ok}/{len(SCENES)} 张成功, 总耗时 {round(time.time()-t0,1)}s", flush=True)
