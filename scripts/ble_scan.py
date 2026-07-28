"""被动扫描 BLE 广播，查找口袋先知是否存在不依赖 WiFi 窗口的常驻通道。

纯监听：不连接、不配对、不写入任何数据，对周围设备无影响。

用法：
    python3 scripts/ble_scan.py            # 扫描 20 秒
    python3 scripts/ble_scan.py 60         # 扫描 60 秒

首次运行 macOS 会弹出蓝牙权限请求，必须允许。若提示
"Bluetooth device is turned off" 但系统蓝牙明明开着，那就是权限被拒，
去「系统设置 → 隐私与安全性 → 蓝牙」把当前终端 App 勾上。

依赖：pip3 install --user bleak
"""
import asyncio
import sys

try:
    from bleak import BleakScanner
except ImportError:
    sys.exit("缺少依赖，请先运行：pip3 install --user bleak")

# 设备的 WiFi 侧 MAC，仅作参考。ESP32 的 BLE MAC 通常与 WiFi MAC
# 相差一个小偏移（常见 +1/+2），所以留意接近的地址。
# macOS 出于隐私不暴露 BLE 设备的真实 MAC，只给随机 UUID，
# 因此主要靠名称、厂商数据和信号强度来辨认。
WIFI_MAC = "58:2a:bd:0a:98:c8"

KEYWORDS = ["rand", "pocket", "prophet", "ink", "epd", "mind", "dot", "先知", "esp"]

# 常见的 ESP32 自定义串口服务，若出现说明很可能有可写数据通道
NUS_UUID = "6e400001-b5a3-f393-e0a9-e50e24dcca9e"


async def main():
    seconds = int(sys.argv[1]) if len(sys.argv) > 1 else 20
    print(f"被动扫描 BLE 广播 {seconds} 秒（不连接、不写入）...\n")

    found = {}

    def on_found(device, adv):
        found.setdefault(device.address, (device, adv))

    scanner = BleakScanner(detection_callback=on_found)
    try:
        await scanner.start()
    except Exception as e:
        if "turned off" in str(e).lower():
            sys.exit(
                "扫描失败：CoreBluetooth 报告蓝牙关闭。\n"
                "如果系统蓝牙其实是开着的，那这是权限问题——\n"
                "去「系统设置 → 隐私与安全性 → 蓝牙」为当前终端 App 授权后重试。"
            )
        raise
    await asyncio.sleep(seconds)
    await scanner.stop()

    if not found:
        print("没有扫到任何 BLE 广播。若确认周围有蓝牙设备，可能仍是权限问题。")
        return

    print(f"共发现 {len(found)} 个 BLE 设备，按信号强度排序：\n")
    ranked = sorted(found.values(), key=lambda x: -(x[1].rssi or -999))
    suspects = []

    for device, adv in ranked:
        name = device.name or adv.local_name or "(无名称)"
        print(f"  {name:<26} RSSI={adv.rssi:>5}  {device.address}")
        if adv.manufacturer_data:
            ids = [hex(k) for k in adv.manufacturer_data]
            print(f"       厂商ID: {', '.join(ids)}")
        for uuid in (adv.service_uuids or [])[:4]:
            marker = "  ← Nordic UART，可能是数据通道！" if uuid.lower() == NUS_UUID else ""
            print(f"       服务: {uuid}{marker}")

        low = name.lower()
        if any(k in low for k in KEYWORDS) or (adv.service_uuids and
               NUS_UUID in [u.lower() for u in adv.service_uuids]):
            suspects.append((name, device.address, adv.rssi))

    print("\n" + "=" * 56)
    if suspects:
        print("可疑目标（名称命中关键词或暴露了自定义串口服务）：")
        for name, addr, rssi in suspects:
            print(f"  {name}  RSSI={rssi}  {addr}")
        print("\n下一步：把设备拿到 Mac 旁边再扫一次，信号最强且距离相关的那个就是它。")
    else:
        print("没有明显命中。判别方法：把设备紧贴 Mac 扫一次、再拿远扫一次，")
        print("RSSI 变化最剧烈的那个就是目标设备。")
    print("=" * 56)


asyncio.run(main())
