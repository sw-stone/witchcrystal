/**
 * @file sm_alarm.c
 * @brief 闹钟：基于系统时间 + 软件定时器轮询（每 1s 检查）
 *   - 全局抢占：到点立即触发 SM_EVT_ALARM_TRIGGER
 *   - 支持 HH:MM 设置/取消
 */

#include "sm_alarm.h"
#include "sm_state_machine.h"
#include "tal_api.h"
#include "tal_sw_timer.h"
#include "tuya_log.h"
#include <time.h>

#define TAG "[ALARM] "

static TIMER_ID s_poll_timer = NULL;
static bool      s_set      = false;
static uint8_t   s_hour     = 0;
static uint8_t   s_minute   = 0;
static bool      s_inited   = false;
static bool      s_fired    = false;  /* 今天已触发过 */

static void poll_cb(TIMER_ID tid, void *arg)
{
    (void)tid; (void)arg;
    if (!s_set) return;

    /* 取系统时间（UNIX 时间）*/
    time_t t = tal_time_get_posix();
    struct tm *lt = localtime(&t);
    if (!lt) return;

    /* 跨天重置 fired */
    if (s_fired && (lt->tm_hour != s_hour || lt->tm_min != s_minute)) {
        s_fired = false;
    }

    if (!s_fired && lt->tm_hour == s_hour && lt->tm_min == s_minute) {
        s_fired = true;
        PR_INFO(TAG "fire! %02d:%02d", s_hour, s_minute);
        sm_event_t e = { SM_EVT_ALARM_TRIGGER, 0, NULL };
        sm_fsm_dispatch(&e);
    }
}

int sm_alarm_init(void)
{
    if (s_inited) return 0;
    tal_sw_timer_create(poll_cb, NULL, &s_poll_timer);
    tal_sw_timer_start(s_poll_timer, 1000, TAL_TIMER_CYCLE);  /* 1s 轮询 */
    s_inited = true;
    PR_INFO(TAG "init (1s poll timer started)");
    return 0;
}

int sm_alarm_set(const char *hhmm)
{
    if (hhmm == NULL || strlen(hhmm) < 4) return -1;
    /* 解析 "HH:MM" */
    int h, m;
    if (sscanf(hhmm, "%d:%d", &h, &m) != 2) return -1;
    if (h < 0 || h > 23 || m < 0 || m > 59) return -1;
    s_hour = (uint8_t)h;
    s_minute = (uint8_t)m;
    s_set = true;
    s_fired = false;
    PR_INFO(TAG "set to %02d:%02d", s_hour, s_minute);
    return 0;
}

int sm_alarm_cancel(void)
{
    s_set = false;
    PR_INFO(TAG "cancelled");
    return 0;
}

int sm_alarm_stop_ringing(void)
{
    /* 仅停止响铃，不取消设置（明日仍会响）*/
    s_fired = true;  /* 标记今天已触发 */
    PR_INFO(TAG "stop ringing");
    return 0;
}

bool sm_alarm_is_set(void)
{
    return s_set;
}
