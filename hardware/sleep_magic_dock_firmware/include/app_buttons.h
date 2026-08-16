/**
 * @file app_buttons.h
 * @brief 屿眠 Sleep Isle 三路按钮 GPIO 定义（TODO-D1 已确认 · 原理图定稿版）
 *
 * 分配依据（三源交叉验证）：
 *  - 官方原理图 T5AI-Core_V101-SCH.pdf p5：J1/J2 排针物理引脚定位
 *  - usr_gpio_cfg.h：GPIO2/3/4 SECOND_FUNC_DISABLE + PULL_UP_EN（空闲+默认上拉）
 *  - gpio_map.h：全 GPIO 支持中断，无第二功能锁定
 *
 * 已避开：UART0(10/11)、I2S_MCLK(28)、功放EN(39)、LED(9)、板载按钮(29)、
 *         摇杆(20/24/25)、RF 禁区(26/27)、JPEG/DVP(29-38)、USB(J2.3/4)
 *
 * 物理接线：
 *  - 按钮-前 → J2 pin 20 (P2)
 *  - 按钮-后 → J1 pin 16 (P3)
 *  - 按钮-下 → J1 pin 21 (P4)
 *  - 公共端 → GND（J1 15/22、J2 2/21 任一）
 */

#ifndef APP_BUTTONS_H
#define APP_BUTTONS_H

/* 按钮-前：进入首次引导（S0→S1）。边沿触发，下降沿有效。物理位：J2 pin 20 */
#define APP_BTN_FRONT_GPIO      (2)     /* GPIO_2，内部上拉，按下拉低 */
#define APP_BTN_FRONT_DEBOUNCE  (50)    /* ms */

/* 按钮-后：强制回待机（任意态→S0），全局最高优先级事件。边沿触发，下降沿有效。物理位：J1 pin 16 */
#define APP_BTN_BACK_GPIO       (3)     /* GPIO_3，内部上拉，按下拉低 */
#define APP_BTN_BACK_DEBOUNCE   (50)    /* ms */

/* 按钮-下：手机在位检测（S3 进入 / S0 退出锚点）。电平触发，非边沿。物理位：J1 pin 21 */
#define APP_BTN_DOWN_GPIO       (4)     /* GPIO_4，内部上拉 */
#define APP_BTN_DOWN_DEBOUNCE   (100)   /* ms */
/* 压下=低=手机在座；弹起=高=手机离座（立即回待机） */
#define APP_BTN_DOWN_ACTIVE_LVL (0)

#endif /* APP_BUTTONS_H */
