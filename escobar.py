import paho.mqtt.client as mqtt
import time
import mysql.connector as conexiune
from queue import Queue

q1 = Queue()
q2 = Queue()
cliend_id = 'rpi2' #un client asemanator cu cel anterior
clean_session = False #dorim ca mesajele sa fie pastrate pana la reconectare
host = '101.232.174.243'
port_insecure = 1883 #portul securizat fiind 8883
qos = 2 #calitatea maxima

db = conexiune.connect(
    host = host,
    user = 'root',
    passwd = 'prikoke',
    database = 'bazaDeDate'
)
cursorul_meu = db.cursor()

topic_wifi_senzor1 = 'temperaturi/wifi/senzor1'
topic_wifi_senzor2 = 'temperaturi/wifi/senzor2'
topic_wifi = 'temperaturi/wifi/#'

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        client.connected_flag = True
        print('M-am conectat.')
    else:
        client.bad_connection_flag = True
        print('Eroare la conexiune cu codul: ',rc)
    try:
        (result, mid) = client.subscribe(topic_wifi, qos)
        while result != 0:
            print('... ...')
            (result, mid) = client.subscribe(topic_wifi, qos)
        print('Am reusit abaonarea la canlul cu identificatorul de mesaj: ', mid)
    except:
        print('Nu am putut sa ne abonam la canalul cu datele primite de la senzori...')
        exit(-3)
def on_disconnect(client, userdata, rc):
    client.connected_flag = False
    print('Clientul s-a deconectat cu codul: ', rc)
    if rc < 7:
        client.loop_stop()
        print('Este o eroare grava...')
        exit(-4)
    else:
        client.bad_connection_flag = True #pentru a putea reveni in bucla
def on_subscribe(client, userdata, mid, granted_qos):
    print('Identificaoturl de mesaj emis : ',mid)
    pass
def on_message(client, userdata, message):
    payload = str(message.payload.decode("utf-8"))
    if message.topic == topic_wifi_senzor1:
        print('De la wifi1 avem: ',payload)
        q1.put(payload)
    elif message.topic == topic_wifi_senzor2:
        print('De la wifi2 avem: ',payload)
        q2.put(payload)
    if message.retain == 1:
        print("Mesajul acesta a fost emis cat timp clientul era deconectat...")

client = mqtt.Client(cliend_id,clean_session)
client.bad_connection_flag = False #flag pentru conexiune deficitara
client.connected_flag = False #flag pentru conexiune stabilita
client.suback_flag = False #flag pentru subscriere
client.on_connect = on_connect
client.on_disconnect = on_disconnect
client.on_subscribe = on_subscribe
client.on_message = on_message
try:
    client.connect(host=host, port=port_insecure, keepalive=60, bind_address='')
except:
    print('Parametri incorecti!')
    exit(-1)
client.loop_start()
while not client.connected_flag and not client.bad_connection_flag:
    print('...')
    time.sleep(.5)
if client.bad_connection_flag:
    client.loop_stop()
    exit(-2)
while client.connected_flag or client.bad_connection_flag:
    print('q1 are dimensiunea: ',q1.qsize(),' si q2: ',q2.qsize())
    while not q1.empty() and not q2.empty():
        (t1,t2) = (q1.get(),q2.get()) #puteam nota direct parametri, insa este mai elegant asa
        db.commit()
        try:
            params = [100] #valoarea buffer-ului mysql va fi 100
            try:
                cursorul_meu.callproc('adaugare',params)
            except:
                print('Nu merge adaugarea, deci sunt parametri gresiti...')
                time.slepp(1)
                continue
            try:
                cursorul_meu.execute('insert into temperaturi(nume_camera, temperatura_wifith1, temperatura_wifith2) values(\'albastra\',%s, %s)',(t1,t2))
            except:
                print('Insertie defectuaosa, deci sunt parametri gresiti...')
        except:
            print('Nu exista inca baza de date!!!')
            time.sleep(1)
            try:
                db = mysql.connector.connect(
                    host = '101.232.174.243',
                    user = 'root',
                    passwd = 'prikoke',
                    database = 'bazaDeDate'
                )
                cursorul_meu = db.cursor()
            except:
                print('Reconectare esuata...')
    time.sleep(1)
cursorul_meu.close()
client.loop_stop()
client.disconnect()