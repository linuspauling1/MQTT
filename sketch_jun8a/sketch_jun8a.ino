#include <OneWire.h>
#include <DallasTemperature.h>
#include <ESP8266WiFi.h>

const int oneWireBus = D5;     
OneWire oneWire(oneWireBus);
DallasTemperature sensors(&oneWire);

void setup() {
  Serial.begin(115200);
  sensors.begin();
}

void loop() {
  sensors.requestTemperatures(); 
  float temperatureC = sensors.getTempCByIndex(1);
  Serial.println(temperatureC);
  delay(1000);
}