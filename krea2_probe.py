# 保存链路探针：1024x1024 单张
import json, time, urllib.request, urllib.parse
base = "http://127.0.0.1:8189"
prompt = ("深秋金黄芦苇荡逆光，泥土小径，平视，无人，无文字，film grain, candid travel photo, "
          "photographic realism, no CGI look")
g = json.load(open(r"D:\GitHub\ComfyUI\models\krea2_first_test.json", encoding="utf-8"))
g["5"]["inputs"]["width"] = 1024
g["5"]["inputs"]["height"] = 1024
g["6"]["inputs"]["text"] = prompt
g["3"]["inputs"]["seed"] = 998877
g["8"]["inputs"]["filename_prefix"] = "krea2_scenes/probe_1024"
req = urllib.request.Request(base + "/prompt", data=json.dumps({"prompt": g}).encode(), headers={"Content-Type": "application/json"})
pid = json.load(urllib.request.urlopen(req, timeout=30))["prompt_id"]
t0 = time.time()
while time.time() - t0 < 200:
    time.sleep(5)
    h = json.load(urllib.request.urlopen(f"{base}/history/{pid}", timeout=15))
    e = h.get(pid)
    if e and e.get("status", {}).get("status_str") in ("success", "error"):
        print("状态:", e["status"]["status_str"], f"{time.time()-t0:.0f}s", flush=True)
        print("outputs:", json.dumps(e.get("outputs", {}), ensure_ascii=False)[:400], flush=True)
        break
