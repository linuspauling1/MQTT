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
ante_th1 = 0 #o valoare momentan irelevanta pentru temperatura precedenta
topic2 = 'nodemcu2/1wire' #canalul pe care trimitem date
ante_th2 = 0 #o valoare momentan irelevanta pentru temperatura precedenta
topic_will = 'temperaturi/1wire' #canalul pe care trimitem "the last will message"

def start():
	try:
		status_director = os.stat(path)
		if S_ISDIR(status_director.st_mode):
			for file in os.listdir(path):
				status_file = os.stat(path + '/' + file)
				if S_ISDIR(status_file.st_mode):
					cale = path + '/'+ file + '/w1_slave'
					try:
						status = os.stat(cale)
						if S_ISREG(status.st_mode):
							senzori.append(cale)
						else:
							print('Directorul pentru senzori nu contine fisierul necesar...')
					except:
						if not re.search('bus_master',cale):
							print('In directorul acesta nu am gasit informatiile necesare! E grav!')
				else:
					print('Directorul contine ceva neasteptat...')
		else:
			print('Fisierul nu este director, desi ar fi trebuit sa fie...')
	except Exception as exceptie:
		print('Nu exista fisierul ',path,'...')
		print(exceptie)
		exit(-1)
def citire():
	global valoare1, valoare2
	try:
		if len(senzori) == 0:
			print('Momentan senzorii lipsesc...')
			time.sleep(1) #asteptam 1 secunda
			valoare1 = ante_th1 #nu dorim ca valorile sa se schimbe
			valoare2 = ante_th2
		if len(senzori) > 0 :
			with open(senzori[0], 'r') as f:
			    continut = f.readlines()[1]
			    temperatura = continut.split()[-1]
			    valoare1 = float(int(temperatura[2:])//100)/10
			valoare2 = ante_th2 #nici aici nu vrem ca valorile sa se schimbe
		if len(senzori) > 1:
			with open(senzori[1], 'r') as f:
			    continut = f.readlines()[1]
			    temperatura = continut.split()[-1]
			    valoare2 = float(int(temperatura[2:])//100)/10
	except Exception as e:
		print(e)
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
start() #ar trebui ca aici senzorii sa fie deja conectati, altfel nu va porni procesul
while not client.bad_connection_flag:
    if client.connected_flag:
    	citire()
    	if ante_th1 != valoare1:
    		client.publish(topic1, valoare1, qos, retain)
    		ante_th1 = valoare1
    	if ante_th2 != valoare2:
    		client.publish(topic2, valoare2, qos, retain)
    		ante_th2 = valoare2
    else:
        print('Incercam reconectarea...')
    time.sleep(1) #achizitionam date la fiecare secunda (senzorul oricum are intertie termica mare)
client.loop_stop() #oprim bucla
client.disconnect() #ne deconectam
