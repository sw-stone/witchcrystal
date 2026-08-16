/**
 * @file sm_led.c
 * @brief LED 灯效引擎：P9 / PWM ch9（复用板级 TUYA_T5AI_CORE.config）
 *   - 呼吸 / 闪烁 / 全亮 / 熄灭 / 引导 / 塔罗转场 / 闹钟 / 庆祝
 *   - 软件 timer 驱动渐变，回调内严禁阻塞
 */

#include "sm_led.h"
#include "tkl_pwm.h"
#include "tal_api.h"
#include "tal_sw_timer.h"
#include "tuya_log.h"

#define TAG "[LED] "

#define LED_PWM_CHANNEL   TUYA_PWM_NUM_9
#define LED_GPIO_PIN      TUYA_GPIO_NUM_9
#define LED_TIMER_MS      20
#define LED_BREATHE_STEPS 50

static sm_led_effect_t s_cur = SM_LED_OFF;
static uint8_t         s_brightness = 50;
static TIMER_ID        s_timer = NULL;
static uint8_t         s_step = 0;
static bool            s_up = true;
static bool            s_inited = false;

static TUYA_PWM_BASE_CFG_T s_pwm = {
    .polarity  = TUYA_PWM_POSITIVE,
    .count_mode = TUYA_PWM_CNT_UP,
    .duty      = 0,
    .cycle     = 10000,
    .frequency = 1000,
};

static void led_set_duty(uint32_t duty)
{
    if (duty > 10000) duty = 10000;
    s_pwm.duty = duty;
    tkl_pwm_info_set(LED_PWM_CHANNEL, &s_pwm);
    if (duty == 0) tkl_pwm_stop(LED_PWM_CHANNEL);
    else           tkl_pwm_start(LED_PWM_CHANNEL);
}

static void led_timer_cb(TIMER_ID tid, void *arg)
{
    (void)tid; (void)arg;
    switch (s_cur) {
    case SM_LED_OFF:
    case SM_LED_SLEEP:
        /* 静态低亮度 / 熄灭 */
        break;
    case SM_LED_GUIDE:
    case SM_LED_DOCKED:
    case SM_LED_CHEER:
        /* 常亮 */
        break;
    case SM_LED_BREATH: {
        /* 0..100..0 渐变 */
        uint32_t d = (uint32_t)s_step * 10000 / LED_BREATHE_STEPS;
        if (!s_up) d = 10000 - d;
        led_set_duty(d * s_brightness / 100);
        if (s_up) { s_step++; if (s_step >= LED_BREATHE_STEPS) { s_step = LED_BREATHE_STEPS; s_up = false; } }
        else      { if (s_step == 0) { s_up = true; } else s_step--; }
        break;
    }
    case SM_LED_SPEAKING:
    case SM_LED_TAROT: {
        /* 慢速闪烁 */
        s_step = (s_step + 1) % 20;
        led_set_duty((s_step < 10 ? 8000 : 1000) * s_brightness / 100);
        break;
    }
    case SM_LED_ALARM: {
        /* 快速全亮闪烁 */
        s_step = (s_step + 1) % 8;
        led_set_duty(s_step < 4 ? 10000 : 0);
        break;
    }
    default: break;
    }
}

int sm_led_init(void)
{
    if (s_inited) return 0;

    OPERATE_RET rt = tkl_pwm_init(LED_PWM_CHANNEL, &s_pwm);
    if (rt != OPRT_OK) {
        PR_ERR(TAG "pwm init failed: %d", rt);
        return -1;
    }
    tal_sw_timer_create(led_timer_cb, NULL, &s_timer);
    tal_sw_timer_start(s_timer, LED_TIMER_MS, TAL_TIMER_CYCLE);
    s_inited = true;
    PR_INFO(TAG "init on PWM ch9 / GPIO P9");
    return 0;
}

void sm_led_set_effect(sm_led_effect_t e)
{
    if (e >= SM_LED_MAX || e == s_cur) return;
    PR_INFO(TAG "effect %d -> %d", s_cur, e);
    s_cur = e;
    s_step = 0;
    s_up = true;
    switch (e) {
    case SM_LED_OFF:
        led_set_duty(0);
        break;
    case SM_LED_GUIDE:
    case SM_LED_DOCKED:
    case SM_LED_CHEER:
        led_set_duty(8000 * s_brightness / 100);
        break;
    case SM_LED_SLEEP:
        led_set_duty(1500 * s_brightness / 100);
        break;
    case SM_LED_BREATH:
    case SM_LED_SPEAKING:
    case SM_LED_TAROT:
    case SM_LED_ALARM:
        /* 由 timer 推动渐变 */
        break;
    default: break;
    }
}

void sm_led_set_brightness(uint8_t percent)
{
    if (percent > 100) percent = 100;
    s_brightness = percent;
}
