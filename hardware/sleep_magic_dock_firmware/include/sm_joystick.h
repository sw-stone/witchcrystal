#ifndef __SM_JOYSTICK_H__
#define __SM_JOYSTICK_H__

#include "tuya_cloud_types.h"

#ifdef __cplusplus
extern "C" {
#endif

/**
 * @file app_joystick.h
 * @brief PS2 双轴摇杆驱动（T5AI-Core）
 *
 * 接线（T5AI-Core 44 Pin 排针）：
 *   VRx → P25（TUYA_ADC_NUM_0 / ADC ch1）
 *   VRy → P24（TUYA_ADC_NUM_0 / ADC ch2）
 *   SW  → P20（数字 GPIO，内部上拉，按下为低）
 *   +5V → 3V3，GND → GND
 */

typedef enum {
    JOY_NONE = 0,
    JOY_LEFT,        /* VRx < 2048 - deadzone */
    JOY_RIGHT,       /* VRx > 2048 + deadzone */
    JOY_UP,          /* VRy > 2048 + deadzone */
    JOY_DOWN,        /* VRy < 2048 - deadzone */
    JOY_PRESS,       /* SW 短按（< 800ms）*/
    JOY_LONG_PRESS,  /* SW 长按（≥ 800ms，松开时上报）*/
} joy_event_t;

OPERATE_RET app_joystick_init(void);
joy_event_t app_joystick_poll(void);
uint16_t app_joystick_vrx(void);
uint16_t app_joystick_vry(void);
bool app_joystick_sw_pressed(void);

#ifdef __cplusplus
}
#endif

#endif /* __SM_JOYSTICK_H__ */
