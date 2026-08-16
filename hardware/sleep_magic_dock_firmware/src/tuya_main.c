/**
 * @file tuya_main.c
 * @brief AI Sleep Magic Ball Dock - 应用入口
 *
 * 按 TuyaOpen 启动契约：tuya_app_main 起 app 线程，user_main 做基础服务
 * 初始化（log/kv/sw_timer/workq/time/cli）+ 授权 + tuya_iot_init + 配网，
 * 然后业务模块 init，最后 yield loop。
 */

#include "tuya_cloud_types.h"
#include "tal_api.h"
#include "tuya_iot.h"
#include "tuya_iot_dp.h"
#include "netmgr.h"
#include "tkl_output.h"
#include "tal_cli.h"
#include "tuya_authorize.h"
#include "board_com_api.h"
#if __has_include("reset_netcfg.h")
#include "reset_netcfg.h"
#endif

#if defined(ENABLE_WIFI) && (ENABLE_WIFI == 1)
#include "netconn_wifi.h"
#endif

#include "tuya_config.h"
#include "sm_state_machine.h"
#include "sm_button.h"
#include "sm_led.h"
#include "sm_audio.h"
#include "sm_cloud.h"
#include "sm_alarm.h"
#include "sm_state_sync.h"
#include "sm_joystick.h"
#include "sm_debug_cli.h"

#define TAG "[MAIN] "

static tuya_iot_client_t  ai_client;
static tuya_iot_license_t license;
static bool               s_wifi_online = false;

/* 网络状态检查（每秒）*/
static bool user_network_check(void)
{
    netmgr_status_e status = NETMGR_LINK_DOWN;
    netmgr_conn_get(NETCONN_AUTO, NETCONN_CMD_STATUS, &status);
    return status == NETMGR_LINK_DOWN ? false : true;
}

/* 涂鸦云事件回调 */
static void user_event_handler_on(tuya_iot_client_t *client, tuya_event_msg_t *event)
{
    (void)client;
    switch (event->id) {
    case TUYA_EVENT_MQTT_CONNECTED:
        PR_INFO(TAG "MQTT connected");
        break;
    case TUYA_EVENT_MQTT_DISCONNECT:
        PR_INFO(TAG "MQTT disconnected");
        break;
    case TUYA_EVENT_TIMESTAMP_SYNC:
        PR_INFO(TAG "Sync timestamp:%d", event->value.asInteger);
        break;
    case TUYA_EVENT_DP_RECEIVE_OBJ: {
        /* 处理 App 下发的 DP（如设置闹钟 / 选择睡眠体验）*/
        dp_obj_recv_t *dpobj = event->value.dpobj;
        for (uint32_t i = 0; i < dpobj->dpscnt; i++) {
            dp_obj_t *dp = &dpobj->dps[i];
            switch (dp->id) {
            case SM_DP_ALARM_SET:
                if (dp->type == PROP_STR) {
                    sm_alarm_set(dp->value.dp_str);
                }
                break;
            case SM_DP_SLEEP_SUBTYPE:
                if (dp->type == PROP_ENUM) {
                    /* 云端选择睡眠子类型 → FSM */
                    sm_event_t e = { SM_EVT_CLOUD_CMD, dp->value.dp_enum, NULL };
                    sm_fsm_dispatch(&e);
                }
                break;
            default: break;
            }
        }
        /* 回显 */
        tuya_iot_dp_obj_report(client, dpobj->devid, dpobj->dps, dpobj->dpscnt, 0);
    } break;
    case TUYA_EVENT_RESET:
        PR_INFO(TAG "Device Reset:%d", event->value.asInteger);
        break;
    case TUYA_EVENT_RESET_COMPLETE:
        PR_INFO(TAG "Device Reset Complete!");
        tal_system_reset();
        break;
    default: break;
    }
}

/* 摇杆周期轮询定时器：每 50ms 读一次 SW + 方向 */
static TIMER_ID s_joy_poll_timer = NULL;
static void joy_poll_cb(TIMER_ID tid, void *arg)
{
    (void)tid; (void)arg;
    joy_event_t e = app_joystick_poll();
    if (e == JOY_NONE) return;

    sm_event_t fsm_evt = { SM_EVT_NONE, 0, NULL };
    switch (e) {
    case JOY_PRESS:       /* SW 短按 = 按钮-前 */
        fsm_evt.id = SM_EVT_BTN_FRONT;
        break;
    case JOY_LONG_PRESS:  /* SW 长按 = 按钮-后（强制回待机）*/
        fsm_evt.id = SM_EVT_BTN_BACK;
        break;
    case JOY_LEFT:        /* 在 S6 睡眠体验中切换：冥想 */
        fsm_evt.id  = SM_EVT_CLOUD_CMD;
        fsm_evt.arg1 = SM_SYNC_SLEEP_MEDITATION;
        break;
    case JOY_RIGHT:       /* 白噪音 */
        fsm_evt.id  = SM_EVT_CLOUD_CMD;
        fsm_evt.arg1 = SM_SYNC_SLEEP_WHITENOISE;
        break;
    case JOY_UP:          /* 呼吸 */
        fsm_evt.id  = SM_EVT_CLOUD_CMD;
        fsm_evt.arg1 = SM_SYNC_SLEEP_BREATHING;
        break;
    case JOY_DOWN:        /* 塔罗 */
        fsm_evt.id  = SM_EVT_CLOUD_CMD;
        fsm_evt.arg1 = SM_SYNC_SLEEP_TAROT;
        break;
    default: break;
    }
    if (fsm_evt.id != SM_EVT_NONE) {
        sm_fsm_dispatch(&fsm_evt);
    }
}

/* Wi-Fi 在线状态轮询（5s 一次）→ 通知 audio 模块降级 + 上报云端 */
static TIMER_ID s_net_poll_timer = NULL;
static void net_poll_cb(TIMER_ID tid, void *arg)
{
    (void)tid; (void)arg;
    bool online = user_network_check();
    if (online != s_wifi_online) {
        s_wifi_online = online;
        sm_audio_on_network_change(online);
        sm_cloud_report_wifi_online(online);
    }
}

static void user_main(void)
{
    PR_NOTICE("========================================");
    PR_NOTICE("  AI Sleep Magic Ball Dock v1.0");
    PR_NOTICE("  T5AI-Core firmware");
    PR_NOTICE("========================================");
    PR_NOTICE("Project:     %s", PROJECT_NAME);
    PR_NOTICE("App version: %s", PROJECT_VERSION);
    PR_NOTICE("Compile:     %s %s", __DATE__, __TIME__);
    PR_NOTICE("TuyaOpen:    %s", OPEN_VERSION);

    cJSON_InitHooks(&(cJSON_Hooks){.malloc_fn = tal_malloc, .free_fn = tal_free});
    tal_log_init(TAL_LOG_LEVEL_DEBUG, 1024, (TAL_LOG_OUTPUT_CB)tkl_log_output);
    tal_kv_init(&(tal_kv_cfg_t){
        .seed = "vmlkasdh93dlvlcy",
        .key  = "dflfuap134ddlduq",
    });
    tal_sw_timer_init();
    tal_workq_init();
    tal_time_service_init();
    tal_cli_init();
    sm_debug_cli_init();   /* 'fsm' 调试命令：串口注入事件验证状态机 */
    tuya_authorize_init();

#if __has_include("reset_netcfg.h")
    reset_netconfig_start();
#endif

    if (OPRT_OK != tuya_authorize_read(&license)) {
        license.uuid    = TUYA_OPENSDK_UUID;
        license.authkey = TUYA_OPENSDK_AUTHKEY;
        PR_WARN(TAG "Use built-in open-sdk uuid/authkey (replace before production)");
    }

    /* 初始化 Tuya 设备 */
    OPERATE_RET rt = tuya_iot_init(&ai_client, &(const tuya_iot_config_t){
        .software_ver  = PROJECT_VERSION,
        .productkey    = TUYA_PRODUCT_ID,
        .uuid          = license.uuid,
        .authkey       = license.authkey,
        .event_handler = user_event_handler_on,
        .network_check = user_network_check,
    });
    if (rt != OPRT_OK) {
        PR_ERR(TAG "tuya_iot_init failed: %d", rt);
        return;
    }

    /* 网络 */
    netmgr_type_e type = 0;
#if defined(ENABLE_WIFI) && (ENABLE_WIFI == 1)
    type |= NETCONN_WIFI;
#endif
    netmgr_init(type);
#if defined(ENABLE_WIFI) && (ENABLE_WIFI == 1)
    netmgr_conn_set(NETCONN_WIFI, NETCONN_CMD_NETCFG,
                    &(netcfg_args_t){.type = NETCFG_TUYA_BLE | NETCFG_TUYA_WIFI_AP});

    /* ==== 临时 WiFi 直连（TODO: 设备联网成功后可删除本段）==== */
    {
        netconn_wifi_info_t wifi_info = {0};
        snprintf(wifi_info.ssid, sizeof(wifi_info.ssid), "le vent de Versailles");
        snprintf(wifi_info.pswd, sizeof(wifi_info.pswd), "nsy888888");
        netmgr_conn_set(NETCONN_WIFI, NETCONN_CMD_SSID_PSWD, &wifi_info);
        PR_NOTICE(TAG "[WiFi] override -> %s", wifi_info.ssid);
    }
#endif

    /* 板级硬件注册（音频/按钮 P29/LED）*/
    rt = board_register_hardware();
    if (rt != OPRT_OK) {
        PR_ERR(TAG "board_register_hardware failed: %d", rt);
    }

    /* 业务模块 init（顺序：LED → cloud/sync → alarm → audio → button → joystick → FSM）*/
    sm_led_init();
    sm_cloud_init();
    sm_sync_init();
    sm_alarm_init();
    sm_audio_init();
    sm_button_init();

    /* 摇杆 init + 启动 50ms 周期轮询（VRx=P25/VRy=P24/SW=P20）*/
    rt = app_joystick_init();
    if (rt != OPRT_OK) {
        PR_ERR(TAG "joystick init failed: %d (P25/P24/P20 wiring?)", rt);
    } else {
        tal_sw_timer_create(joy_poll_cb, NULL, &s_joy_poll_timer);
        tal_sw_timer_start(s_joy_poll_timer, 50, TAL_TIMER_CYCLE);
        PR_INFO(TAG "joystick polling started (50ms cycle)");
    }

    /* FSM 必须最后启动，确保所有 entry 动作可用的模块都已就绪 */
    sm_fsm_init();

    PR_INFO(TAG "device ready");

    /* 启动 tuya iot 任务 */
    tuya_iot_start(&ai_client);

#if __has_include("reset_netcfg.h")
    reset_netconfig_check();
#endif

    /* 网络状态轮询 */
    tal_sw_timer_create(net_poll_cb, NULL, &s_net_poll_timer);
    tal_sw_timer_start(s_net_poll_timer, 5000, TAL_TIMER_CYCLE);

    /* yield loop */
    for (;;) {
        tuya_iot_yield(&ai_client);
    }
}

static THREAD_HANDLE s_app_thread = NULL;

static void app_thread(void *arg)
{
    (void)arg;
    user_main();
    tal_thread_delete(s_app_thread);
    s_app_thread = NULL;
}

void tuya_app_main(void)
{
    THREAD_CFG_T thrd = {
        .stackDepth = 8192,
        .priority   = 4,
        .thrdname   = "tuya_app_main",
        .psram_mode = 0,
    };
    tal_thread_create_and_start(&s_app_thread, NULL, NULL, app_thread, NULL, &thrd);
}
