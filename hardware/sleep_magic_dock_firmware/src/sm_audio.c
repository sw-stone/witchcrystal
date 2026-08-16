/**
 * @file sm_audio.c
 * @brief 音频管线封装：基于 TuyaOpen ai_chat_main + ai_audio_* (参考 your_chat_bot demo)
 *   - VAD → ASR → LLM Agent → TTS → 1W 功放
 *   - AEC 回采支持 TTS 打断
 *   - Wi-Fi 断线本地降级（按钮/闹钟/白噪音仍可用，对话提示网络不可用）
 *
 * 注意：本模块只做"状态机-音频管线"的适配，不重新实现 SDK 内部 AI 链路。
 */

#include "sm_audio.h"
#include "sm_state_machine.h"
#include "tal_api.h"
#include "tuya_log.h"

#define TAG "[AUDIO] "

#if __has_include("ai_chat_main.h")
#include "ai_chat_main.h"
#include "ai_audio_player.h"
#include "ai_audio_input.h"
#define HAVE_AI_AUDIO 1
#else
#define HAVE_AI_AUDIO 0
#endif

static bool s_muted     = false;
static bool s_online    = false;
static bool s_alarm_on  = false;
static bool s_inited    = false;

/* AI 事件回调 → FSM 事件（参考 ai_user_event.h 的事件类型）*/
#if HAVE_AI_AUDIO
#include "ai_user_event.h"

static void on_ai_event(AI_NOTIFY_EVENT_T *evt)
{
    if (evt == NULL) return;
    sm_event_t e = { SM_EVT_NONE, 0, NULL };
    switch (evt->type) {
    case AI_USER_EVT_TTS_START:
        e.id = SM_EVT_AI_TTS_START;
        break;
    case AI_USER_EVT_TTS_STOP:
        e.id = SM_EVT_AI_TTS_END;
        break;
    case AI_USER_EVT_CHAT_BREAK:
        /* 用户语音打断 TTS */
        e.id = SM_EVT_AI_CHAT_INTERRUPTED;
        break;
    case AI_USER_EVT_TEXT_STREAM_STOP:
        /* 一段对话结束 */
        e.id = SM_EVT_AI_SESSION_END;
        break;
    case AI_USER_EVT_TEXT_STREAM_DATA:
        /* ASR/LLM 文本流，只取最后一段 */
        if (evt->data) {
            AI_NOTIFY_TEXT_T *t = (AI_NOTIFY_TEXT_T *)evt->data;
            e.id   = SM_EVT_AI_ASR_RESULT;
            e.arg1 = t->datalen;
            e.arg2 = t->data;
        }
        break;
    case AI_USER_EVT_VAD_TIMEOUT:
        /* VAD 静默超时，对话自然结束 */
        e.id = SM_EVT_AI_SESSION_END;
        break;
    default:
        break;
    }
    if (e.id != SM_EVT_NONE) sm_fsm_dispatch(&e);
}
#endif

int sm_audio_init(void)
{
    if (s_inited) return 0;
#if HAVE_AI_AUDIO
    OPERATE_RET rt = ai_chat_init(&(AI_CHAT_MODE_CFG_T){
        .default_mode = AI_CHAT_MODE_HOLD,  /* push-to-talk: 长按 USER 说话 */
        .default_vol  = 50,
        .evt_cb       = (AI_USER_EVENT_NOTIFY)on_ai_event,
    });
    if (rt != OPRT_OK) {
        PR_ERR(TAG "ai_chat_init failed: %d", rt);
        return -1;
    }
    PR_INFO(TAG "AI audio pipeline initialized (hold mode, AEC on)");
#else
    PR_WARN(TAG "ai_chat_main.h not available, voice pipeline disabled (offline-only)");
#endif
    s_inited = true;
    return 0;
}

void sm_audio_vad_enable(bool on)
{
#if HAVE_AI_AUDIO
    /* wakeup 模式下 VAD 由 SDK 管理，这里仅打日志 */
    PR_DEBUG(TAG "vad %s", on ? "on" : "off");
#else
    (void)on;
#endif
}

void sm_audio_mute(bool on)
{
    s_muted = on;
#if HAVE_AI_AUDIO
    ai_chat_set_volume(on ? 0 : 50);
#endif
    PR_DEBUG(TAG "mute %s", on ? "on" : "off");
}

void sm_audio_clear_session(void)
{
#if HAVE_AI_AUDIO
    /* 触发 ai_audio 内部 reset，清空 LLM 上下文 */
    ai_audio_player_stop(AI_AUDIO_PLAYER_ALL);
    ai_audio_input_reset();
#endif
    PR_INFO(TAG "session cleared");
}

void sm_audio_stop_all(void)
{
#if HAVE_AI_AUDIO
    ai_audio_player_stop(AI_AUDIO_PLAYER_ALL);
#endif
    s_alarm_on = false;
}

void sm_audio_play_docked_fx(void)
{
#if HAVE_AI_AUDIO
    ai_audio_player_alert(12);  /* 入座提示音 */
#endif
}

void sm_audio_play_sleep(sm_sleep_subtype_t s)
{
    if (!s_online) {
        /* 离线降级：本地播放白噪音 / 呼吸引导（资源预置）*/
        PR_INFO(TAG "offline sleep mode %d (local fallback)", s);
#if HAVE_AI_AUDIO
        /* 用预置本地音频资源 */
        ai_audio_player_alert(20);  /* 假设 20=白噪音本地 */
#endif
        return;
    }
    /* 在线时由 LLM Agent 推送冥想引导 TTS */
    PR_INFO(TAG "online sleep mode %d (LLM-driven)", s);
}

void sm_audio_play_tarot_sequence(void)
{
#if HAVE_AI_AUDIO
    ai_audio_player_alert(13);  /* 塔罗音效 */
#endif
    /* TTS 解读由 LLM 接管 */
}

void sm_audio_play_alarm_loop(void)
{
    s_alarm_on = true;
#if HAVE_AI_AUDIO
    ai_audio_player_alert(15);  /* 闹钟循环音 */
#endif
}

void sm_audio_stop_alarm(void)
{
    s_alarm_on = false;
#if HAVE_AI_AUDIO
    ai_audio_player_stop(AI_AUDIO_PLAYER_FG);
#endif
}

void sm_audio_play_cheer(void)
{
#if HAVE_AI_AUDIO
    ai_audio_player_alert(16);  /* 起床庆祝音效 */
#endif
}

void sm_audio_on_network_change(bool online)
{
    if (s_online == online) return;
    s_online = online;
    PR_INFO(TAG "network %s", online ? "ONLINE" : "OFFLINE");
    if (!online && !s_alarm_on) {
        /* 离线降级提示 */
#if HAVE_AI_AUDIO
        ai_audio_player_alert(17);
#endif
    }
}
