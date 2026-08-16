#ifndef __SM_ALARM_H__
#define __SM_ALARM_H__

#include "tuya_cloud_types.h"
#include "sm_state_machine.h"

#ifdef __cplusplus
extern "C" {
#endif

/**
 * @brief 闹钟模块：基于系统 RTC + 软件定时器轮询
 *  - 全局抢占：到点立即触发 SM_EVT_ALARM_TRIGGER
 *  - 支持设置/取消
 */
int  sm_alarm_init(void);

/** 设置闹钟时刻 HH:MM，立即生效 */
int  sm_alarm_set(const char *hhmm);

/** 取消闹钟（不会影响正在响铃）*/
int  sm_alarm_cancel(void);

/** 停止正在响铃（响铃期间由 FSM S8→S9 时调用）*/
int  sm_alarm_stop_ringing(void);

/** 闹钟是否已设置 */
bool sm_alarm_is_set(void);

#ifdef __cplusplus
}
#endif

#endif
