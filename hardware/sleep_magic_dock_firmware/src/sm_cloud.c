/**
 * @file sm_cloud.c
 * @brief DP 上报封装
 */

#include "sm_cloud.h"
#include "tuya_iot.h"
#include "tuya_iot_dp.h"
#include "tal_api.h"
#include "tuya_log.h"

#define TAG "[CLOUD] "

static bool s_inited = false;

static void report_enum(uint8_t dp_id, int32_t v)
{
    if (!s_inited) return;
    tuya_iot_client_t *c = tuya_iot_client_get();
    dp_obj_t dp = {0};
    dp.id = dp_id; dp.type = PROP_ENUM; dp.value.dp_enum = v;
    tuya_iot_dp_obj_report(c, c->activate.devid, &dp, 1, 0);
    PR_DEBUG(TAG "enum dp=%d v=%d", dp_id, v);
}

static void report_bool(uint8_t dp_id, bool v)
{
    if (!s_inited) return;
    tuya_iot_client_t *c = tuya_iot_client_get();
    dp_obj_t dp = {0};
    dp.id = dp_id; dp.type = PROP_BOOL; dp.value.dp_bool = v;
    tuya_iot_dp_obj_report(c, c->activate.devid, &dp, 1, 0);
    PR_DEBUG(TAG "bool dp=%d v=%d", dp_id, v);
}

static void report_value(uint8_t dp_id, int32_t v)
{
    if (!s_inited) return;
    tuya_iot_client_t *c = tuya_iot_client_get();
    dp_obj_t dp = {0};
    dp.id = dp_id; dp.type = PROP_VALUE; dp.value.dp_value = v;
    tuya_iot_dp_obj_report(c, c->activate.devid, &dp, 1, 0);
    PR_DEBUG(TAG "value dp=%d v=%d", dp_id, v);
}

static void report_string(uint8_t dp_id, const char *s)
{
    if (!s_inited || s == NULL) return;
    tuya_iot_client_t *c = tuya_iot_client_get();
    dp_obj_t dp = {0};
    dp.id = dp_id; dp.type = PROP_STR; dp.value.dp_str = (char *)s;
    tuya_iot_dp_obj_report(c, c->activate.devid, &dp, 1, 0);
    PR_DEBUG(TAG "string dp=%d len=%d", dp_id, (int)strlen(s));
}

int sm_cloud_init(void)
{
    s_inited = true;
    PR_INFO(TAG "init");
    return 0;
}

void sm_cloud_report_state(int code)              { report_enum(SM_DP_STATE_CODE, code); }
void sm_cloud_report_docked(bool docked)          { report_bool(SM_DP_DOCKED, docked); }
void sm_cloud_report_ai_speaking(bool speaking)   { report_bool(SM_DP_AI_SPEAKING, speaking); }
void sm_cloud_report_alarm_set(const char *hhmm)  { report_string(SM_DP_ALARM_SET, hhmm); }
void sm_cloud_report_sleep_subtype(int sub)       { report_enum(SM_DP_SLEEP_SUBTYPE, sub); }
void sm_cloud_report_volume(int vol)              { report_value(SM_DP_VOLUME, vol); }
void sm_cloud_report_wifi_online(bool online)     { report_bool(SM_DP_WIFI_ONLINE, online); }
void sm_cloud_report_heartbeat(uint32_t seq)      { report_value(SM_DP_HEARTBEAT, (int32_t)seq); }
