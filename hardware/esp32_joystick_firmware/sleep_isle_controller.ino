/*
 * ============================================================================
 *  ESP32-S3 N16R8 + PS2 摇杆 → 屿眠 Sleep Isle 硬件控制器 v2
 * ----------------------------------------------------------------------------
 *  信号定义（对应《软件与硬件交互逻辑说明》）:
 *    遥感按钮-前      → 摇杆前推    → {event:"joy_front"}   播放首次使用引导 引入.mp4
 *    遥感按钮-后      → 摇杆后拉    → {event:"joy_back"}    强制返回黑屏待机
 *    遥感按钮-下      → 摇杆按下    → {event:"joy_down"}    手机放入底座 → 播放 锁定.mp4
 *    停止闹钟按键信号 → 闹钟响起时摇杆按下 → {event:"alarm_stop"} 停止闹钟→欢呼
 *    （左右保留给模块切换：冥想/白噪音/呼吸/塔罗）
 *
 *  通信:
 *    HTTP POST /device/signal → gateway 状态机 → WS /ws/crystal 推给 sleep-isle.html
 *
 *  接线（同 v1）:
 *    VRX → GPIO 1（前后 ADC 轴）
 *    SW  → GPIO 4（按下=LOW）
 * ============================================================================
 */

#include <WiFi.h>
#include <HTTPClient.h>

// ============== 用户配置区 ==============
#define WIFI_SSID           "Haizol-Work"
#define WIFI_PASSWORD       "Haizol42167!"
#define GATEWAY_HOST        "192.169.29.23"
#define GATEWAY_PORT        3000
#define GATEWAY_PATH_SIGNAL "/device/signal"

#define JOY_VRX_PIN         1
#define JOY_SW_PIN          4

#define JOY_CENTER          2048
#define JOY_THRESHOLD       1500
#define JOY_DEBOUNCE_MS     500
#define SW_DEBOUNCE_MS      50
#define SW_LONGPRESS_MS     800      // 长按=停止闹钟（闹钟场景下摇杆按下即停，这里用短按即可）

// ============== 运行时状态 ==============
static bool     s_sw_pressed = false;
static int      s_last_joy_y = JOY_CENTER;
static bool     s_joy_armed  = true;
static unsigned long s_last_move_ms = 0;

// ============== WiFi ==============
static void connect_wifi() {
  Serial.printf("[WiFi] Connecting to %s", WIFI_SSID);
  WiFi.mode(WIFI_STA);
  WiFi.setSleep(false);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  uint32_t start = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - start < 30000) {
    Serial.print(".");
    delay(500);
  }
  if (WiFi.status() == WL_CONNECTED) {
    Serial.printf("\n[WiFi] Connected! IP=%s\n", WiFi.localIP().toString().c_str());
  } else {
    Serial.println("\n[WiFi] FAILED — rebooting");
    delay(5000);
    ESP.restart();
  }
}

// ============== 发送硬件信号 ==============
static void post_signal(const char* event) {
  if (WiFi.status() != WL_CONNECTED) return;
  HTTPClient http;
  String url = String("http://") + GATEWAY_HOST + ":" + GATEWAY_PORT + GATEWAY_PATH_SIGNAL;
  if (!http.begin(url)) return;
  http.addHeader("Content-Type", "application/json");
  http.setTimeout(500);
  // 注意：是否为"停止闹钟"由 gateway 根据"闹钟正在响"判断，硬件不自行推断
  String body = String("{\"device_id\":\"crystal_ball_01\",\"event\":\"") + event + "\"}";
  int code = http.POST(body);
  if (code > 0 && code != 200) {
    Serial.printf("[HTTP] POST -> %d: %s\n", code, http.getString().c_str());
  } else if (code <= 0) {
    Serial.printf("[HTTP] POST error: %s\n", http.errorToString(code).c_str());
  }
  http.end();
}

// ============== 摇杆前后检测（VRX 轴） ==============
static void poll_joystick_y() {
  int y = analogRead(JOY_VRX_PIN);

  if (abs(y - JOY_CENTER) < JOY_THRESHOLD / 2) {
    s_joy_armed = true;
    return;
  }
  if (!s_joy_armed) return;

  unsigned long now = millis();
  if (now - s_last_move_ms < JOY_DEBOUNCE_MS) return;

  if (y > JOY_CENTER + JOY_THRESHOLD) {
    // 前推（ADC 值变大方向取决于接线，现场可用串口日志校准对调）
    s_joy_armed = false;
    s_last_move_ms = now;
    Serial.printf("[Joy] Y=%d → FRONT → 引入视频\n", y);
    post_signal("joy_front");
  } else if (y < JOY_CENTER - JOY_THRESHOLD) {
    s_joy_armed = false;
    s_last_move_ms = now;
    Serial.printf("[Joy] Y=%d → BACK → 黑屏待机\n", y);
    post_signal("joy_back");
  }
}

// ============== 摇杆按下检测（底座信号 / 停止闹钟信号） ==============
static void poll_joystick_sw() {
  bool cur = (digitalRead(JOY_SW_PIN) == LOW);
  static unsigned long last_change_ms = 0;
  unsigned long now = millis();
  if (cur != s_sw_pressed) {
    if (now - last_change_ms >= SW_DEBOUNCE_MS) {
      s_sw_pressed = cur;
      last_change_ms = now;
      if (s_sw_pressed) {
        // 语义由网关判定：AI待机中=底座信号(锁定)；闹钟响时=停止闹钟
        Serial.println("[Joy] SW pressed → joy_down (gateway 判定语义)");
        post_signal("joy_down");
      }
    }
  } else {
    last_change_ms = now;
  }
}

// ============== setup / loop ==============
void setup() {
  Serial.begin(115200);
  delay(200);
  Serial.println("\n=== Sleep Isle Hardware Controller v2 ===");
  pinMode(JOY_VRX_PIN, INPUT);
  analogReadResolution(12);
  pinMode(JOY_SW_PIN, INPUT_PULLUP);
  connect_wifi();
  Serial.println("=== Ready. Front=onboarding, Back=black-standby, Press=dock/alarm-stop ===\n");
}

void loop() {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("[WiFi] lost, reconnecting...");
    connect_wifi();
  }
  poll_joystick_y();
  poll_joystick_sw();
  delay(10);
}
