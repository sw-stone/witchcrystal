#ifndef __SM_LED_H__
#define __SM_LED_H__

#include "tuya_cloud_types.h"

#ifdef __cplusplus
extern "C" {
#endif

/* LED 灯效枚举（与状态机 entry 动作对应）*/
typedef enum {
    SM_LED_OFF       = 0,  /* S0 熄灭 */
    SM_LED_GUIDE     = 1,  /* S1 引导态 */
    SM_LED_DOCKED    = 2,  /* S3 入座提示 */
    SM_LED_BREATH    = 3,  /* S4 呼吸 */
    SM_LED_SPEAKING  = 4,  /* S5 说话 */
    SM_LED_SLEEP     = 5,  /* S6 睡眠柔和 */
    SM_LED_TAROT     = 6,  /* S7 塔罗转场 */
    SM_LED_ALARM     = 7,  /* S8 闹钟全亮闪烁 */
    SM_LED_CHEER     = 8,  /* S9 庆祝 */
    SM_LED_MAX
} sm_led_effect_t;

int  sm_led_init(void);
void sm_led_set_effect(sm_led_effect_t e);
void sm_led_set_brightness(uint8_t percent);  /* 0-100 */

#ifdef __cplusplus
}
#endif

#endif
