# Krea-2 首测一次性脚本：提交工作流→轮询→取回成图（用完可删）
import json, time, urllib.request, urllib.parse

base = "http://127.0.0.1:8189"
graph = json.load(open(r"D:\GitHub\ComfyUI\models\krea2_first_test.json", encoding="utf-8"))
req = urllib.request.Request(base + "/prompt", data=json.dumps({"prompt": graph}).encode(), headers={"Content-Type": "application/json"})
t0 = time.time()
resp = json.load(urllib.request.urlopen(req, timeout=30))
pid = resp.get("prompt_id")
if not pid:
    print("提交失败:", resp)
    raise SystemExit(1)
print("prompt_id:", pid, "| 已提交")

outputs, ok = None, None
while time.time() - t0 < 360:
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
