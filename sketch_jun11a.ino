#include <OneWire.h>
#include <DallasTemperature.h>
#include <ESP8266WiFi.h>
#include <PubSubClient.h>
#include <cstring>
#include "DHT.h"

#define senzor_umiditate_temperatura DHT11

const int magistralaOneWire = 14;//echivalent cu D5     
OneWire oneWire(magistralaOneWire); 
DallasTemperature sensors(&oneWire);

char* network_name = "WMKT2";
char* network_pass = "1324354657687980";
char* clientID = "NodeMCU1";
char* topic_prag_inferior = "nodemcu1/prag/inferior";//numele topicurilor pe care transmitem catre NodeMCU,
char* topic_prag_superior = "nodemcu1/prag/superior";//temperaturile prag,
char* topic_diferenta = "nodemcu1/diferenta";//diferenta maxima admisa intre valorile temperaturilor si
char* topic_perioada = "nodemcu1/perioada";//perioada de achizitie a temperaturilor
char* topic_nodemcu = "nodemcu1/#";//topic care cuprinde toate subtopicurile nodemcu
char* topic_wifi_senzor1 = "temperaturi1/senzori/senzor1";//numele topicurilor de pe care primim temperaturile
char* topic_wifi_senzor2 = "temperaturi1/senzori/senzor2";
char* topic_wifi = "temperaturi1/senzori/#";//topic care cuprinde ambele temperaturi
char* topic_1wire = "temperaturi1/1wire";
char temperatura_1wire_string[6];
char temperatura_wifi1_string[6];
char temperatura_wifi2_string[6];//temperaturile achizitionate
const int br = 115200;//baud rate pentru seriala
const int port = 1883;//portul nesecurizat traditional mqtt
const int analogInPin = A0;//intrarea analogica pentru termistor
const int termistor1 = D1;//primul termistor
const int termistor2 = D2;//al doilea termistor
const int alarma_exces = D3;//actuator care alerteaza temperatura excesiva, se aprinde un led rosu
const int alarma_deficit = D4;//actuator care anunta temperatura prea mica, se aprinde un led albastru
const int temperatura1 = D6;//senzor temperatura si umiditate dht
const int temperatura2 = D7;//alt senzor dht
const int pwm = D8;//port pwm
IPAddress ip_server(101,232,174,243);//ip-ul din LAN al raspberry-ului
DHT dht1 = DHT(temperatura1,senzor_umiditate_temperatura);
DHT dht2 = DHT(temperatura2,senzor_umiditate_temperatura);
int analogValue;//o folosim la achizitia de temperatura
unsigned long cur, prev, prev_check, timp;
int perioada = 2000;//initial achizitionam temperaturile la fiecare doua secunde
float prag_inferior;
float prag_superior;
float temperatura_1wire;
float diferenta;
float wifi1, wifi2;
float temperatura_medie;//pilotul va fi media celor doua mai apropiate temperaturi

WiFiClient client_wifi;
PubSubClient client_mqtt(client_wifi);

inline void mesaj_eroare() {
    Serial.print("Stare curenta: ");
    Serial.print(client_mqtt.state());
    Serial.print(".\n");
}

bool isNo(char* payload)//identificare numere
{
	int i, count = 0, count_neg = 0;
	bool digit = true;
	for(i = 0;payload[i] != 0;++i) {
		if(payload[i] == '.')
			++count;
    if(payload[i] == '-')
      ++count_neg;
		if((payload[i] != '.' && payload[i] != '-' && payload[i] > '9' && payload[i] < '0') || count > 1 || count_neg > 1) {
			digit = false;
			break;
		}
	}
	return digit;
}

void callback(const char topic[], byte* payload, unsigned int length) {
  char* buffer = (char*)malloc((length+1)*sizeof(char));
	memcpy(buffer, payload, length);
	buffer[length]=0;
  if(!isNo(buffer)){
    Serial.print("Nu este numar: ");
    Serial.println(buffer);
    return;
  }
  if(!strcmp(topic,topic_prag_inferior)) {
    prag_inferior = atof(buffer);
  } else if(!strcmp(topic, topic_prag_superior)) {
    prag_superior = atof(buffer);
  } else if(!strcmp(topic,topic_diferenta)) {
    diferenta = atof(buffer);
  } else if(!strcmp(topic,topic_perioada)) {
    perioada = atoi(buffer) ? atoi(buffer) : perioada;//nu poate fi perioada nula, ar insemna o frecventa infinita
  } else {
    Serial.print("Topic-ul este irelevant pentru cerinta.Nume topic: ");
    Serial.print(topic);
    Serial.print(" avand textul: ");
    Serial.println(buffer);
  }
  free(buffer);
}

void setup() {
  sensors.begin();//incepem achizitionarea datelor de la senzorul 1-wire
  pinMode(termistor1,OUTPUT_OPEN_DRAIN);
  pinMode(termistor2,OUTPUT_OPEN_DRAIN);
  pinMode(alarma_exces,OUTPUT_OPEN_DRAIN);
  pinMode(alarma_deficit,OUTPUT_OPEN_DRAIN);
  digitalWrite(termistor1,LOW);
  digitalWrite(termistor2,HIGH);
  digitalWrite(alarma_exces,HIGH);
  digitalWrite(alarma_deficit,HIGH);
  dht1.begin();//va avea efect pentru placa a doua
  dht2.begin();//va avea efect pentru placa a doua
  Serial.begin(br);
  Serial.println();//curatam ecranul
  WiFi.begin(network_name,network_pass);
  Serial.print("\nSe conecteaza...");
  while(!WiFi.isConnected()) { //verificam conexiunea in reteaua locala
    Serial.println("...");
    delay(500);//intarziere mai mare
  }
  Serial.print("\nS-a conectat primul modul in LAN!\n");
  Serial.print("Modulul are ip-ul: ");
  Serial.println(WiFi.localIP());
  client_mqtt.setServer(ip_server,port);
  client_mqtt.setCallback(callback);//callback pentru subscribe
  while(!client_mqtt.connect(clientID,NULL,NULL,"temperaturi2/wifi/senzor1",2,true,"M-am deconectat...",true)) { //verificam conexiunea drept client MQTT
    Serial.print("Nu s-a conectat clientul MQTT...\n");//si setam "las will message"-ul
    mesaj_eroare();//dorim ca sesiunile sa fie "curate"
    delay(100);//intarziere mai mica
  }
  while(!client_mqtt.subscribe(topic_nodemcu,1)) { //ne abonam la canalele care ne ofera informatii
    Serial.print("Clientul");
    Serial.print(clientID);
    Serial.print(" inca nu s-a abonat.\n");
    mesaj_eroare();
    delay(200);//intarziere putin mai mica
  }
}

void achizitieOneWire(){//ar fi bine ca achizitia sa se faca cu o perioada de minim 750ms
  static int timp = 0;
  int now = millis();
  if(now - timp > perioada){
    timp = now;
    sensors.requestTemperatures(); 
    float temperatura_1fir = sensors.getTempCByIndex(0);
    if(!isnan(temperatura_1fir))
      temperatura_1wire = temperatura_1fir;
    /*Serial.print("Temperatura masurata de 1-wire: ");
    Serial.println(temperatura_1wire);*/
  }
}

void senzori_dht() { //ar fi bine ca achizitia de date sa se faca la cel putin 2 sec
  static int timp = 0;
  int now = millis();
  if(now - timp > perioada){
    timp = now;
    float humidity1 = dht1.readHumidity();
    float temperature1 = dht1.readTemperature();
    float humidity2 = dht2.readHumidity();
    float temperature2 = dht2.readTemperature();
    /*Serial.print("Umiditate DHT1: ");
    Serial.print(humidity1);
    Serial.print(" Temperatura DHT1: ");
    Serial.println(temperature1);
    Serial.print("Umiditate DHT2: ");
    Serial.print(humidity2);
    Serial.print(" Temperatura DHT2: ");
    Serial.println(temperature2);*/
    if(!isnan(temperature1))    
      wifi1 = temperature1;
    else
      wifi1 = -99.9;
    if(!isnan(temperature2))
      wifi2 = temperature2;
    else
      wifi2 = -99.9;
  }
}

void multiplexare() {//mereu vom primi valori care sunt numere, nu e cazul de testare pentru NaN
  static bool flag = false;
  static int timp = 0;
  int now = millis();
  if(now - timp > perioada/2 && !flag){
    analogValue = analogRead(A0);
    wifi1 = analogValue/10.0;
    digitalWrite(termistor1,HIGH);
    digitalWrite(termistor2,LOW);
    flag = true;
  }
  if(now - timp > perioada){
    analogValue = analogRead(A0);
    wifi2 = analogValue/10.0;
    digitalWrite(termistor2,HIGH);
    digitalWrite(termistor1,LOW);
    flag = false;
    timp = millis();
  }
}

void achizitie() {
  if(abs(wifi1) >= 100.0){
      Serial.print("Valoarea este inadmisibil de mare in modul.\n");
      strcpy(temperatura_wifi1_string,"-99.9");
  } else {
      dtostrf(wifi1,2,1,(char*)temperatura_wifi1_string);
  }
  if(abs(wifi2) >= 100.0){
      Serial.print("Valoarea este inadmisibil de mare in modul.\n");
      strcpy(temperatura_wifi2_string,"-99.9");
  } else {
      dtostrf(wifi2,2,1,(char*)temperatura_wifi2_string);
  }
  if(abs(temperatura_1wire) >= 100.0){
      Serial.print("Valoarea este inadmisibil de mare in modul.\n");
      strcpy(temperatura_1wire_string,"-99.9");
  } else {
      dtostrf(temperatura_1wire,2,1,(char*)temperatura_1wire_string);
  }
}

void actuatori() {
  //calcul medie
  if(abs(wifi1 - wifi2) > abs(wifi1 - temperatura_1wire))
    if(abs(wifi1 - temperatura_1wire) > abs(wifi2 - temperatura_1wire))
      temperatura_medie = (wifi2 + temperatura_1wire)/2.0;
    else
      temperatura_medie = (wifi1 + temperatura_1wire)/2.0;
  else
    if(abs(wifi1 - wifi2) > abs(wifi2 - temperatura_1wire))
      temperatura_medie = (wifi2 + temperatura_1wire)/2.0;
    else
      temperatura_medie = (wifi1 + wifi2)/2.0;
  //stabilire temperatura extrema
  static float dif_max = 0.f;
  if(abs(temperatura_medie - wifi1) > abs(temperatura_medie - wifi2))
    if(abs(temperatura_medie - wifi1) > abs(temperatura_medie - temperatura_1wire))
      dif_max = wifi1;
    else
      dif_max = temperatura_1wire;
  else
    if(abs(temperatura_medie - wifi2) > abs(temperatura_medie - temperatura_1wire))
      dif_max = wifi2;
    else
      dif_max = temperatura_1wire;
  bool temperaturaPreaMare = false;
  bool temperaturaPreaMica = false;
  bool temperaturaPotrivita = false;
  bool mediePreaMare = false;
  bool mediePreaMica = false;
  bool mediePotrivita = false;
  //stabilim in ce sens este deviata temperatura citita incorect
  if(dif_max - temperatura_medie > diferenta){
    temperaturaPreaMica = false;
    temperaturaPreaMare = true;
    temperaturaPotrivita = false;
  } else if(temperatura_medie - dif_max > diferenta){
    temperaturaPreaMica = true;
    temperaturaPreaMare = false;
    temperaturaPotrivita = false;
  } else {
    temperaturaPreaMica = false;
    temperaturaPreaMica = false;
    temperaturaPotrivita = true;
  }
  //stabilim deviatia mediei
  if(temperatura_medie > prag_superior){
    mediePreaMare = true;
    mediePreaMica = false;
    mediePotrivita = false;
  } else if(temperatura_medie < prag_inferior){
    mediePreaMare = false;
    mediePreaMica = true;
    mediePotrivita = false;
  } else {
    mediePreaMare = false;
    mediePreaMica = false;
    mediePotrivita = true;
  }
  //vom trata cazurile corespunzator
  static bool steag = false;
  static unsigned long timp_anterior = 0;
  if(mediePreaMare && temperaturaPreaMare){
    digitalWrite(alarma_deficit,HIGH);
    if(millis() - timp_anterior > 500) {//palpaie cu o perioada de o secunda
      steag = !steag;
      timp_anterior = millis();
      digitalWrite(alarma_exces,steag);//palpaie rosu
    }
  } else if(mediePreaMica && temperaturaPreaMare){
      digitalWrite(alarma_deficit,LOW);//e aprins albastru
      if(millis() - timp_anterior > 500) {//palpaie cu o perioada de o secunda
        steag = !steag;
        timp_anterior = millis();
        digitalWrite(alarma_exces,steag);//palpaie rosu
      }
  } else if(mediePotrivita && temperaturaPreaMare){
      digitalWrite(alarma_deficit,LOW);//a aprins albastru
      digitalWrite(alarma_exces,LOW);//si e aprins si rosu
  } else if(mediePreaMare && temperaturaPreaMica){
      digitalWrite(alarma_exces,LOW);//e aprins rosu
      if(millis() - timp_anterior > 500) {//palpaie cu o perioada de o secunda
        steag = !steag;
        timp_anterior = millis();
        digitalWrite(alarma_deficit,steag);//palpaie albastru
      }
  } else if(mediePreaMica && temperaturaPreaMica){
      digitalWrite(alarma_exces,HIGH);
      if(millis() - timp_anterior > 500){//palpaie cu o perioada de o secunda
        steag = !steag;
        timp_anterior = millis();
        digitalWrite(alarma_deficit,steag);//palpaie albastru
      }
  } else if(mediePotrivita && temperaturaPreaMica){
      if(millis() - timp_anterior > 500){//palpaie cu o perioada de o secunda
        steag = !steag;
        timp_anterior = millis();
        digitalWrite(alarma_exces,steag);//palpaie rosu
        digitalWrite(alarma_deficit,!steag);//si albastru
      }
  } else if(mediePreaMare && temperaturaPotrivita){
      digitalWrite(alarma_exces,LOW);//e aprins rosu,
      digitalWrite(alarma_deficit,HIGH);//dar stins albastru
  } else if(mediePreaMica && temperaturaPotrivita){
      digitalWrite(alarma_exces,HIGH);//e stins rosu,
      digitalWrite(alarma_deficit,LOW);//dar aprins albastru
  } else if(mediePotrivita && temperaturaPotrivita){
      digitalWrite(alarma_exces,HIGH);//nu palpaie si nu e aprins nimic
      digitalWrite(alarma_deficit,HIGH);
  }
  //actuator cu histerezis pentru camera frigorifica (reactioneaza la temperaturi inadmisibil de mari)
  static bool racitor = false;
  float histerezis_cald_inferior = (prag_superior - prag_inferior)/2.f;
  float histerezis_cald_superior = (prag_superior - prag_inferior)/2.f;
  if(!histerezis_cald_inferior || !histerezis_cald_superior)
    histerezis_cald_inferior = histerezis_cald_superior = 100.f;//altfel se declanseaza la pornire
  int dc;
  if(temperatura_medie > prag_superior + histerezis_cald_superior)
    racitor = true;
  if((temperatura_medie < prag_superior - histerezis_cald_inferior) && racitor)
    racitor = false;
  if(racitor){
    dc = (int)((prag_superior + histerezis_cald_superior - temperatura_1wire)/(histerezis_cald_inferior + histerezis_cald_superior)*1023.0);
    if(temperatura_medie > prag_superior + histerezis_cald_superior)
      dc = 0;
    dc = 1023 - dc;
    Serial.print("Factor de umplere (de la 0 la 1023): ");
    Serial.println(dc);
    analogWrite(pwm,dc);
  } else{
    analogWrite(pwm,0);
  }
}

void loop() {
  multiplexare();//o apelam pentru prima placa
  //senzori_dht();//o apelam pentru a doua placa
  achizitieOneWire();//o apelam pentru ambele placi
  bool bucla = true;
  cur = millis();
  //verificam conexiunea
  bool flag_loop = client_mqtt.loop();//verificam daca mai este conectat clientul
  if(!flag_loop)
    bucla = false;
  if(!flag_loop && (cur - prev_check >= 500)) {//ne reconectam din 500ms in 500ms
    prev_check = millis();
    if(!client_mqtt.connect(clientID)) { //verificam conexiunea drept client MQTT
      Serial.print("Nu s-a reconectat clientul MQTT...\n");
      mesaj_eroare();
    }
    if(!client_mqtt.subscribe("nodemcu2/prag/#",1)) { //NU este necesara aceasta portiune de cod, ar fi fost doar in cazul in care 
      Serial.print("Clientul"); //am fi avut o conexiune cu clean session flag-ul setat !!!
      Serial.print(clientID); // de asemenea, pot fi retinute pana la 100 de mesaje (default) de catre borker
      Serial.print(" inca nu s-a reabonat.\n");
      mesaj_eroare();
    }
  }
  if(bucla) {
    //procesam datele
    if(cur - prev >= perioada) {
      prev = millis();
      /*Serial.print("prag inferior: ");
      Serial.println(prag_inferior);
      Serial.print("prag superior: ");
      Serial.println(prag_superior);
      Serial.print("diferenta: ");
      Serial.println(diferenta);
      Serial.print("perioada: ");
      Serial.println(perioada);
      Serial.print("Media este: ");
      Serial.println(temperatura_medie);*/
      //publish:
      achizitie();
      actuatori();
      Serial.print("Primul senzor a masurat: ");
      Serial.println(temperatura_wifi1_string);
      Serial.print("Al doilea senzor a masurat: ");
      Serial.println(temperatura_wifi2_string);
      Serial.print("Senzorul 1-wire a masurat: ");
      Serial.println(temperatura_1wire_string);
      if(!client_mqtt.publish(topic_wifi_senzor1,(const unsigned char*)temperatura_wifi1_string,strlen(temperatura_wifi1_string),true)){ //fiind siruri de caractere nu e imperioasa specificarea dimensiunii
        Serial.print("Clientul"); //ar trebui ca mesajele sa ajunga la destinatie, totusi, nu este sigur
        Serial.print(clientID); //in dimensiunea specificata pentru transmiterea textului nu trebuie inclus si terminatorul
        Serial.print(" nu a publicat inca valoarea citita de senzorul 1.\n");
        mesaj_eroare();
      }
      if(!client_mqtt.publish(topic_wifi_senzor2,(const unsigned char*)temperatura_wifi2_string,strlen(temperatura_wifi2_string),true)){ // mesajele vor fi retinute
        Serial.print("Cleiantul");
        Serial.print(clientID);
        Serial.print(" nu a publicat inca valoarea citita de senzorul 2.\n");
        mesaj_eroare();
      }
      if(!client_mqtt.publish(topic_1wire,(const unsigned char*)temperatura_1wire_string,strlen(temperatura_1wire_string),true)){ // mesajele vor fi retinute
        Serial.print("Cleiantul");
        Serial.print(clientID);
        Serial.print(" nu a publicat inca valoarea citita de senzorul 1-wire.\n");
        mesaj_eroare();
      }
    }
  }
}