#ifndef __TUYA_CONFIG_H__
#define __TUYA_CONFIG_H__

#include "tuya_cloud_types.h"

#ifdef __cplusplus
extern "C" {
#endif

/* 复用 mbti_divination 已激活设备的 PID/UUID/AuthKey
 * 注意：若要切换到独立 PID "sleep_magic_dock"，需在涂鸦 IoT 平台
 * 申请新 UUID/AuthKey 并替换此处。
 */
#ifndef TUYA_PRODUCT_ID
#define TUYA_PRODUCT_ID         "t6wgdighkirqcnyw"
#endif

#ifndef TUYA_OPENSDK_UUID
#define TUYA_OPENSDK_UUID       "uuid9bb10d35903b55de"
#endif

#ifndef TUYA_OPENSDK_AUTHKEY
#define TUYA_OPENSDK_AUTHKEY    "UxCacYWpAjNK722ee4UPZamr7B1Tit0S"
#endif

/* AI Agent 人设（与云端 Agent 配置一致）*/
#ifndef CONFIG_AI_AGENT_PERSONA
#define CONFIG_AI_AGENT_PERSONA \
    "You are 'Nyx', a sleep guardian spirit living in a magic ball dock. " \
    "Speak softly, briefly, and warmly. Guide users toward sleep through " \
    "meditation, white noise, breathing, or tarot. Never exceed 3 sentences per turn."
#endif

#ifdef __cplusplus
}
#endif

#endif
