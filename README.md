# pocket-prophet-dashboard

给"口袋先知"墨水屏做的功能扩展：一个本地 Web 服务，让这块 200×200 的小屏幕显示自定义内容——**摇一卦**、看天气、看股票行情、看今日要闻、看 Claude Code 的 token 消耗。全部通过设备官方已经暴露的能力实现，不逆向、不刷机（详见下方「定位」）。

<p align="center">
<img src="docs/img/divination.png" width="140"> <img src="docs/img/weather.png" width="140"> <img src="docs/img/stocks.png" width="140"> <img src="docs/img/news.png" width="140"> <img src="docs/img/usage.png" width="140">
</p>

---

## 快速开始

```bash
git clone https://github.com/BruceLanLan/pocket-prophet-dashboard.git
cd pocket-prophet-dashboard
pip install -r requirements.txt

cp config.example.json config.json
# 编辑 config.json：填入设备的局域网 IP（在设备上打开"更换壁纸"界面时
# 能看到），MAC 地址可选（填了的话 IP 变了会自动找回）

python3 app.py
```

启动后访问 `http://<这台电脑的局域网IP>:5151`（同一 WiFi 下手机也能打开）。

**用之前有一件事必须知道：设备平时不联网。** 它只在你手动打开设备上的"更换壁纸"界面时才会加入局域网，退出界面就立刻断开（实测确认，日志见 [`docs/evidence/`](docs/evidence/)）。所以每次要推内容上去，流程是：

1. 在设备上打开"更换壁纸"界面
2. 打开这个 Web 页面，点你想要的功能
3. 看设备屏幕

页面顶部的状态点会告诉你设备现在在不在线；不在线时点按钮会给出"请先打开更换壁纸界面"的提示，不会报错崩溃。

---

## 功能

| 功能 | 说明 |
|---|---|
| 🔮 **摇卦** | 三枚铜钱法起六爻，服务端用密码学安全随机数（`secrets`，不是 `random`）真实抛掷。给出本卦、变卦（如有动爻）、和一句判断 |
| 🌤️ **天气** | 数据源 [wttr.in](https://wttr.in)，城市在设置页里改 |
| 📈 **行情** | 数据源 Yahoo Finance 公开接口，股票清单在设置页里改，每只股票配一条当日分时走势线 |
| 📰 **要闻** | 数据源今日头条热榜 |
| 📊 **Token 用量** | 解析本机 Claude Code 的本地转录文件，展示今日 token 消耗、近 5 小时窗口、按模型拆分、近似成本估算。**这不是官方订阅额度百分比**——那个数据本地拿不到，这里给的是本地转录统计出的用量，别混着看 |

摇卦是"推了就看"的一次性动作；天气/行情/新闻/用量四页支持先"预览"（只调用转换接口生成预览图，**不会**真的推给设备）再决定要不要"推送"。

---

## 设置页

访问 `/settings` 可以改：

- 设备 IP / MAC
- 天气城市（默认深圳）
- 股票清单（默认 `AAPL`、`NVDA`，逗号分隔）

改完点保存即可，不需要重启服务。

---

## 项目结构

```
pocket-prophet-dashboard/
  app.py                    # Flask 服务：路由 + 页面注册表
  config.py / config.json   # 运行时配置读写
  device.py                 # 设备通信：云端图片转换 + 局域网推送
  providers/                # 各功能的数据抓取（天气/行情/新闻/用量/起卦）
  renderer/                 # 各功能的 200×200 图像渲染
  templates/                # 网页（首页 + 设置页）
  history/                  # 每次推送前的源图备份（设备没有读回接口，这是唯一的回滚依据）
  scripts/                  # 早期设备探测脚本，开发调试用，不是运行本项目所必需
  docs/                     # 见下方文档索引
```

---

## 文档索引

这个 README 只讲"怎么用"。设备本身的接口细节、每一个实测数字的来源、开发过程中的判断和取舍，都在这里：

| 文档 | 内容 |
|---|---|
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | 设备接口全貌、云端 API 契约、面板规格、负载预算——全部标注了实测依据，不是推测 |
| [`docs/PLAN.md`](docs/PLAN.md) | 分阶段开发记录（Phase 1–5 已完成，见下方状态）；Phase 0 待验证 |
| [`docs/PLAN-v2.md`](docs/PLAN-v2.md) | 新一轮深化计划：自动推送、奇门遁甲、各页视觉与信息密度优化 |
| [`docs/OPTIONS.md`](docs/OPTIONS.md) | 蓝牙 / NFC / USB / 固件等其他改造路径的探索记录（多数已证实是死路，存档备查，不是待办） |
| [`docs/evidence/`](docs/evidence/) | 设备联网时机的原始实测日志 |

## 项目状态

- ✅ Phase 1 推送管线骨架
- ✅ Phase 2 摇卦
- ✅ Phase 3 配置界面
- ✅ Phase 4 天气 / 行情 / 新闻
- ✅ Phase 5 Token 用量
- ⏳ Phase 0 显示语义验证——推上去的图能不能作为待机画面持续显示在屏幕上，还没测。不影响以上功能使用，只影响"离网后内容还在不在屏幕上"这一点的心理预期；细节见 `docs/PLAN.md`

## 定位：扩展，不是破解

**本项目只使用官方能力，不做任何逆向或破解。**

- ✅ 用：官方的图片上传接口（`/wallpaper`）、官方的云端图片转换 API、官方的蓝牙翻页 HID 能力
- ❌ 不做：逆向设备私有编码格式、dump 或改写固件、拆机、绕过任何鉴权

开发过程中确实探过这些路（记录在 `docs/OPTIONS.md`），但全部划在范围之外——设备联网受限这类约束，就在官方能力内接受它、绕过它，而不是靠破解去解除它。

## 免责声明

本项目与"口袋先知"厂商无任何关联，纯属个人对自有设备的研究和自用改造。所有交互都通过设备在局域网内暴露的公开接口，以及厂商本身对外提供的云端转换接口完成，不涉及破解设备固件、绕过身份鉴权或访问他人设备。

## License

MIT，见 [`LICENSE`](LICENSE)。
