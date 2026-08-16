#ifndef __SM_BUTTON_H__
#define __SM_BUTTON_H__

#include "tuya_cloud_types.h"
#include "sm_state_machine.h"

#ifdef __cplusplus
extern "C" {
#endif

/**
 * @brief 初始化 3 路按钮：
 *   - 按钮-前：P29（板级已注册为 "ai_chat_button"），通过 tdl_button 订阅
 *   - 按钮-后：CONFIG_BTN_BACK_GPIO（44 Pin 扩展），GPIO IRQ + 软件去抖
 *   - 按钮-下：CONFIG_BTN_DOWN_GPIO（44 Pin 扩展），电平触发，复用手机在位检测
 *
 * TODO-1（需硬件确认）：BTN_BACK_GPIO / BTN_DOWN_GPIO 引脚请按 T5AI-Core_V101-SCH
 *                       原理图确认后替换 Kconfig 默认值。
 */
int  sm_button_init(void);

/** 启动按钮扫描任务（在 tuya_app_main 内调用）*/
int  sm_button_start(void);

/** 查询按钮-下当前电平（true=压下，手机在座）*/
bool sm_button_down_is_pressed(void);

#ifdef __cplusplus
}
#endif

#endif
