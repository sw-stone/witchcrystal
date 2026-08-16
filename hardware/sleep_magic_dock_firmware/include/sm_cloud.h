#ifndef __SM_CLOUD_H__
#define __SM_CLOUD_H__

#include "tuya_cloud_types.h"

#ifdef __cplusplus
extern "C" {
#endif

/* DP ID 分配（与云端产品功能定义对齐）*/
#define SM_DP_STATE_CODE      101  /* enum: 当前状态码 S0-S9（手机端视觉同步）*/
#define SM_DP_DOCKED          102  /* bool:  手机在位 */
#define SM_DP_AI_SPEAKING     103  /* bool:  AI 正在说话 */
#define SM_DP_ALARM_SET       104  /* string: 闹钟时间 HH:MM */
#define SM_DP_SLEEP_SUBTYPE   105  /* enum:  当前睡眠子类型 0-4 */
#define SM_DP_VOLUME          106  /* value: 0-100 */
#define SM_DP_WIFI_ONLINE     107  /* bool:  网络在线 */
#define SM_DP_HEARTBEAT       108  /* value: S8 闹钟期间心跳计数 */

int  sm_cloud_init(void);

/* 业务上报接口 */
void sm_cloud_report_state(int state_code);
void sm_cloud_report_docked(bool docked);
void sm_cloud_report_ai_speaking(bool speaking);
void sm_cloud_report_alarm_set(const char *hhmm);
void sm_cloud_report_sleep_subtype(int sub);
void sm_cloud_report_volume(int vol);
void sm_cloud_report_wifi_online(bool online);
void sm_cloud_report_heartbeat(uint32_t seq);

#ifdef __cplusplus
}
#endif

#endif
