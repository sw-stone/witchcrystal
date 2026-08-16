/**
 * @file sm_state_sync.c
 * @brief 状态码同步：FSM 状态 → 涂鸦云 DP → 手机 H5 视觉切换
 *   - 切换目标误差 < 500ms（直接 DP 上报，无需等待确认）
 *   - S8 闹钟期间周期心跳保活
 */

#include "sm_state_sync.h"
#include "sm_cloud.h"
#include "tal_api.h"
#include "tal_sw_timer.h"
#include "tuya_log.h"

#define TAG "[SYNC] "

#ifndef CONFIG_STATE_SYNC_HEARTBEAT_MS
#define CONFIG_STATE_SYNC_HEARTBEAT_MS 5000
#endif

static TIMER_ID s_heartbeat_timer = NULL;
static uint32_t s_heartbeat_seq   = 0;
static bool     s_inited          = false;

static void heartbeat_cb(TIMER_ID tid, void *arg)
{
    (void)tid; (void)arg;
    s_heartbeat_seq++;
    sm_cloud_report_heartbeat(s_heartbeat_seq);
    PR_DEBUG(TAG "heartbeat #%u", s_heartbeat_seq);
}

int sm_sync_init(void)
{
    if (s_inited) return 0;
    tal_sw_timer_create(heartbeat_cb, NULL, &s_heartbeat_timer);
    s_inited = true;
    PR_INFO(TAG "init");
    return 0;
}

void sm_sync_send(sm_sync_code_t code)
{
    PR_INFO(TAG "state code -> %d", (int)code);
    sm_cloud_report_state((int)code);

    /* AI 说话态同时上报 DP 103 */
    if (code == SM_SYNC_AI_SPEAKING) {
        sm_cloud_report_ai_speaking(true);
    } else if (code == SM_SYNC_AI_IDLE_LOOP || code == SM_SYNC_BLACK) {
        sm_cloud_report_ai_speaking(false);
    }

    /* 入座态上报 DP 102 */
    if (code == SM_SYNC_LOCKED_VIDEO) {
        sm_cloud_report_docked(true);
    } else if (code == SM_SYNC_BLACK) {
        sm_cloud_report_docked(false);
    }
}

void sm_sync_start_heartbeat(void)
{
    s_heartbeat_seq = 0;
    tal_sw_timer_start(s_heartbeat_timer, CONFIG_STATE_SYNC_HEARTBEAT_MS, TAL_TIMER_CYCLE);
    PR_INFO(TAG "heartbeat started (every %dms)", CONFIG_STATE_SYNC_HEARTBEAT_MS);
}

void sm_sync_stop_heartbeat(void)
{
    tal_sw_timer_stop(s_heartbeat_timer);
    PR_INFO(TAG "heartbeat stopped");
}
