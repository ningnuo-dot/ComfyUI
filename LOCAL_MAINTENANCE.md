# ComfyUI2 本地维护说明（MiniMax H3 部署线）

2026-09-11 新建。与老安装 `D:\GitHub\ComfyUI` 并排的全新官方 ComfyUI，作为 MiniMax H3 本地部署与后续主力候选；老安装原文未动作回退。上游自带 AGENTS.md 保留不动，本文件只记本地定制。机器：RTX 4070 **12GB**（12282MB）+ 物理内存 **16GB**，D 盘。

## Git 远端

- `origin` = 用户 fork `ningnuo-dot/ComfyUI`（master 跟踪 origin/master）；`upstream` = 官方 `Comfy-Org/ComfyUI`。2026-09-12 应客户端提示把 upstream 从旧地址 `comfyanonymous/ComfyUI` 更新为现址（同仓库迁移，历史与提交号不变）。
- 同步上游按 `D:\Agent-JiYi\shared\github-local-upstream-workflow.md`：候选分支 merge、验证后再切，不在本运行副本直接 pull。本地内容按主题小提交、中文提交说明；默认不 push。

## 启动

```bat
D:\GitHub\ComfyUI2\.venv\Scripts\python.exe main.py --port 8189 --disable-async-offload --disable-pinned-memory
```

- 端口固定 8189：8188 被老 ComfyUI 占用。
- 两个 disable 参数是 Krea-2 部署时实测固化的低内存修复（16GB 物理内存机器上「异步卸载+钉住内存」会崩），H3 沿用。

## 环境

- uv venv + cpython 3.12（uv 托管），torch 2.14.0+cu130（直连轮子 URL 安装，uv 对 +cu130 标签解析会失败）。
- 其余包按老 venv site-packages 反推的 `env_pins.txt` 逐版本复刻；清华镜像 `--index-url https://pypi.tuna.tsinghua.edu.cn/simple`。
- 自定义节点 `ComfyUI-GGUF`（gh-proxy 镜像克隆，github.com 直连不稳定）+ **`ComfyUI-Chinese-Translation`（中文汉化，2026-09-12 装）**。H3 官方节点是 0.35.0 内置（`comfy_extras/nodes_minimax_h3.py`），无需第三方。
- **翻译插件本地补丁**（在其 `zh-CN/Nodes/internal.json`，上游拉更新后需重打或提 PR）：新增 5 条——MiniMaxH3AddGuide（锚点）、MiniMaxH3FunControlNetApply（控制网）、CLIPLoaderGGUF、UnetLoaderGGUF、VideoTrim；修 3 处——Music3 条目「MiniMa水平偏移」坏字符串×2、ReferenceToVideo 描述文不对题。上游其余 H3 翻译（ReferenceToVideo 21 输入/ImageToVideo/EmptyLatentAV/SigmaShift/SDPose 全家）直接可用。AIGODLIKE 无 H3 覆盖已排除；老安装里的无远端旧副本弃用。
- **汉化生效核验（2026-09-12 实机）**：浏览器实测菜单/节点/参数全面中文，右上「翻译开启 (zh-CN)」默认开。已知边界：H3 官方模板里的**分组框标题**（User Inputs、Video Settings 等）是工作流内容文本，**节点自定义标题**（`Load Video  (Control Video)`、`Resolution Selector (Size)`，写在模板 JSON 的 title 字段）受插件「自定义标题保护」设计跳过。**同日已处理**：6 个 H3 模板的分组框+节点自定义标题共 73 处批量汉化（仅改 `groups[].title`/`nodes[].title`；脚本与原文件备份在 `user\backup_20260912_workflows\`，脚本 `rename_h3_titles.py`，上游模板更新后如需重跑可复用）；**第二轮补漏**：模板 1/2/5 子图（`definitions.subgraphs`）内部 9 处×3 文件=27 处（脚本 `rename_h3_subgraph_titles.py`）。**闭环测试（不出片）全过**：①主图+子图全部真实节点在服务端 934 个注册类型中齐全（MarkdownNote/UUID 子图实例系前端虚拟节点，不在 object_info 属正常）；②6 模板经 `app.loadGraphData` 实机载入节点数/连线数全一致、零缺节点、零英文标题残留；③`graphToPrompt` 序列化全部成功且核心节点（ImageToVideo/ReferenceToVideo/AddGuide×3/FunControlNetApply）与 If/Else 开关均正确进入 API prompt。**回滚**：`user\backup_20260912_workflows\rollback.py v0|v1|v2`（v0 原始英文/v1 仅主图汉化/v2 全汉化；同目录有 3 个双击 .bat；每次回滚前自动快照当前状态，回滚可再撤销）。未翻项：模板 MarkdownNote 的英文正文（量大未动，需要时再翻）。

## 模型

- `extra_model_paths.yaml` 借用老安装 `D:\GitHub\ComfyUI\models`（只读借用，同名本机优先），klein/Krea-2 无需迁移即可用。
- H3 权重全部在本机 `models/`，SHA-256 清单 `models/h3_weights_sha256.txt`（7 个文件 2026-09-11 全部校验通过，LoRA 单独验过 1 个）：
  - `diffusion_models/minimax_h3_{fl2va,ref2va}_pruned_w4a8_mixed.safetensors`（Kijai，11.7/11.0GiB，ComfyUI 原生量化格式）
  - `text_encoders/Qwen3-VL-32B-Instruct-MiniMax-H3-L0-49-UD-Q2_K_XL.gguf` + `mmproj-BF16.gguf`（nif0，8.9/1.1GiB；mmproj 在 R2V 图片参考时是否必需**待验证**，纯文本 T2V 用不到）
  - `vae/minimax_h3_video_vae_int8_convrot.safetensors`（Kijai 2.95GiB 减半版）+ `vae/minimax_h3_audio_vae_fp32.safetensors`（官方 0.6GiB）
  - `loras/MiniMax-H3-{FL2VA,Ref2VA}-Acc-8Step_pruned_comfy.safetensors`（Kijai 加速 LoRA，各 1.6GiB）

## 脚本

- `download_h3.sh`：hf-mirror 断点续传下载器（重跑只补缺失）。
- `h3_fl2va_baseline.py`：FL2VA 基线首跑（864×480@124帧≈5.2s、8步 turbo、种子 1），内置 nvidia-smi 显存预检（<11.5GB 拒跑）。
- `smoke_test.log`：2026-09-11 冒烟启动记录（H3/GGUF 节点注册、借用路径加载验证通过）。

## H3 关键参数备忘（源自官方模板 video_minimax_h3_t2v / 节点源码）

- 编码器加载：`CLIPLoader`/`CLIPLoaderGGUF` type=**minimax**。
- 分辨率：官方推荐 16:9 全质量 0.98MP=1344×768（面积上限），**避免 1.0MP**（1376×768 超限）；基线用 0.4MP=864×480。
- 帧长：17k+5 网格，EmptyMiniMaxH3LatentAV 自动对齐；**训练范围 124-362 帧（≈5.2-15s）**，短于 124 帧未训练。
- 官方模板默认配 turbo LoRA + BasicScheduler(simple, 4步) + res_multistep；Kijai Acc-8Step 按 8 步用。

## 状态与验收边界

- 2026-09-11：**FL2VA 基线首跑机器验收通过**——`output\video\MiniMax_H3\fl2va_baseline_00001_.mp4`（864×480/124帧/24fps/h264+AAC/5.167s，SHA-256 `b12dec69…`，全流程 360s），档案 `D:\GitHub\ariadne\docs\video-tests\h3-fl2va-baseline-20260911.md`。用户目视验收待做。
- ComfyUI-GGUF 三个本地补丁（勿被上游覆盖）：loader.py qwen3vl mmproj 合并触发 + `qwen3vl_mmproj_key_fix`（deepstack 配置索引→顺序索引、merger/fc 键名）；nodes.py CLIPLoaderGGUF `device` 选项（低显存 mmap 解绑往返会 access violation，编码器暂固定 CPU）。
- 下一步：腾显存（关 Broadcast/壁纸引擎）试编码器回 GPU 提速；Ref2VA 实验（人物+服装+场景+动作参考，Phase 3 核心）。

## FLUX.2 klein 4B（2026-09-11 迁入）

- 权重三件套 12.0GB 从老安装**实体迁入**本机 `models/`（fp8 主模型 4.07GB + qwen_3_4b 编码器 8.04GB + flux2-vae 0.34GB），SHA-256 清单 `models/flux2_klein_weights_sha256.txt`。老安装已无 klein。
- 0.35.0 原生支持（CLIPLoader type=flux2 / klein_te qwen3_4b），零升级。入口：`user/default/workflows/Flux2Klein文生图.json` + 脚本 `flux2_klein_first_run.py`（已指向 8189，取图落本机 output/）。
- 实测（1024²/4步/euler/cfg1）：老安装首测冷 15.1s；本机新进程冷加载 30.6s；热跑 12.1s；显存 9.16GB。成图 `output/flux2_klein_first_test_00001_.png`（与老安装首测字节一致，同种子）。
- 坑：① 这版 CFGGuider 必须接 positive/negative，缺了 400；② mv 迁移时勿落 models 根目录，必须进各自子文件夹否则 value_not_in_list；③ 蒸馏版参数 4 步 cfg1，勿混用官方编辑模板（base 版 20 步 cfg5）的参数；④ 与 H3 换任务时照旧先 POST /free 清显存缓存。

## Krea-2 Turbo（2026-09-11 迁入，同日与 klein 一起）

- 权重三件套 17.4GB 从老安装**实体迁入**本机 `models/`（fp8 主模型 krea2_turbo_fp8_scaled + 编码器 qwen3vl_4b_fp8_scaled + VAE qwen_image_vae），SHA-256 清单 `models/krea2_weights_sha256.txt`。老安装已无任何生图模型，仅剩退役冻结的 Kie Omni 节点。
- 脚本 6 个随迁并全部补丁（8188→8189、输出/工作流路径改 ComfyUI2）：`krea2_first_run.py`（单张）、`krea2_scene_batch.py`（批量）、`krea2_probe.py`、`krea2_reed_backlit/retry/v4real.py`。工作流 `user/default/workflows/Krea2文生图.json`。
- 实测：8189 上 /free 后首跑 84.3s（17.4GB 冷加载），成图正常，显存 9.27GB。
- 注意：klein（9.2GB）与 krea2（9.8GB）同显存互斥，**换模型任务前必须 POST /free**（本文件 H3 节既有约束，对 klein/krea2 同样适用）。
