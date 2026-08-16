/**
 * @file sm_debug_cli.c
 * @brief FSM 串口调试命令实现（开发/验收期专用）
 *
 * 通过 tal_cli 注册 `fsm` 命令，从日志串口注入事件驱动状态机，
 * 不依赖物理按钮/摇杆/云端即可复现全部 S0~S9 转移（P1 验收门）。
 */
#include "sm_debug_cli.h"
#include "sm_state_machine.h"
#include "sm_state_sync.h"
#include "tal_cli.h"
#include "tuya_log.h"
#include <string.h>
#include <stdio.h>
#include <stdlib.h>

#define TAG "[FSMCLI] "

/* ---------- 子命令：fsm（无参数）打印当前状态 ---------- */
static void cli_fsm_state(int argc, char *argv[])
{
    (void)argc; (void)argv;
    PR_INFO(TAG "state = %s (code %d), sleep_sub = %d",
            sm_fsm_state_name(sm_fsm_get_state()), (int)sm_fsm_get_state(),
            (int)SM_SLEEP_NONE);
}

/* ---------- 子命令：fsm list 枚举全部事件 ---------- */
static void cli_fsm_list(int argc, char *argv[])
{
    (void)argc; (void)argv;
    static const struct { int id; const char *name; } k_ev[] = {
        { SM_EVT_BTN_FRONT,           "front  按钮-前" },
        { SM_EVT_BTN_BACK,            "back   按钮-后(最高优先级)" },
        { SM_EVT_BTN_DOWN_PRESSED,    "dock   手机入座" },
        { SM_EVT_BTN_DOWN_RELEASED,   "undock 手机离座" },
        { SM_EVT_VOICE_VAD_DETECTED,  "voice  VAD语音" },
        { SM_EVT_AI_TTS_START,        "tts on TTS开始" },
        { SM_EVT_AI_TTS_END,          "tts off TTS结束" },
        { SM_EVT_AI_CHAT_INTERRUPTED, "打断TTS" },
        { SM_EVT_ALARM_TRIGGER,       "alarm  闹钟抢占" },
        { SM_EVT_CLOUD_CMD,           "cloud  云指令(arg1=子类型)" },
        { SM_EVT_S1_INTRO_TIMEOUT,    "S1超时" },
        { SM_EVT_S3_DOCKED_TIMEOUT,   "S3激活超时" },
        { SM_EVT_S4_SILENCE_TIMEOUT,  "S4静默30s" },
        { SM_EVT_S9_CHEER_DONE,       "S9庆祝完成" },
        { SM_EVT_AI_SESSION_END,      "AI会话结束" },
        { SM_EVT_AI_PROACTIVE_TRIGGER,"AI主动发起" },
    };
    PR_INFO(TAG "== events (%d) ==", (int)(sizeof(k_ev) / sizeof(k_ev[0])));
    for (size_t i = 0; i < sizeof(k_ev) / sizeof(k_ev[0]); i++) {
        PR_INFO(TAG "  ev %2d  %s", k_ev[i].id, k_ev[i].name);
    }
    PR_INFO(TAG "== sleep subtypes (cloud cmd arg1) ==");
    PR_INFO(TAG "  %d meditation / %d whitenoise / %d breathing / %d tarot",
            (int)SM_SYNC_SLEEP_MEDITATION, (int)SM_SYNC_SLEEP_WHITENOISE,
            (int)SM_SYNC_SLEEP_BREATHING, (int)SM_SYNC_SLEEP_TAROT);
}

/* ---------- 事件注入统一入口 ---------- */
static void inject(sm_event_id_t id, int32_t arg1)
{
    PR_INFO(TAG "inject <%s> arg1=%d", sm_fsm_event_name(id), arg1);
    sm_event_t e = { id, arg1, NULL };
    sm_fsm_dispatch(&e);
    PR_INFO(TAG "now state = %s", sm_fsm_state_name(sm_fsm_get_state()));
}

/* ---------- 主命令回调 ---------- */
static void cli_fsm_cmd(int argc, char *argv[])
{
    if (argc < 2) {
        cli_fsm_state(0, NULL);
        PR_INFO(TAG "usage: fsm [state|list|ev <n>|front|back|dock|undock|voice|tts on|tts off|alarm|sub <n>]");
        return;
    }

    const char *sub = argv[1];

    if (strcmp(sub, "state") == 0) {
        cli_fsm_state(0, NULL);
        return;
    }
    if (strcmp(sub, "list") == 0) {
        cli_fsm_list(0, NULL);
        return;
    }
    if (strcmp(sub, "front") == 0) {
        inject(SM_EVT_BTN_FRONT, 0);
        return;
    }
    if (strcmp(sub, "back") == 0) {
        inject(SM_EVT_BTN_BACK, 0);
        return;
    }
    if (strcmp(sub, "dock") == 0) {
        inject(SM_EVT_BTN_DOWN_PRESSED, 0);
        return;
    }
    if (strcmp(sub, "undock") == 0) {
        inject(SM_EVT_BTN_DOWN_RELEASED, 0);
        return;
    }
    if (strcmp(sub, "voice") == 0) {
        inject(SM_EVT_VOICE_VAD_DETECTED, 0);
        return;
    }
    if (strcmp(sub, "tts") == 0) {
        inject((argc >= 3 && strcmp(argv[2], "on") == 0)
                   ? SM_EVT_AI_TTS_START : SM_EVT_AI_TTS_END, 0);
        return;
    }
    if (strcmp(sub, "alarm") == 0) {
        inject(SM_EVT_ALARM_TRIGGER, 0);
        return;
    }
    if (strcmp(sub, "sub") == 0 || strcmp(sub, "cloud") == 0) {
        if (argc < 3) {
            PR_INFO(TAG "need subtype: 60 meditation / 61 whitenoise / 62 breathing / 63 tarot");
            return;
        }
        int32_t n = (int32_t)atoi(argv[2]);
        inject(SM_EVT_CLOUD_CMD, n);
        return;
    }
    if (strcmp(sub, "ev") == 0) {
        if (argc < 3) {
            PR_INFO(TAG "need event id, see: fsm list");
            return;
        }
        inject((sm_event_id_t)atoi(argv[2]), 0);
        return;
    }

    PR_INFO(TAG "unknown subcommand: %s", sub);
}

/* ---------- 注册 ---------- */
static cli_cmd_t s_cmds[] = {
    {
        .name = "fsm",
        .help = "fsm debug: state|list|ev <n>|front|back|dock|undock|voice|tts on|tts off|alarm|sub <n>",
        .func = cli_fsm_cmd,
    },
};

int sm_debug_cli_init(void)
{
    int rt = tal_cli_cmd_register(s_cmds, sizeof(s_cmds) / sizeof(s_cmds[0]));
    if (rt == 0) {
        PR_INFO(TAG "registered 'fsm' debug commands");
    } else {
        PR_WARN(TAG "tal_cli_cmd_register failed: %d", rt);
    }
    return rt;
}
