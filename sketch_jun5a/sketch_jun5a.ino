#include "DHT.h"
#define senzor_umiditate_temperatura DHT11
const int temperatura1 = D6;
const int temperatura2 = D7;
DHT dht1 = DHT(temperatura1,senzor_umiditate_temperatura);
DHT dht2 = DHT(temperatura2,senzor_umiditate_temperatura);
void setup() {
  Serial.begin(115200);
  dht1.begin();
  dht2.begin();
  Serial.println();
}

void loop() {
  delay(2000);
  float humidity1 = dht1.readHumidity();
  float temperature1 = dht1.readTemperature();
  float humidity2 = dht2.readHumidity();
  float temperature2 = dht2.readTemperature();
  Serial.print("Umiditate DHT1: ");
  Serial.print(humidity1);
  Serial.print(" Temperatura DHT1: ");
  Serial.println(temperature1);
  Serial.print("Umiditate DHT2: ");
  Serial.print(humidity2);
  Serial.print(" Temperatura DHT2: ");
  Serial.println(temperature2);
}
