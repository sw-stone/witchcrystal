#ifndef __SM_AUDIO_H__
#define __SM_AUDIO_H__

#include "tuya_cloud_types.h"
#include "sm_state_machine.h"

#ifdef __cplusplus
extern "C" {
#endif

/**
 * @brief 音频管线封装：基于 TuyaOpen ai_chat_main / ai_audio_* 实现
 *  - VAD 常开（S4）
 *  - ASR → LLM Agent → TTS → 1W 功放
 *  - AEC 回采支持 TTS 播报中用户语音打断
 *  - Wi-Fi 断线时本地降级（保留按钮/闹钟/白噪音）
 */
int  sm_audio_init(void);

/* 唤醒/聆听控制 */
void sm_audio_vad_enable(bool on);

/* 播放控制 */
void sm_audio_play_docked_fx(void);          /* 入座音效 */
void sm_audio_play_sleep(sm_sleep_subtype_t s); /* 冥想/白噪音/呼吸 */
void sm_audio_play_tarot_sequence(void);     /* 塔罗音效 + 转场 */
void sm_audio_play_alarm_loop(void);         /* 闹钟循环 */
void sm_audio_play_cheer(void);              /* 起床庆祝 */
void sm_audio_stop_all(void);
void sm_audio_stop_alarm(void);

/* 会话/静音 */
void sm_audio_mute(bool on);
void sm_audio_clear_session(void);           /* S2 强制清空 AI 上下文 */

/* 网络状态变化通知（用于离线降级提示）*/
void sm_audio_on_network_change(bool online);

#ifdef __cplusplus
}
#endif

#endif
