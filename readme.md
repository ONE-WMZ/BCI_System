# BCI System

基于 Python、PsychoPy 和 LSL 的脑机接口系统，目前支持 SSVEP 刺激预览、脑电采集、CCA 离线分析与实时方向控制，可对接游戏或小车 HTTP 接口，后续将扩展 MI（运动想象）功能。

## 环境与启动

使用 Python 3.10，需支持 Tkinter，并安装以下依赖：

```bash
pip install psychopy pylsl numpy scipy scikit-learn screeninfo opencv-python websockets aiohttp flask
python App_.py
```

采集与实时识别前，需启动设备的 LSL 脑电流。当前分析代码按 **250 Hz** 处理，默认通道索引为 `[6, 7, 8, 9, 13]`，使用其他设备时需调整代码。

## 使用流程

1. 填写受试者信息，扫描并选择 LSL 设备。
2. 在 Data Collect 页选择数据目录、任务和刺激时长，可先预览刺激，再开始采集。
3. 在 Analysis 页选择数据目录与 **CCA**，设置窗口和步长，查看准确率及自动计算的阈值。
4. 在 Realtime 页选择任务、CCA 和阈值；需要发送控制指令时，加载 Control API JSON。

- **SSVEP**：四方向闪烁刺激；**PD-SSVEP**：叠加摄像头或 WebSocket 视频画面。
- PD-SSVEP 的 Frame API 使用 `ws://` 或 `wss://` 地址；勾选摄像头后填写设备索引。
- FBCCA、MI 尚未完整实现。

## 本地联调

```bash
python Server-game/server.py
python Server-webtest/server.py
```

两个服务可按需独立启动：

| 服务 | 页面 | Control API JSON |
| --- | --- | --- |
| 游戏 | http://127.0.0.1:8765 | `Server-game/API.json` |
| HTTP 指令测试 | http://127.0.0.1:5000 | `Server-webtest/API.json` |

游戏画面地址：`ws://127.0.0.1:8766/ws/frame?role=viewer`。小车接口配置见 `API_1.json`、`API_2.json`，使用前按实际设备修改地址和参数。

## 数据与目录

采集数据直接保存到所选目录，`.npy` 数组形状为 `(采样点数, 通道数)`：

```text
所选数据目录/
├── +.npy                  # 静息数据
├── up.npy / down.npy      # 上、下方向
├── left.npy / right.npy   # 左、右方向
├── events.csv             # 采集事件
├── person_info.json       # 受试者信息与刺激频率
└── realtime/              # 每次成功识别的脑电片段（时间戳_序号_方向.npy）
```

`App_.py` 为入口，`Task_/` 包含预览、采集、分析和实时任务，`Unit_/` 包含 GUI、LSL、刺激、CCA 及接口通信模块。
