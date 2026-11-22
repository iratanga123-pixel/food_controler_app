/*
  Smart Food Loss Prevention - sensor node firmware (runs in the Wokwi ESP32 simulator)

  Simulated parts:
    DHT22         -> air temperature and relative humidity   (pin D15)
    DS18B20       -> temperature inside the grain            (pin D4)
    Potentiometer -> stands in for the capacitive grain moisture probe (pin D34)

  Turn the potentiometer and click the DHT22 / DS18B20 during the simulation to change values.
  Every reading is printed as JSON on the Serial Monitor. If you add a ThingSpeak write key,
  readings are also sent to the internet through Wokwi's virtual Wi-Fi.
*/
#include <WiFi.h>
#include <HTTPClient.h>
#include "DHTesp.h"
#include <OneWire.h>
#include <DallasTemperature.h>

const char* STORE_ID = "NYG01";
const char* THINGSPEAK_KEY = "";          // optional: your ThingSpeak channel write key
const unsigned long INTERVAL_MS = 5000;   // a real node would use 30-60 minutes

const int DHT_PIN = 15, ONEWIRE_PIN = 4, MOISTURE_PIN = 34;
// Calibration of the moisture probe: raw ADC value at two known moisture levels.
// With real hardware you measure these against a commercial grain moisture meter.
const float RAW_DRY = 0, MOIST_DRY = 8.0;      // raw reading at 8% moisture
const float RAW_WET = 4095, MOIST_WET = 25.0;  // raw reading at 25% moisture
const float SAFE_MOISTURE = 13.5;              // maize

DHTesp dht;
OneWire oneWire(ONEWIRE_PIN);
DallasTemperature grainProbe(&oneWire);

float rawToMoisture(int raw) {
  return MOIST_DRY + (raw - RAW_DRY) * (MOIST_WET - MOIST_DRY) / (RAW_WET - RAW_DRY);
}

void setup() {
  Serial.begin(115200);
  dht.setup(DHT_PIN, DHTesp::DHT22);
  grainProbe.begin();
  WiFi.begin("Wokwi-GUEST", "", 6);
  Serial.print("Connecting to Wi-Fi");
  for (int i = 0; i < 20 && WiFi.status() != WL_CONNECTED; i++) { delay(250); Serial.print("."); }
  Serial.println(WiFi.status() == WL_CONNECTED ? " connected" : " offline (serial only)");
}

void loop() {
  TempAndHumidity air = dht.getTempAndHumidity();
  grainProbe.requestTemperatures();
  float grainTemp = grainProbe.getTempCByIndex(0);
  float moisture = rawToMoisture(analogRead(MOISTURE_PIN));

  // Simple on-device warning, so the store still gets a local alarm when the network is down.
  const char* local = moisture > SAFE_MOISTURE + 1.5 || air.humidity > 80 ? "HIGH"
                    : moisture > SAFE_MOISTURE || air.humidity > 70 ? "WATCH" : "OK";

  char json[220];
  snprintf(json, sizeof(json),
    "{\"store_id\":\"%s\",\"air_temp\":%.1f,\"humidity\":%.1f,\"grain_moisture\":%.1f,\"grain_temp\":%.1f,\"local_risk\":\"%s\"}",
    STORE_ID, air.temperature, air.humidity, moisture, grainTemp, local);
  Serial.println(json);

  if (strlen(THINGSPEAK_KEY) > 0 && WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    String url = String("http://api.thingspeak.com/update?api_key=") + THINGSPEAK_KEY +
                 "&field1=" + air.temperature + "&field2=" + air.humidity +
                 "&field3=" + moisture + "&field4=" + grainTemp;
    http.begin(url);
    int code = http.GET();
    Serial.printf("ThingSpeak upload: HTTP %d\n", code);
    http.end();
  }
  delay(INTERVAL_MS);
}
