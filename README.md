# pocket-prophet-dashboard

给"口袋先知"墨水屏做**功能扩展**的项目。用设备官方已经暴露的能力，把它用到官方没明说、但完全能干的新场景。核心是让它显示自定义信息：天气、股票、新闻、六爻卦象、Claude Code token 消耗。

## 定位：扩展，不是破解

**本项目只使用官方能力，不做任何逆向或破解。** 这条边界是刚性的，执行时不得越界：

- ✅ **用**：官方的图片上传接口（`/wallpaper`）、官方的云端图片转换 API（厂商自己对外提供的）、官方的蓝牙翻页 HID 能力。
- ❌ **不做**：逆向 `COMPRESS_ARRAY_V2` 编码格式、dump 或改写固件、拆机、绕过任何鉴权。

设备探索过程中确实摸到过这些破解路线（记录在 `docs/OPTIONS.md`），但它们**全部划在范围之外**。设备联网受限等约束，就在官方能力内接受它、绕过它，而不是靠破解去解除它。

## ⚠️ 先读这条：设备不常驻联网

实测确认，**这台设备只在用户手动停留于"更换壁纸"界面时才加入局域网**，退出该界面后在网络层与应用层同时立即不可达，且 25 分钟内不会自行唤醒（[对照日志](docs/evidence/)）。

因此**不存在"后台定时自动推送"这种可能**，本项目是**用户触发式**的：你在设备上打开那个界面，然后从浏览器点一下把内容推上去。

这条约束对各功能的影响并不均等——摇卦完好无损（它本来就是主动求问的仪式），而天气/行情/新闻这类"瞥一眼即最新"的环境化功能则被削弱。削弱到什么程度，取决于 `docs/PLAN.md` 的 Phase 0 验证结果（推上去的图能否作为待机画面留在屏幕上）。**五个页面都会做**，Phase 0 决定的是体验等级，不是做不做。

## 免责声明

本项目与"口袋先知"厂商无任何关联，纯属个人对自有设备的研究和自用改造。所有交互都通过设备在局域网内暴露的公开接口，以及厂商本身对外提供的云端转换接口完成，不涉及破解设备固件、绕过身份鉴权或访问他人设备。

## 文档

| 文档 | 内容 |
|---|---|
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | 整体架构与全部已确认事实（自包含，实测依据齐全） |
| [`docs/PLAN.md`](docs/PLAN.md) | 分阶段开发计划，每步带验证点，按风险排序 |
| [`docs/OPTIONS.md`](docs/OPTIONS.md) | 其他通道的探索记录与结论（BLE / USB 已探明为死路，NFC / 固件为范围外备忘） |
| [`docs/evidence/`](docs/evidence/) | 原始实测日志，两份联网探测的对照 |

**执行开发前请先读 ARCHITECTURE.md 与 PLAN.md**，尤其是 PLAN.md 的 Phase 0——它是阻断性的地基验证，裁定各页面的实际体验等级，且需要付出一次不可逆的壁纸覆盖代价（用户已同意，无需再次确认）。

## 现状：已确认的接口

### 设备本地接口（无鉴权，配网后设备在你的局域网内直接暴露）

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/` | 官方"更换壁纸"网页 |
| GET | `/wallpaper/info` | 返回 `{has_custom, length, capacity, max_upload}`。数值单位是 base64 字符数，不是解码后的字节数 |
| POST | `/wallpaper` | body 直接是 `COMPRESS_ARRAY_V2` 的 base64 字符串本身（不需要解码），`Content-Type: application/octet-stream`。**会立即覆盖当前壁纸，且没有读回接口 —— 覆盖前请自行保留原图** |
| DELETE | `/wallpaper` | 恢复出厂内建壁纸（不是恢复你上一次的自定义图） |

### 云端转换接口

```
POST https://dot.mindreset.tech/api/authV2/device/render/convert
Content-Type: application/json

{
  "series": "rand",
  "model": "rand_0",
  "edition": 1,
  "image": "data:image/png;base64,....",
  "colorLevels": 4,
  "ditherType": "DIFFUSION",
  "ditherKernel": "THRESHOLD"
}
```

`ditherKernel` 可选值（照抄官方网页的下拉选项）：`FLOYD_STEINBERG` `THRESHOLD` `ATKINSON` `SIERRA2` `BURKES` `STUCKI` `JARVIS_JUDICE_NINKE` `DIFFUSION_ROW` `DIFFUSION_COLUMN` `DIFFUSION_2D`。

返回：

```json
{
  "COMPRESS_ARRAY_V2": "设备专用编码，base64字符串，原样POST给设备即可",
  "COMPRESS_RENDER": "base64 PNG，仅供预览"
}
```

### 面板规格（已用 `COMPRESS_RENDER` 解码实测确认，非猜测）

- 分辨率 **200×200**
- **4 级灰阶**：`{0, 85, 170, 255}`
- `max_upload` 等字段单位是 base64 字符数：200×200×2bit/8 = 10000 字节解码数据 ≈ 13.3K base64 字符，与实测 `max_upload:14336` 量级吻合

### 负载预算与可读性（实测）

扁平化图文设计远在 14336 上限之内，负载不是约束：天气页 2792、行情页 3236、新闻页 4440（均为 `THRESHOLD` 核）。`THRESHOLD` 比 `FLOYD_STEINBERG` 省约 30%，只有照片类渐变会逼近上限（抖动后 9716）。

13px 中文可读、14px 舒适，每行约 14 个汉字；一屏可放"标题 + 5 行数据 + 走势线"或"标题 + 8 行文字"。完整数据见 [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)。

### 接口面已探明

对 23 个常见路径（`/api` `/status` `/battery` `/sensor` `/event` `/shake` `/nfc` `/ota` 等）逐一探测，全部 302 跳转到 `http://192.168.4.1/`（ESP32 SoftAP 兜底）。**设备只有上表四个接口，在 WiFi 通道上是只写的**——拿不到电量、按键、摇动或 NFC 事件。

设备确实能通过**蓝牙 HID** 向 Mac 发按键（见 `docs/ARCHITECTURE.md` §1.6），但蓝牙与 WiFi 分属两个互斥的设备界面，无法一边发信号一边收推送。所以起卦仍只能由 Web 界面触发、设备负责显示。

## 待验证（范围内）

- **推送的图是否作为待机画面留在屏幕上**，以及设备停在"更换壁纸"界面时屏幕显示的是什么。由 PLAN.md 的 Phase 0 一次观察回答，决定各页面的实际体验等级。

## 已知但不做（范围外）

`COMPRESS_ARRAY_V2` 的字节编码规则尚未破解（观察到疑似行程编码 + 一段疑似校验/签名的尾部字节）。**本项目不逆向它**——直接使用厂商云端的转换 API 即可，那本就是官方对外提供的能力。相关观察记录在 `docs/OPTIONS.md`，仅作存档。

## scripts/

- `probe_device.py <device-ip>` — 查询设备当前壁纸状态
- `gen_test_images.py` — 生成一批 200×200 测试图（纯色 / 单像素标记 / 棋盘格），落盘到 `out/test_images.json`
- `call_convert.py` — 对每张测试图调用云端 convert API，把原始 `COMPRESS_ARRAY_V2` 落盘到 `out/full_arrays.json`

```bash
pip install -r requirements.txt
python3 scripts/probe_device.py 192.168.x.x
python3 scripts/gen_test_images.py
python3 scripts/call_convert.py
```

## Roadmap

详细分阶段计划见 [`docs/PLAN.md`](docs/PLAN.md)。

- [ ] **Phase 0** 显示语义验证（阻断性：推上去的图会不会作为待机画面留在屏幕上，裁定各页面的体验等级）
- [ ] **Phase 1** 推送管线骨架（探活 / 转换 / 推送 / 负载校验 / IP 漂移自愈）
- [ ] **Phase 2** 六爻起卦（排在前面是因为它不依赖外部数据源，最快能验证管线）
- [ ] **Phase 3** Web 配置界面
- [ ] **Phase 4** 天气 / 行情 / 新闻页
- [ ] **Phase 5** Claude Code token 消耗页
- [ ] （范围外）逆向 `COMPRESS_ARRAY_V2` 编码器以脱离厂商云端
