/**
 * @file sm_button.c
 * @brief 3 路按钮驱动
 *   - 前：P29 板级按钮，通过 tdl_button 订阅（避免与板级驱动冲突，参考 mbti_divination 经验）
 *   - 后：扩展 GPIO + IRQ + 软件去抖
 *   - 下：扩展 GPIO 电平触发（手机在位检测）
 */

#include "sm_button.h"
#include "sm_state_machine.h"
#include "tal_api.h"
#include "tal_sw_timer.h"
#include "tkl_gpio.h"
#include "tdl_button_manage.h"
#include "tuya_log.h"

/* 兜底默认值（Kconfig 注入的 CONFIG_* 优先）
 * GPIO 分配已按官方原理图 T5AI-Core_V101-SCH 定稿（docs/hardware/pinmap.md）：
 *   按钮-前 = P29 板载（tdl_button）
 *   按钮-后 = GPIO_3（J1 pin 16）
 *   按钮-下 = GPIO_4（J1 pin 21，电平在位检测）
 */
#ifndef CONFIG_BUTTON_NAME
#define CONFIG_BUTTON_NAME "ai_chat_button"
#endif
#ifndef CONFIG_BTN_BACK_GPIO
#define CONFIG_BTN_BACK_GPIO 3
#endif
#ifndef CONFIG_BTN_DOWN_GPIO
#define CONFIG_BTN_DOWN_GPIO 4
#endif
#ifndef CONFIG_BTN_DEBOUNCE_MS
#define CONFIG_BTN_DEBOUNCE_MS 50
#endif
#ifndef CONFIG_BTN_DOWN_DEBOUNCE_MS
#define CONFIG_BTN_DOWN_DEBOUNCE_MS 100
#endif

#define TAG "[BTN] "

static TDL_BUTTON_HANDLE s_front_handle = NULL;
static TIMER_ID          s_back_debounce_timer = NULL;
static TIMER_ID          s_down_debounce_timer = NULL;
static bool              s_back_pressed = false;
static bool              s_down_pressed = false;
static bool              s_down_curr    = false;

/* ===== 按钮-前：板级 P29 via tdl_button ===== */
static void front_btn_cb(char *name, TDL_BUTTON_TOUCH_EVENT_E event, void *argc)
{
    (void)name; (void)argc;
    sm_event_t e = { SM_EVT_NONE, 0, NULL };
    if (event == TDL_BUTTON_PRESS_SINGLE_CLICK) {
        e.id = SM_EVT_BTN_FRONT;
    } else if (event == TDL_BUTTON_LONG_PRESS_START) {
        /* 长按在 S8 闹钟响铃时也作为停止键 */
        e.id = SM_EVT_BTN_FRONT;
    }
    if (e.id != SM_EVT_NONE) {
        sm_fsm_dispatch(&e);
    }
}

/* ===== 按钮-后：扩展 GPIO IRQ + 软件去抖 ===== */
static void back_debounce_cb(TIMER_ID tid, void *arg)
{
    (void)tid; (void)arg;
    TUYA_GPIO_LEVEL_E lv;
    if (tkl_gpio_read(CONFIG_BTN_BACK_GPIO, &lv) != OPRT_OK) return;
    bool pressed = (lv == TUYA_GPIO_LEVEL_LOW);  /* 低有效 */

    if (pressed && !s_back_pressed) {
        s_back_pressed = true;
        sm_event_t e = { SM_EVT_BTN_BACK, 0, NULL };
        sm_fsm_dispatch(&e);
        PR_INFO(TAG "BACK pressed (force standby)");
    } else if (!pressed && s_back_pressed) {
        s_back_pressed = false;
    }
}

static void back_gpio_irq_cb(void *args)
{
    (void)args;
    /* IRQ 上下文不直接处理，启动去抖定时器 */
    tal_sw_timer_start(s_back_debounce_timer, CONFIG_BTN_DEBOUNCE_MS, TAL_TIMER_ONCE);
}

/* ===== 按钮-下：电平触发的手机在位检测 ===== */
static void down_debounce_cb(TIMER_ID tid, void *arg)
{
    (void)tid; (void)arg;
    TUYA_GPIO_LEVEL_E lv;
    if (tkl_gpio_read(CONFIG_BTN_DOWN_GPIO, &lv) != OPRT_OK) return;
    bool pressed = (lv == TUYA_GPIO_LEVEL_LOW);  /* 压下=低 */

    if (pressed != s_down_curr) {
        s_down_curr = pressed;
        sm_event_t e = { pressed ? SM_EVT_BTN_DOWN_PRESSED : SM_EVT_BTN_DOWN_RELEASED, 0, NULL };
        sm_fsm_dispatch(&e);
        PR_INFO(TAG "DOWN %s (dock %s)", pressed ? "pressed" : "released",
                pressed ? "IN" : "OUT");
    }
}

static void down_gpio_irq_cb(void *args)
{
    (void)args;
    tal_sw_timer_start(s_down_debounce_timer, CONFIG_BTN_DOWN_DEBOUNCE_MS, TAL_TIMER_ONCE);
}

/* ===== 周期性轮询按钮-下（电平触发，需要稳定状态而非边沿）===== */
static void down_poll_cb(TIMER_ID tid, void *arg)
{
    (void)tid; (void)arg;
    down_debounce_cb(tid, arg);
    tal_sw_timer_start(s_down_debounce_timer, CONFIG_BTN_DOWN_DEBOUNCE_MS * 5, TAL_TIMER_ONCE);
}

/* ===== 初始化 ===== */
static int init_back_button(void)
{
    TUYA_GPIO_BASE_CFG_T cfg = {
        .mode   = TUYA_GPIO_PULLUP,
        .direct = TUYA_GPIO_INPUT,
        .level  = TUYA_GPIO_LEVEL_HIGH,
    };
    OPERATE_RET rt = tkl_gpio_init(CONFIG_BTN_BACK_GPIO, &cfg);
    if (rt != OPRT_OK) {
        PR_ERR(TAG "BACK gpio init failed: %d", rt);
        return -1;
    }
    TUYA_GPIO_IRQ_T irq = {
        .mode = TUYA_GPIO_IRQ_RISE_FALL,
        .cb   = back_gpio_irq_cb,
        .arg  = NULL,
    };
    rt = tkl_gpio_irq_init(CONFIG_BTN_BACK_GPIO, &irq);
    if (rt != OPRT_OK) {
        PR_ERR(TAG "BACK irq init failed: %d", rt);
        return -1;
    }
    tkl_gpio_irq_enable(CONFIG_BTN_BACK_GPIO);
    tal_sw_timer_create(back_debounce_cb, NULL, &s_back_debounce_timer);
    PR_INFO(TAG "BACK button on GPIO %d (expansion)", CONFIG_BTN_BACK_GPIO);
    return 0;
}

static int init_down_button(void)
{
    TUYA_GPIO_BASE_CFG_T cfg = {
        .mode   = TUYA_GPIO_PULLUP,
        .direct = TUYA_GPIO_INPUT,
        .level  = TUYA_GPIO_LEVEL_HIGH,
    };
    OPERATE_RET rt = tkl_gpio_init(CONFIG_BTN_DOWN_GPIO, &cfg);
    if (rt != OPRT_OK) {
        PR_ERR(TAG "DOWN gpio init failed: %d", rt);
        return -1;
    }
    /* 初始化时读一次当前电平（手机可能已在座）*/
    TUYA_GPIO_LEVEL_E lv;
    if (tkl_gpio_read(CONFIG_BTN_DOWN_GPIO, &lv) == OPRT_OK) {
        s_down_curr    = (lv == TUYA_GPIO_LEVEL_LOW);
        s_down_pressed = s_down_curr;
    }

    TUYA_GPIO_IRQ_T irq = {
        .mode = TUYA_GPIO_IRQ_RISE_FALL,
        .cb   = down_gpio_irq_cb,
        .arg  = NULL,
    };
    rt = tkl_gpio_irq_init(CONFIG_BTN_DOWN_GPIO, &irq);
    if (rt != OPRT_OK) {
        PR_ERR(TAG "DOWN irq init failed: %d", rt);
        return -1;
    }
    tkl_gpio_irq_enable(CONFIG_BTN_DOWN_GPIO);

    /* 额外周期轮询，防止 IRQ 漏触发 */
    tal_sw_timer_create(down_poll_cb, NULL, &s_down_debounce_timer);
    tal_sw_timer_start(s_down_debounce_timer, CONFIG_BTN_DOWN_DEBOUNCE_MS * 5, TAL_TIMER_ONCE);
    PR_INFO(TAG "DOWN button on GPIO %d (dock detect, initial=%d)", CONFIG_BTN_DOWN_GPIO, s_down_curr);
    return 0;
}

int sm_button_init(void)
{
    /* 按钮-前：通过 tdl_button 订阅板级 "ai_chat_button"（P29）*/
    TDL_BUTTON_CFG_T btn_cfg = {
        .long_start_valid_time     = 1000,
        .long_keep_timer           = 500,
        .button_debounce_time      = 50,
        .button_repeat_valid_count = 2,
        .button_repeat_valid_time  = 300,
    };
    OPERATE_RET rt = tdl_button_create((char *)CONFIG_BUTTON_NAME, &btn_cfg, &s_front_handle);
    if (rt != OPRT_OK) {
        PR_ERR(TAG "front tdl_button_create failed: %d", rt);
        return -1;
    }
    tdl_button_event_register(s_front_handle, TDL_BUTTON_PRESS_SINGLE_CLICK, front_btn_cb);
    tdl_button_event_register(s_front_handle, TDL_BUTTON_LONG_PRESS_START,  front_btn_cb);
    PR_INFO(TAG "FRONT button subscribed via tdl_button (%s)", CONFIG_BUTTON_NAME);

    if (init_back_button() != 0) return -1;
    if (init_down_button()  != 0) return -1;

    /* 若开机时手机已在座，主动投递一次 DOWN_PRESSED */
    if (s_down_curr) {
        sm_event_t e = { SM_EVT_BTN_DOWN_PRESSED, 0, NULL };
        sm_fsm_dispatch(&e);
    }
    return 0;
}

int sm_button_start(void)
{
    /* tdl_button 已自带扫描任务，GPIO IRQ 即时响应，无需额外线程 */
    return 0;
}

bool sm_button_down_is_pressed(void)
{
    return s_down_curr;
}
