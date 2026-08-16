/**
 * @file sm_joystick.c
 * @brief PS2 双轴摇杆驱动实现（T5AI-Core）
 *
 * T5-E1 模组 ADC 通道映射（全部挂 TUYA_ADC_NUM_0）：
 *   P25 → ch1   P24 → ch2
 * SW 用 P20（数字 GPIO，按下为低），不复用 ADC。
 */
#include "sm_joystick.h"
#include "tkl_adc.h"
#include "tkl_gpio.h"
#include "tal_api.h"

/***********************************************************
 ************************macro define************************
 ***********************************************************/
#define JOY_VRX_PIN             TUYA_GPIO_NUM_25
#define JOY_VRY_PIN             TUYA_GPIO_NUM_24
#define JOY_SW_PIN              TUYA_GPIO_NUM_20

#define JOY_ADC_PORT            TUYA_ADC_NUM_0
#define JOY_VRX_CH_ID           1   /* P25 = ADC ch1 */
#define JOY_VRY_CH_ID           2   /* P24 = ADC ch2 */

#define JOY_ADC_WIDTH           12
#define JOY_ADC_FREQ            10000
#define JOY_ADC_REF_VOL         3300

#define JOY_DEADZONE            600
#define JOY_DEBOUNCE_MS         300
#define SW_LONG_PRESS_MS        800
#define SW_DEBOUNCE_MS          100
#define JOY_ADC_CENTER          2048
#define JOY_ADC_FAIL_MAX        20

/***********************************************************
 ***********************variable define**********************
 ***********************************************************/
static bool     s_inited      = false;
static uint32_t s_last_evt_ms = 0;
static uint32_t s_sw_down_ms  = 0;
static bool     s_sw_was_down = false;
static uint8_t  s_adc_fail_cnt = 0;

/***********************************************************
 ***********************function define**********************
 ***********************************************************/
OPERATE_RET app_joystick_init(void)
{
    OPERATE_RET rt = OPRT_OK;

    /* ADC：ch_list 同时含 ch1(P25)/ch2(P24)，单次转换模式 */
    TUYA_ADC_BASE_CFG_T adc_cfg = {0};
    adc_cfg.ch_list.bits.ch_1 = 1;
    adc_cfg.ch_list.bits.ch_2 = 1;
    adc_cfg.ch_nums           = 2;
    adc_cfg.width             = JOY_ADC_WIDTH;
    adc_cfg.freq              = JOY_ADC_FREQ;
    adc_cfg.type              = TUYA_ADC_EXTERNAL_SAMPLE_VOL;
    adc_cfg.mode              = TUYA_ADC_SINGLE;
    adc_cfg.conv_cnt          = 1;
    adc_cfg.ref_vol           = JOY_ADC_REF_VOL;

    TUYA_CALL_ERR_RETURN(tkl_adc_init(JOY_ADC_PORT, &adc_cfg));

    /* SW：输入 + 上拉（按下为低）*/
    TUYA_GPIO_BASE_CFG_T sw_cfg = {
        .mode   = TUYA_GPIO_PULLUP,
        .direct = TUYA_GPIO_INPUT,
        .level  = TUYA_GPIO_LEVEL_HIGH,
    };
    TUYA_CALL_ERR_RETURN(tkl_gpio_init(JOY_SW_PIN, &sw_cfg));

    s_inited = true;
    PR_NOTICE("[Joy] init: VRx=P25(ch1) VRy=P24(ch2) SW=P20");
    return OPRT_OK;
}

/* ADC 失败时返回中点值（而非 0），避免被 poll 误判为 LEFT */
static uint16_t __joy_adc_read(uint8_t ch_id)
{
    int32_t val = 0;
    if (OPRT_OK != tkl_adc_read_single_channel(JOY_ADC_PORT, ch_id, &val)) {
        val = 0;
    }
    if (val == 0) {
        if (s_adc_fail_cnt < JOY_ADC_FAIL_MAX) s_adc_fail_cnt++;
    } else {
        s_adc_fail_cnt = 0;
    }
    return (val == 0) ? JOY_ADC_CENTER : (uint16_t)val;
}

uint16_t app_joystick_vrx(void)
{
    if (!s_inited) return JOY_ADC_CENTER;
    return __joy_adc_read(JOY_VRX_CH_ID);
}

uint16_t app_joystick_vry(void)
{
    if (!s_inited) return JOY_ADC_CENTER;
    return __joy_adc_read(JOY_VRY_CH_ID);
}

bool app_joystick_sw_pressed(void)
{
    if (!s_inited) return false;
    TUYA_GPIO_LEVEL_E lv = TUYA_GPIO_LEVEL_HIGH;
    tkl_gpio_read(JOY_SW_PIN, &lv);
    return (lv == TUYA_GPIO_LEVEL_LOW);
}

joy_event_t app_joystick_poll(void)
{
    if (!s_inited) return JOY_NONE;

    uint32_t now = tal_system_get_millisecond();
    bool     sw_down = app_joystick_sw_pressed();

    /* ---- SW：按下记时刻，松开按时长判短/长按 ---- */
    if (sw_down && !s_sw_was_down) {
        s_sw_down_ms  = now;
        s_sw_was_down = true;
    } else if (!sw_down && s_sw_was_down) {
        uint32_t dur = now - s_sw_down_ms;
        s_sw_was_down = false;
        if (now - s_last_evt_ms >= SW_DEBOUNCE_MS) {
            s_last_evt_ms = now;
            if (dur >= SW_LONG_PRESS_MS) {
                PR_DEBUG("[Joy] SW long press (%dms)", dur);
                return JOY_LONG_PRESS;
            }
            PR_DEBUG("[Joy] SW short press (%dms)", dur);
            return JOY_PRESS;
        }
        goto axis;
    }

axis:
    /* ---- 方向：VRx/VRy 超出 deadzone 才触发，300ms 消抖 ---- */
    if (now - s_last_evt_ms < JOY_DEBOUNCE_MS) {
        return JOY_NONE;
    }
    /* ADC 持续失败（摇杆未接/被占用）：禁用方向事件，仅保留 SW 按键 */
    if (s_adc_fail_cnt >= JOY_ADC_FAIL_MAX) {
        static bool s_adc_fail_logged = false;
        if (!s_adc_fail_logged) {
            s_adc_fail_logged = true;
            PR_WARN("[Joy] ADC persist fail, axis disabled (SW only)");
        }
        return JOY_NONE;
    }
    uint16_t x = app_joystick_vrx();
    uint16_t y = app_joystick_vry();

    if (x < 2048 - JOY_DEADZONE) {
        s_last_evt_ms = now;
        PR_DEBUG("[Joy] LEFT  VRx=%d", x);
        return JOY_LEFT;
    }
    if (x > 2048 + JOY_DEADZONE) {
        s_last_evt_ms = now;
        PR_DEBUG("[Joy] RIGHT VRx=%d", x);
        return JOY_RIGHT;
    }
    if (y > 2048 + JOY_DEADZONE) {
        s_last_evt_ms = now;
        PR_DEBUG("[Joy] UP    VRy=%d", y);
        return JOY_UP;
    }
    if (y < 2048 - JOY_DEADZONE) {
        s_last_evt_ms = now;
        PR_DEBUG("[Joy] DOWN  VRy=%d", y);
        return JOY_DOWN;
    }

    return JOY_NONE;
}
