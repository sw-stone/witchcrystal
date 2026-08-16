# 屿眠 Sleep Isle · 三路按钮 GPIO 分配（TODO-D1 · Rev.B 定稿）

> 状态：**定稿**。三源交叉验证：官方原理图 T5AI-Core_V101-SCH.pdf（p5 J1/J2 排针定义）+ 丝印图 T5AI-Core_V101-ASM.pdf + SDK 板级头文件。原理图 PDF 已存档于本目录。

## 引脚分配表

| 按钮 | GPIO | 排针物理位 | 触发方式 | 有效电平 | 去抖 | 用途 |
|---|---|---|---|---|---|---|
| 按钮-前（引导） | GPIO_2 | **J2 pin 20** | 边沿（下降沿中断） | 低 | 50 ms | S0→S1 进入首次引导 |
| 按钮-后（强制待机） | GPIO_3 | **J1 pin 16** | 边沿（下降沿中断） | 低 | 50 ms | 任意态→S0，全局最高优先级 |
| 按钮-下（在位检测） | GPIO_4 | **J1 pin 21** | **电平**（非边沿） | 压下=低=在座，弹起=高=离座 | 100 ms | 手机在位检测，S3 进入/S0 退出锚点 |

公共端接地：J1 pin 15/22、J2 pin 2/21 任一。

配合既有资源：板载用户按钮 P29（可复用为按钮-前备份）、用户 LED P9。

## 依据链（三源交叉验证）

1. **原理图**：T5AI-Core_V101-SCH.pdf 第 5 页 J1/J2 排针定义（GPIO→物理针脚定位）。
2. `usr_gpio_cfg.h`：GPIO2/3/4 均为 `SECOND_FUNC_DISABLE` + 默认 `PULL_UP_EN` —— 空闲引脚且免外部上拉电阻。
3. `gpio_map.h`：BK7258 全部 GPIO 支持中断（边沿+电平）。

## 已避开的占用引脚

| 引脚 | 占用 |
|---|---|
| 10 / 11 | UART0（烧录+日志双路串口） |
| 28 | I2S_MCLK（音频） |
| 39 | 功放 EN |
| 9 | 用户 LED P9 |
| 29 | 板载用户按钮 P29 |
| 20 / 24 / 25 | PS2 摇杆（VRx/VRy/SW，见 README） |
| **26 / 27** | **RF 禁区，禁止使用**（历史占位值曾用 P26，已修复） |
| 29-38 | JPEG/DVP 区域 |
| J2.3 / J2.4 | USB |
| — | Flash/PSRAM 专用引脚（见 BSP） |

## 接线文字图

```
轻触按钮×2（前/后）          手机底座微动开关(下)
 ┌──[BTN前]── GPIO_2          ┌──[SW下]── GPIO_4
 │                            │
 GND                          GND
（内部上拉，另一端接地；按下拉低） （内部上拉；手机放置压下=低=在座）

 ┌──[BTN后]── GPIO_3
 │
 GND
```

## 风险备注

1. ~~物理引脚序号待 SCH 确认~~ → **Rev.B 已定稿**：前=J2 pin20 / 后=J1 pin16 / 下=J1 pin21，原理图 PDF 已存档本目录。
2. **SPI1 冲突预案**：TODO-D4 已决策 MVP 纯 H5 缓存，SPI1 冲突风险解除；未来若启用 SPI Flash/SD 再重评估。
3. **深睡唤醒**：S0/S4 低功耗模式下若需按钮唤醒，GPIO 需重配 KEEP_INPUT 属性，见 tkl_gpio 低功耗章节。
4. **历史占位值修复记录**：sm_button.c 曾用 BACK=26（RF 禁区）/ DOWN=28（I2S_MCLK）危险值，Rev.B 起修正为 Kconfig 默认 3/4，`tuya_kconfig.h` 已确认 BTN_BACK_GPIO=3 / BTN_DOWN_GPIO=4，新 bin 已产出（`.build/bin/sleep_magic_dock_QIO_1.0.0.bin` 等）。

## 相关联决策（同轮定稿）

- **TODO-D2**：S3→S4 激活 = 固定延时 3s（Kconfig 可调）。
- **TODO-D4**：外部存储 = MVP 纯 H5 缓存，断网白噪声兜底走算法生成。
- **TODO-D5**：LED = MVP 仅板载 P9，预留 I2C RGB 扩展路径（GPIO_0/1）。
