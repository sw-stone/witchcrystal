#ifndef __SM_STATE_SYNC_H__
#define __SM_STATE_SYNC_H__

#include "tuya_cloud_types.h"
#include "sm_state_machine.h"

#ifdef __cplusplus
extern "C" {
#endif

/**
 * @brief 状态码同步：固件 FSM 状态 → 涂鸦云 DP → 手机 H5 视觉切换
 *  - 切换误差目标 < 500ms
 *  - S8 闹钟期间周期心跳保活
 */
int  sm_sync_init(void);

/** 立即同步状态码到云端（SM_SYNC_*）*/
void sm_sync_send(sm_sync_code_t code);

/** 启动 S8 心跳（每 CONFIG_STATE_SYNC_HEARTBEAT_MS 一次）*/
void sm_sync_start_heartbeat(void);

/** 停止心跳 */
void sm_sync_stop_heartbeat(void);

#ifdef __cplusplus
}
#endif

#endif
