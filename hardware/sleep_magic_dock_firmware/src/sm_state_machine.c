/**
 * @file sm_state_machine.c
 * @brief 显式状态表驱动的 FSM：state × event → {action, next_state}
 * 禁止 if-else 散落；所有转移在 s_state_table 内集中定义。
 */

#include "sm_state_machine.h"
#include "sm_button.h"
#include "sm_led.h"
#include "sm_audio.h"
#include "sm_cloud.h"
#include "sm_alarm.h"
#include "sm_state_sync.h"
#include "tal_api.h"
#include "tal_sw_timer.h"
#include "tuya_log.h"

/* 兜底默认值（Kconfig 注入优先）*/
#ifndef CONFIG_S1_INTRO_TIMEOUT_MS
#define CONFIG_S1_INTRO_TIMEOUT_MS 30000
#endif
#ifndef CONFIG_S3_TO_S4_DELAY_MS
#define CONFIG_S3_TO_S4_DELAY_MS 3000
#endif
#ifndef CONFIG_LOW_POWER_ENABLE
#define CONFIG_LOW_POWER_ENABLE 1
#endif

#define TAG "[FSM] "

/* 前向声明：entry/exit 钩子（每个状态一对）*/
static void on_enter_S0(void);
static void on_enter_S1(void);
static void on_enter_S2(void);
static void on_enter_S3(void);
static void on_enter_S4(void);
static void on_enter_S5(void);
static void on_enter_S6(void);
static void on_enter_S7(void);
static void on_enter_S8(void);
static void on_enter_S9(void);

/* ========== 当前状态 + 子类型 ========== */
static sm_state_t         s_state    = SM_STATE_STANDBY;
static sm_sleep_subtype_t s_sub      = SM_SLEEP_NONE;
static TIMER_ID           s_timer    = NULL;
static bool               s_inited   = false;

/* 状态名 / 事件名（日志用）*/
static const char *const k_state_name[SM_STATE_MAX] = {
    "S0_STANDBY", "S1_FIRST_USE", "S2_FORCE_STANDBY", "S3_DOCKED",
    "S4_AI_STANDBY", "S5_AI_SPEAKING", "S6_SLEEP_EXPERIENCE",
    "S7_TAROT_DRAW", "S8_ALARM_RINGING", "S9_WAKEUP_DONE"
};
static const char *const k_event_name[SM_EVT_MAX] = {
    "NONE", "BTN_FRONT", "BTN_BACK", "BTN_DOWN_PRESSED", "BTN_DOWN_RELEASED",
    "VOICE_VAD", "AI_TTS_START", "AI_TTS_END", "AI_ASR_RESULT",
    "AI_CHAT_INTERRUPTED", "ALARM_TRIGGER", "CLOUD_CMD",
    "S1_TIMEOUT", "S3_TIMEOUT", "S4_SILENCE_TIMEOUT", "S9_CHEER_DONE",
    "AI_SESSION_END", "AI_PROACTIVE_TRIGGER"
};

const char *sm_fsm_state_name(sm_state_t s) { return (s < SM_STATE_MAX) ? k_state_name[s] : "?"; }
const char *sm_fsm_event_name(sm_event_id_t e) { return (e < SM_EVT_MAX) ? k_event_name[e] : "?"; }
sm_state_t sm_fsm_get_state(void) { return s_state; }

/* ========== 状态切换 ========== */
void sm_fsm_set_state(sm_state_t next)
{
    if (next >= SM_STATE_MAX || next == s_state) return;
    PR_INFO(TAG "transition: %s -> %s", sm_fsm_state_name(s_state), sm_fsm_state_name(next));
    s_state = next;
    switch (next) {
        case SM_STATE_STANDBY:          on_enter_S0(); break;
        case SM_STATE_FIRST_USE:        on_enter_S1(); break;
        case SM_STATE_FORCE_STANDBY:    on_enter_S2(); break;
        case SM_STATE_DOCKED:           on_enter_S3(); break;
        case SM_STATE_AI_STANDBY:       on_enter_S4(); break;
        case SM_STATE_AI_SPEAKING:      on_enter_S5(); break;
        case SM_STATE_SLEEP_EXPERIENCE: on_enter_S6(); break;
        case SM_STATE_TAROT_DRAW:       on_enter_S7(); break;
        case SM_STATE_ALARM_RINGING:    on_enter_S8(); break;
        case SM_STATE_WAKEUP_DONE:      on_enter_S9(); break;
        default: break;
    }
}

/* ========== 一次性定时器回调（用于 S1/S3/S4/S9 超时）==========
 * tal_sw_timer 的 arg 在 create 时绑定，无法动态改；
 * 用 s_pending_timer_evt 暂存待触发的事件 ID，回调内取出。
 */
static sm_event_id_t s_pending_timer_evt = SM_EVT_NONE;

/* 低功耗 stub（实际可接 tal_sleep / tal_cpu_*，TODO 待集成）*/
static inline void sm_low_power_enter(void) { PR_DEBUG(TAG "low power enter (stub)"); }
static inline void sm_low_power_exit(void)  { PR_DEBUG(TAG "low power exit (stub)"); }

static void fsm_timer_cb(TIMER_ID tid, void *arg)
{
    (void)tid; (void)arg;
    sm_event_id_t evt = s_pending_timer_evt;
    s_pending_timer_evt = SM_EVT_NONE;
    sm_event_t e = { evt, 0, NULL };
    sm_fsm_dispatch(&e);
}

static void timer_start_once(sm_event_id_t evt_id, uint32_t ms)
{
    if (s_timer == NULL) {
        tal_sw_timer_create(fsm_timer_cb, NULL, &s_timer);
    }
    tal_sw_timer_stop(s_timer);
    s_pending_timer_evt = evt_id;
    tal_sw_timer_start(s_timer, ms, TAL_TIMER_ONCE);
}

/* ========== 各状态 entry 动作（exit 一般无副作用）========== */

static void on_enter_S0(void)  /* STANDBY */
{
    sm_led_set_effect(SM_LED_OFF);
    sm_audio_stop_all();
    sm_audio_mute(true);
    sm_sync_send(SM_SYNC_BLACK);
#if defined(CONFIG_LOW_POWER_ENABLE) && (CONFIG_LOW_POWER_ENABLE == 1)
    sm_low_power_enter();
#endif
}

static void on_enter_S1(void)  /* FIRST_USE */
{
    sm_led_set_effect(SM_LED_GUIDE);
    sm_audio_mute(false);
    sm_sync_send(SM_SYNC_INTRO_VIDEO);
    /* 视频播完由手机端通过 DP 101 上报 SM_SYNC_BLACK 触发 → SM_EVT_CLOUD_CMD
     * 兜底超时 CONFIG_S1_INTRO_TIMEOUT_MS 防手机不在线卡死 */
    timer_start_once(SM_EVT_S1_INTRO_TIMEOUT, CONFIG_S1_INTRO_TIMEOUT_MS);
}

static void on_enter_S2(void)  /* FORCE_STANDBY 瞬态 */
{
    sm_audio_stop_all();
    sm_audio_clear_session();
    /* 立即回落 S0 */
    sm_fsm_set_state(SM_STATE_STANDBY);
}

static void on_enter_S3(void)  /* DOCKED */
{
    sm_led_set_effect(SM_LED_DOCKED);
    sm_audio_mute(false);
    sm_audio_play_docked_fx();
    sm_cloud_report_docked(true);
    sm_sync_send(SM_SYNC_LOCKED_VIDEO);
    timer_start_once(SM_EVT_S3_DOCKED_TIMEOUT, CONFIG_S3_TO_S4_DELAY_MS);
}

static void on_enter_S4(void)  /* AI_STANDBY */
{
    sm_led_set_effect(SM_LED_BREATH);
    sm_audio_mute(false);
    sm_audio_vad_enable(true);
    sm_sync_send(SM_SYNC_AI_IDLE_LOOP);
#if defined(CONFIG_LOW_POWER_ENABLE) && (CONFIG_LOW_POWER_ENABLE == 1)
    sm_low_power_exit();
#endif
}

static void on_enter_S5(void)  /* AI_SPEAKING */
{
    sm_led_set_effect(SM_LED_SPEAKING);
    sm_sync_send(SM_SYNC_AI_SPEAKING);
}

static void on_enter_S6(void)  /* SLEEP_EXPERIENCE */
{
    sm_led_set_effect(SM_LED_SLEEP);
    switch (s_sub) {
        case SM_SLEEP_MEDITATION: sm_sync_send(SM_SYNC_SLEEP_MEDITATION); break;
        case SM_SLEEP_WHITENOISE: sm_sync_send(SM_SYNC_SLEEP_WHITENOISE); break;
        case SM_SLEEP_BREATHING:  sm_sync_send(SM_SYNC_SLEEP_BREATHING);  break;
        case SM_SLEEP_TAROT:      sm_sync_send(SM_SYNC_SLEEP_TAROT);      break;
        default: break;
    }
    sm_audio_play_sleep(s_sub);
}

static void on_enter_S7(void)  /* TAROT_DRAW */
{
    sm_led_set_effect(SM_LED_TAROT);
    sm_sync_send(SM_SYNC_TAROT_TRANSITION);
    sm_audio_play_tarot_sequence();
}

static void on_enter_S8(void)  /* ALARM_RINGING 全局抢占 */
{
    sm_led_set_effect(SM_LED_ALARM);
    sm_audio_stop_all();
    sm_audio_play_alarm_loop();
    sm_sync_send(SM_SYNC_ALARM_LOOP);
    sm_sync_start_heartbeat();
}

static void on_enter_S9(void)  /* WAKEUP_DONE 瞬态 */
{
    sm_led_set_effect(SM_LED_CHEER);
    sm_audio_stop_alarm();
    sm_audio_play_cheer();
    sm_sync_send(SM_SYNC_CHEER_VIDEO);
    sm_sync_stop_heartbeat();
    timer_start_once(SM_EVT_S9_CHEER_DONE, 5000); /* 庆祝播 5s 后回 S0 */
}

/* ========== 显式状态表：[state][event] → (action, next_state) ==========
 * 未列出的事件 → 忽略；BTN_BACK 与 ALARM_TRIGGER 在所有状态都生效。
 */
typedef struct {
    sm_state_t    next;
    sm_sleep_subtype_t sub;   /* S6 进入时携带的子类型 */
} trans_t;

/* 默认忽略 */
#define IGN  { SM_STATE_MAX, SM_SLEEP_NONE }

/* 全局事件（任意状态都响应）*/
static inline bool global_event(sm_event_id_t e, sm_state_t cur, trans_t *out)
{
    if (e == SM_EVT_BTN_BACK) {
        *out = (trans_t){ SM_STATE_FORCE_STANDBY, SM_SLEEP_NONE };
        return true;
    }
    if (e == SM_EVT_ALARM_TRIGGER && cur != SM_STATE_ALARM_RINGING) {
        *out = (trans_t){ SM_STATE_ALARM_RINGING, SM_SLEEP_NONE };
        return true;
    }
    if (e == SM_EVT_BTN_DOWN_RELEASED && cur != SM_STATE_STANDBY && cur != SM_STATE_FIRST_USE) {
        /* 任意工作态手机离座 → S0 */
        *out = (trans_t){ SM_STATE_STANDBY, SM_SLEEP_NONE };
        return true;
    }
    return false;
}

/* 主分发器 */
void sm_fsm_dispatch(sm_event_t *evt)
{
    if (!s_inited || evt == NULL) return;

    PR_INFO(TAG "event %s in %s arg1=%d", sm_fsm_event_name(evt->id),
            sm_fsm_state_name(s_state), evt->arg1);

    /* 1. 全局事件优先 */
    trans_t t = IGN;
    if (global_event(evt->id, s_state, &t)) {
        if (t.next != SM_STATE_MAX) {
            if (t.next == SM_STATE_SLEEP_EXPERIENCE) s_sub = t.sub;
            sm_fsm_set_state(t.next);
        }
        return;
    }

    /* 2. 状态-事件表 */
    switch (s_state) {
    case SM_STATE_STANDBY:
        if (evt->id == SM_EVT_BTN_FRONT) { sm_fsm_set_state(SM_STATE_FIRST_USE); return; }
        if (evt->id == SM_EVT_BTN_DOWN_PRESSED) { sm_fsm_set_state(SM_STATE_DOCKED); return; }
        break;

    case SM_STATE_FIRST_USE:
        /* 视频播完（云端上报 SM_SYNC_BLACK）→ S2 强制回待机 */
        if (evt->id == SM_EVT_CLOUD_CMD && evt->arg1 == SM_SYNC_BLACK) {
            sm_fsm_set_state(SM_STATE_FORCE_STANDBY);
            return;
        }
        /* 兜底超时 → S2（防手机不在线卡死）*/
        if (evt->id == SM_EVT_S1_INTRO_TIMEOUT) { sm_fsm_set_state(SM_STATE_FORCE_STANDBY); return; }
        if (evt->id == SM_EVT_BTN_DOWN_PRESSED) { sm_fsm_set_state(SM_STATE_DOCKED); return; }
        break;

    case SM_STATE_FORCE_STANDBY:
        /* 瞬态，on_enter_S2 已自动切到 S0 */
        break;

    case SM_STATE_DOCKED:
        if (evt->id == SM_EVT_S3_DOCKED_TIMEOUT) { sm_fsm_set_state(SM_STATE_AI_STANDBY); return; }
        break;

    case SM_STATE_AI_STANDBY:
        if (evt->id == SM_EVT_VOICE_VAD_DETECTED ||
            evt->id == SM_EVT_AI_PROACTIVE_TRIGGER) {
            sm_fsm_set_state(SM_STATE_AI_SPEAKING);
            return;
        }
        if (evt->id == SM_EVT_CLOUD_CMD && evt->arg1 == SM_SYNC_SLEEP_TAROT) {
            s_sub = SM_SLEEP_TAROT;
            sm_fsm_set_state(SM_STATE_TAROT_DRAW);
            return;
        }
        if (evt->id == SM_EVT_CLOUD_CMD) {
            /* 云端选择睡眠体验子类型 */
            switch (evt->arg1) {
                case SM_SYNC_SLEEP_MEDITATION: s_sub = SM_SLEEP_MEDITATION; sm_fsm_set_state(SM_STATE_SLEEP_EXPERIENCE); return;
                case SM_SYNC_SLEEP_WHITENOISE: s_sub = SM_SLEEP_WHITENOISE; sm_fsm_set_state(SM_STATE_SLEEP_EXPERIENCE); return;
                case SM_SYNC_SLEEP_BREATHING:  s_sub = SM_SLEEP_BREATHING;  sm_fsm_set_state(SM_STATE_SLEEP_EXPERIENCE); return;
                default: break;
            }
        }
        break;

    case SM_STATE_AI_SPEAKING:
        if (evt->id == SM_EVT_AI_TTS_START) { /* 维持 S5 */ return; }
        if (evt->id == SM_EVT_AI_TTS_END || evt->id == SM_EVT_AI_SESSION_END) {
            sm_fsm_set_state(SM_STATE_AI_STANDBY);
            return;
        }
        if (evt->id == SM_EVT_AI_CHAT_INTERRUPTED) {
            /* TTS 被打断，重新聆听 → 维持 S5 */
            return;
        }
        if (evt->id == SM_EVT_AI_ASR_RESULT && evt->arg2) {
            /* ASR 文本中含睡眠关键词 → 进 S6（简化判定）*/
            const char *txt = evt->arg2;
            if (strstr(txt, "冥想") || strstr(txt, "meditation")) { s_sub = SM_SLEEP_MEDITATION; sm_fsm_set_state(SM_STATE_SLEEP_EXPERIENCE); return; }
            if (strstr(txt, "白噪音") || strstr(txt, "whitenoise")) { s_sub = SM_SLEEP_WHITENOISE; sm_fsm_set_state(SM_STATE_SLEEP_EXPERIENCE); return; }
            if (strstr(txt, "呼吸") || strstr(txt, "breathing"))   { s_sub = SM_SLEEP_BREATHING;  sm_fsm_set_state(SM_STATE_SLEEP_EXPERIENCE); return; }
            if (strstr(txt, "塔罗") || strstr(txt, "tarot"))       { sm_fsm_set_state(SM_STATE_TAROT_DRAW); return; }
        }
        break;

    case SM_STATE_SLEEP_EXPERIENCE:
        if (evt->id == SM_EVT_CLOUD_CMD && evt->arg1 == SM_SYNC_AI_IDLE_LOOP) {
            sm_fsm_set_state(SM_STATE_AI_STANDBY);
            return;
        }
        break;

    case SM_STATE_TAROT_DRAW:
        if (evt->id == SM_EVT_AI_TTS_END || evt->id == SM_EVT_AI_SESSION_END) {
            sm_fsm_set_state(SM_STATE_AI_STANDBY);
            return;
        }
        break;

    case SM_STATE_ALARM_RINGING:
        if (evt->id == SM_EVT_BTN_FRONT || evt->id == SM_EVT_BTN_BACK) {
            sm_fsm_set_state(SM_STATE_WAKEUP_DONE);
            return;
        }
        break;

    case SM_STATE_WAKEUP_DONE:
        if (evt->id == SM_EVT_S9_CHEER_DONE) { sm_fsm_set_state(SM_STATE_STANDBY); return; }
        break;

    default: break;
    }

    PR_DEBUG(TAG "event %s ignored in %s", sm_fsm_event_name(evt->id), sm_fsm_state_name(s_state));
}

int sm_fsm_init(void)
{
    if (s_inited) return 0;
    s_state = SM_STATE_STANDBY;
    s_sub   = SM_SLEEP_NONE;
    s_inited = true;
    PR_INFO(TAG "init, enter S0");
    on_enter_S0();
    return 0;
}
