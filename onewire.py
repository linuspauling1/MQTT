#! /usr/bin/python3

import time
import os
from stat import *
import paho.mqtt.client as mqtt
import re

#path = '/sys/bus/w1/devices/' #calea absoluta pentru testele din vm
path = '/sys/bus/w1/devices/' #calea absoluta
senzori = [] #trebuie ca senzorii sa fie deja conectati pentru ca aplicatia sa porneasca...
client_id = '1wire' #numele clientului care sade aici, pe rpi
port_insecure = 1883 #portul nesecurizat pentru mqtt
host = '101.232.174.243' #ip server
qos = 2 #folosim calitatea maxima astfel incat sa nu avem probleme cu deconectarea
clean_session = False #vom stoca informatiile netrimise
retain = True #vom stoca ultimul mesaj
topic1 = 'nodemcu/1wire' #canalul pe care trimitem date
topic2 = 'nodemcu2/1wire' #canalul pe care trimitem date
topic_will = 'temperaturi/1wire' #canalul pe care trimitem "the last will message"
path1 = '/sys/bus/w1/devices/28-0417a20db2ff/w1_slave'
path2 = '/sys/bus/w1/devices/28-0417a20db2ff/w1_slave'

def citire():
	global valoare1, valoare2
	if os.path.exists(path1):
		try:
			with open(path1,'r') as f1:
				continut = f1.readlines()[1]
				temperatura = continut.split()[-1]
				valoare1 = float(int(temperatura[2:])//100)/10
		except Exception as e1:
			print(e1)
	else:
		valoare1 = -99.9
		print('Nu putem citi senzorul de la gpio4!')
	if os.path.exists(path2):
		try:
			with open(path2,'r') as f2:
				continut = f2.readlines()[1]
				temperatura = continut.split()[-1]
				valoare2 = float(int(temperatura[2:])//100)/10
		except Exception as e2:
			valoare2 = -99.9
			print(e2)
	else:
		valoare2 = -99.9
		print('Nu putem citi senorul de la gpio17!')
#partea de mqtt:
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        client.connected_flag = True #s-a conectat clientul daca are codul returnat nul callback-ul on_connect
        print('Conexiune reusita')
    else:
        client.bad_connection_flag = True #setam fanionul ca sa putem iesi din script
        print('Conexiunea a esuat cu codul: ', rc)
def on_disconnect(client, userdata, rc):
    if rc == 0:
        print('Clientul s-a deconectat... Totul este bine.')
    else:
        print('Clientul s-a deconectat cu codul: ', rc,' ... Incercam reconectarea...')
        client.connected_flag = False
        if rc < 7:
            client.loop_stop()
            print('Clientul s-a deconectat cu codul ',rc,' ... Este o eroare grava ...')
            exit(-4)
def on_publish(client, userdata, result):
    print('Mesajul a fost trimis cu codul ', result)
def on_log(client, userdata, result):
	#print(buff)
	pass
client = mqtt.Client(client_id, clean_session)
client.bad_connection_flag = False #setam steagurile pentru client
client.connected_flag = False
client.on_connect = on_connect #adaugam callback-ul
client.on_disconnect = on_disconnect
client.on_publish = on_publish
client.on_log = on_log
client.will_set(topic_will,'M-am deconectat',qos,retain)
try:
    client.connect(host=host, port=port_insecure, keepalive=60, bind_address="") #omitem exceptiile
except:
    print('Conexiunea a esuat...probabil sunt cativa parametri eronati...')
    exit(-1) #iesim fortat din script
client.loop_start() #incepem bucla de procesare a evenimentelor
while not client.bad_connection_flag and not client.connected_flag: #cat timp nu suntem conectati
    print('...')
    time.sleep(.5)
if client.bad_connection_flag:
    client.loop_stop() #incheiem bucla de procesare a evenimentelor
    exit(-2) #iesim fortat
while not client.bad_connection_flag:
    if client.connected_flag:
        citire()
        client.publish(topic1, valoare1, qos, retain)
        print(valoare1)
        client.publish(topic2, valoare2, qos, retain)
        print(valoare2)
    else:
        print('Incercam reconectarea...')
    time.sleep(1) #achizitionam date la fiecare secunda (senzorul oricum are intertie termica mare)
client.loop_stop() #oprim bucla
client.disconnect() #ne deconectam