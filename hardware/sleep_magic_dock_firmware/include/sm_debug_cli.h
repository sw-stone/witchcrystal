#ifndef __SM_DEBUG_CLI_H__
#define __SM_DEBUG_CLI_H__

#ifdef __cplusplus
extern "C" {
#endif

/**
 * @file sm_debug_cli.h
 * @brief FSM 串口调试命令（开发/验收期专用）
 *
 * 无物理按钮/摇杆时，从日志串口注入事件验证状态机全链路：
 *   fsm            - 打印当前状态
 *   fsm ev <n>     - 注入事件（n=事件枚举值，见 sm_state_machine.h）
 *   fsm front      - 按钮-前（等价 ev 1）
 *   fsm back       - 按钮-后（等价 ev 2）
 *   fsm dock       - 手机入座（按钮-下压下）
 *   fsm undock     - 手机离座（按钮-下弹起）
 *   fsm voice      - VAD 语音事件
 *   fsm tts on|off - TTS 播报开始/结束
 *   fsm alarm      - 闹钟触发（全局抢占）
 *   fsm sub <n>    - 云端指令选择睡眠子类型（60-63 或 1-4）
 *   fsm list       - 列出全部事件枚举值
 */

int sm_debug_cli_init(void);

#ifdef __cplusplus
}
#endif

#endif /* __SM_DEBUG_CLI_H__ */
