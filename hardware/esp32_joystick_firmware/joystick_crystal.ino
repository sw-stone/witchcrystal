/*
 * ============================================================================
 *  ESP32-S3 N16R8 + PS2 摇杆 + 麦克风 → 水晶球测试界面硬件控制器
 * ----------------------------------------------------------------------------
 *  硬件接线（推荐，可改）:
 *    PS2 摇杆 VRX  → GPIO 1   (ADC1_CH0)
 *    PS2 摇杆 VRY  → GPIO 2   (ADC1_CH1)  [本固件未使用，可留空]
 *    PS2 摇杆 SW   → GPIO 4   (内部上拉，按下=低电平)
 *    PS2 摇杆 VCC  → 3V3
 *    PS2 摇杆 GND  → GND
 *    麦克风 AO     → GPIO 3   (ADC1_CH2, 本固件未使用——ASR 走 web 浏览器)
 *
 *  交互逻辑:
 *    1. 左右摇动 PS2 摇杆  → 切换水晶球模式（standby/白噪音/呼吸/冥想/占卜/闹钟）
 *    2. 按下摇杆长按        → 开始语音输入（POST /device/state {listening:true}）
 *    3. 松开摇杆            → 结束语音输入（POST /device/state {listening:false}）
 *
 *  通信:
 *    HTTP POST 到 gateway 的 /device/state，gateway 通过 WebSocket /ws/crystal
 *    广播给 web 端"测试" tab，web 端收到后自动启停麦克风 + ASR + LLM + TTS。
 *
 *  依赖:
 *    Arduino-ESP32 板支持包 2.0.14+（支持 ESP32-S3 N16R8）
 *    库：HTTPClient（Arduino-ESP32 内置）
 *
 *  部署:
 *    1. Arduino IDE → 板选择 "ESP32S3 Dev Module"
 *    2. 上传到 ESP32-S3 后，串口 115200 监视器看日志
 *    3. 打开 web 端测试 tab，操作摇杆即可联动
 * ============================================================================
 */

#include <WiFi.h>
#include <HTTPClient.h>

// ============== 用户配置区（按需修改）==============
#define WIFI_SSID           "Haizol-Work"
#define WIFI_PASSWORD       "Haizol42167!"

// gateway 地址（电脑本机运行 gateway 服务时填电脑内网 IP）
// 电脑 IP 可在 Mac 上 `ifconfig | grep inet` 查，手机/电脑同 WiFi 即可
#define GATEWAY_HOST        "192.169.29.23"
#define GATEWAY_PORT        3000
#define GATEWAY_PATH_STATE  "/device/state"

// PS2 摇杆引脚
#define JOY_VRX_PIN         1
#define JOY_SW_PIN          4

// 摇杆阈值与防抖
#define JOY_CENTER          2048   // 中位 ADC 值（12-bit ADC: 0-4095）
#define JOY_THRESHOLD       1500   // 偏离中位多少算"摇动"
#define JOY_DEBOUNCE_MS     400    // 模式切换最小间隔（防抖）
#define SW_DEBOUNCE_MS      50     // 按键消抖
#define STATE_POST_INTERVAL 50     // 状态上报最小间隔（避免刷爆网关）

// 6 个模式（与 web 端 CB_MODE_NAMES 一致）
static const char* MODES[] = {
  "standby", "whitenoise", "breathing", "meditation", "divination", "alarm"
};
static const int MODE_COUNT = sizeof(MODES) / sizeof(MODES[0]);
// ====================================================================

// 运行时状态
static int  s_mode_idx       = 0;             // 当前模式索引
static bool s_listening      = false;         // 当前是否在语音输入
static bool s_sw_pressed     = false;         // 摇杆按键当前是否按下
static unsigned long s_last_mode_switch_ms = 0;
static unsigned long s_last_state_post_ms  = 0;
static int  s_last_joy_x      = JOY_CENTER;   // 上次 X 轴读数（用于检测回到中位）
static bool s_joy_armed      = true;          // 摇杆回到中位后才能再次触发（防连击）

// ============== WiFi 连接 ==============
static void connect_wifi() {
  Serial.printf("[WiFi] Connecting to %s", WIFI_SSID);
  WiFi.mode(WIFI_STA);
  WiFi.setSleep(false);  // 降低延迟
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  uint32_t start = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - start < 30000) {
    Serial.print(".");
    delay(500);
  }
  if (WiFi.status() == WL_CONNECTED) {
    Serial.printf("\n[WiFi] Connected! IP=%s RSSI=%d dBm\n",
                  WiFi.localIP().toString().c_str(), WiFi.RSSI());
  } else {
    Serial.println("\n[WiFi] FAILED — rebooting in 5s");
    delay(5000);
    ESP.restart();
  }
}

// ============== HTTP POST /device/state ==============
static void post_state(const char* mode, bool listening) {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("[HTTP] WiFi down, skip");
    return;
  }
  if (millis() - s_last_state_post_ms < STATE_POST_INTERVAL) return;
  s_last_state_post_ms = millis();

  HTTPClient http;
  String url = String("http://") + GATEWAY_HOST + ":" + GATEWAY_PORT + GATEWAY_PATH_STATE;
  if (!http.begin(url)) {
    Serial.println("[HTTP] begin failed");
    return;
  }
  http.addHeader("Content-Type", "application/json");
  http.setTimeout(500);

  // 构造 JSON: {"device_id":"crystal_ball_01","mode":"...","listening":...,"led":"...","ai_thinking":false}
  String body = String("{\"device_id\":\"crystal_ball_01\",\"mode\":\"") + mode +
                "\",\"listening\":" + (listening ? "true" : "false") +
                ",\"led\":\"" + (listening ? "blue" : "white") + "\"" +
                ",\"ai_thinking\":false}";

  int code = http.POST(body);
  if (code > 0) {
    if (code != 200) {
      Serial.printf("[HTTP] POST -> %d: %s\n", code, http.getString().c_str());
    }
  } else {
    Serial.printf("[HTTP] POST error: %s\n", http.errorToString(code).c_str());
  }
  http.end();
}

// ============== 摇杆按键检测（按下/松开事件）==============
static void poll_joystick_sw() {
  // SW 引脚内部上拉，按下=LOW
  bool cur_pressed = (digitalRead(JOY_SW_PIN) == LOW);

  // 上升沿/下降沿检测 + 消抖
  static unsigned long last_change_ms = 0;
  unsigned long now = millis();
  if (cur_pressed != s_sw_pressed) {
    if (now - last_change_ms >= SW_DEBOUNCE_MS) {
      s_sw_pressed = cur_pressed;
      last_change_ms = now;
      if (s_sw_pressed) {
        // 按下事件 → 开始语音输入
        s_listening = true;
        Serial.println("[Joy] SW pressed → listening=true");
        post_state(MODES[s_mode_idx], s_listening);
      } else {
        // 松开事件 → 结束语音输入
        s_listening = false;
        Serial.println("[Joy] SW released → listening=false");
        post_state(MODES[s_mode_idx], s_listening);
      }
    }
  } else {
    last_change_ms = now;
  }
}

// ============== 摇杆 X 轴检测（左右切换模式）==============
static void poll_joystick_x() {
  int x = analogRead(JOY_VRX_PIN);

  // 必须先回到中位才能再次触发（一次摇动只切一次模式）
  if (abs(x - JOY_CENTER) < JOY_THRESHOLD / 2) {
    s_joy_armed = true;
    return;
  }
  if (!s_joy_armed) return;

  unsigned long now = millis();
  if (now - s_last_mode_switch_ms < JOY_DEBOUNCE_MS) return;

  if (x < JOY_CENTER - JOY_THRESHOLD) {
    // 向左摇 → 上一模式
    s_mode_idx = (s_mode_idx - 1 + MODE_COUNT) % MODE_COUNT;
    s_joy_armed = false;
    s_last_mode_switch_ms = now;
    Serial.printf("[Joy] X=%d → LEFT → mode=%s\n", x, MODES[s_mode_idx]);
    post_state(MODES[s_mode_idx], s_listening);
  } else if (x > JOY_CENTER + JOY_THRESHOLD) {
    // 向右摇 → 下一模式
    s_mode_idx = (s_mode_idx + 1) % MODE_COUNT;
    s_joy_armed = false;
    s_last_mode_switch_ms = now;
    Serial.printf("[Joy] X=%d → RIGHT → mode=%s\n", x, MODES[s_mode_idx]);
    post_state(MODES[s_mode_idx], s_listening);
  }
}

// ============== setup / loop ==============
void setup() {
  Serial.begin(115200);
  delay(200);
  Serial.println("\n=== ESP32-S3 Joystick Crystal Ball Controller ===");

  // 摇杆引脚
  pinMode(JOY_VRX_PIN, INPUT);
  analogReadResolution(12);  // 12-bit ADC: 0-4095
  pinMode(JOY_SW_PIN, INPUT_PULLUP);

  // WiFi
  connect_wifi();

  // 启动时上报一次初始状态
  Serial.printf("[Init] reporting initial mode=%s\n", MODES[s_mode_idx]);
  post_state(MODES[s_mode_idx], s_listening);

  Serial.println("=== Ready. Left/Right=switch mode, Press=voice ===\n");
}

void loop() {
  // WiFi 掉线重连
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("[WiFi] lost, reconnecting...");
    connect_wifi();
  }

  poll_joystick_x();
  poll_joystick_sw();

  delay(10);  // 100Hz 轮询，足够低延迟
}
