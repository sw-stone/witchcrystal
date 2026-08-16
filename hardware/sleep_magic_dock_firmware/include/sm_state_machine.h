#ifndef __SM_STATE_MACHINE_H__
#define __SM_STATE_MACHINE_H__

#include "tuya_cloud_types.h"

#ifdef __cplusplus
extern "C" {
#endif

/* =========================================================================
 * 9+1 状态机：S0-S9
 * 每个状态有明确的 entry/exit 动作，由显式状态表驱动（禁止 if-else 散落）
 * ========================================================================= */
typedef enum {
    SM_STATE_STANDBY          = 0,  /* S0  待机 */
    SM_STATE_FIRST_USE        = 1,  /* S1  首次使用 */
    SM_STATE_FORCE_STANDBY    = 2,  /* S2  强制回待机（瞬态）*/
    SM_STATE_DOCKED           = 3,  /* S3  手机入座 */
    SM_STATE_AI_STANDBY       = 4,  /* S4  AI 待机 */
    SM_STATE_AI_SPEAKING      = 5,  /* S5  AI 主动说话 */
    SM_STATE_SLEEP_EXPERIENCE = 6,  /* S6  睡眠体验（冥想/白噪音/呼吸/塔罗）*/
    SM_STATE_TAROT_DRAW       = 7,  /* S7  塔罗抽卡 */
    SM_STATE_ALARM_RINGING    = 8,  /* S8  闹钟响起（全局抢占）*/
    SM_STATE_WAKEUP_DONE      = 9,  /* S9  起床完成（瞬态）*/
    SM_STATE_MAX
} sm_state_t;

/* 睡眠体验子类型（S6 内部）*/
typedef enum {
    SM_SLEEP_NONE      = 0,
    SM_SLEEP_MEDITATION,
    SM_SLEEP_WHITENOISE,
    SM_SLEEP_BREATHING,
    SM_SLEEP_TAROT
} sm_sleep_subtype_t;

/* =========================================================================
 * 输入事件：按钮、语音、闹钟、云端指令、AI 状态回调
 * ========================================================================= */
typedef enum {
    SM_EVT_NONE = 0,
    /* 按钮事件（去抖后）*/
    SM_EVT_BTN_FRONT,          /* 按钮-前 短按 */
    SM_EVT_BTN_BACK,           /* 按钮-后 短按（全局最高优先级）*/
    SM_EVT_BTN_DOWN_PRESSED,   /* 按钮-下 被压下（手机入座）*/
    SM_EVT_BTN_DOWN_RELEASED,  /* 按钮-下 弹起（手机离座）*/
    /* 语音事件 */
    SM_EVT_VOICE_VAD_DETECTED, /* VAD 检测到用户语音 */
    SM_EVT_AI_TTS_START,       /* TTS 播报开始 */
    SM_EVT_AI_TTS_END,         /* TTS 播报完成 */
    SM_EVT_AI_ASR_RESULT,      /* ASR 识别结果（含文本）*/
    SM_EVT_AI_CHAT_INTERRUPTED,/* 用户语音打断 TTS */
    /* 闹钟 */
    SM_EVT_ALARM_TRIGGER,      /* 闹钟到点（全局抢占）*/
    /* 云端指令 */
    SM_EVT_CLOUD_CMD,          /* H5 联动指令（含子类型）*/
    /* 内部定时器 */
    SM_EVT_S1_INTRO_TIMEOUT,
    SM_EVT_S3_DOCKED_TIMEOUT,
    SM_EVT_S4_SILENCE_TIMEOUT,
    SM_EVT_S9_CHEER_DONE,
    /* AI 业务 */
    SM_EVT_AI_SESSION_END,     /* 一次对话结束 */
    SM_EVT_AI_PROACTIVE_TRIGGER, /* AI 主动发起 */
    SM_EVT_MAX
} sm_event_id_t;

typedef struct {
    sm_event_id_t id;
    int32_t       arg1;  /* 通用参数（如 ASR 长度、子类型码）*/
    const char   *arg2;  /* 通用参数（如 ASR 文本）*/
} sm_event_t;

/* 状态码 → 手机 H5 视觉状态映射（同步给手机端）*/
typedef enum {
    SM_SYNC_BLACK            = 0,  /* S0 */
    SM_SYNC_INTRO_VIDEO      = 1,  /* S1 */
    SM_SYNC_LOCKED_VIDEO     = 3,  /* S3 */
    SM_SYNC_AI_IDLE_LOOP     = 4,  /* S4 / S5-不说话时 */
    SM_SYNC_AI_SPEAKING      = 5,  /* S5-说话时 */
    SM_SYNC_SLEEP_MEDITATION = 60, /* S6 */
    SM_SYNC_SLEEP_WHITENOISE = 61,
    SM_SYNC_SLEEP_BREATHING  = 62,
    SM_SYNC_SLEEP_TAROT      = 63,
    SM_SYNC_TAROT_TRANSITION = 7,  /* S7 */
    SM_SYNC_ALARM_LOOP       = 8,  /* S8 */
    SM_SYNC_CHEER_VIDEO      = 9   /* S9 */
} sm_sync_code_t;

/* ========== API ========== */
int  sm_fsm_init(void);
void sm_fsm_dispatch(sm_event_t *evt);          /* 投递事件到 FSM */
sm_state_t sm_fsm_get_state(void);
const char *sm_fsm_state_name(sm_state_t s);
const char *sm_fsm_event_name(sm_event_id_t e);

/* 内部调用：状态切换执行（state module 用）*/
void sm_fsm_set_state(sm_state_t next);

#ifdef __cplusplus
}
#endif

#endif
