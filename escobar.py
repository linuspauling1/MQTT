import paho.mqtt.client as mqtt
import time
import mysql.connector as conexiune
from queue import Queue

def esteNumar(numar):
    try:
        x = float(numar)
        print(x)
        return True
    except:
        print('Nu este un numar!')
        return False
q1 = Queue() #contine datele primite de la wifi1
q2 = Queue() #contine datele primite de la wifi2
q3 = Queue() #contine datele primite de la 1-wire
cliend_id = 'rpi2' #un client asemanator cu cel anterior
clean_session = False #dorim ca mesajele sa fie pastrate pana la reconectare
host = '101.232.174.243'
port_insecure = 1883 #portul securizat fiind 8883
qos = 2 #calitatea maxima
buffer_size = 100 #dimensiunea circular buffer-ului MySQL
nume_camera = 'albastra' #numele camerei este 'albastra'
conexiune_my_sql = False#stabilim o conexiune cu baza de date mysql
while not conexiune_my_sql:
    try:
        db = conexiune.connect(
            host = '101.232.174.243',
            user = 'root',
            passwd = 'prikoke',
            database = 'bazaDeDate'
        )
        cursorul_meu = db.cursor()
        conexiune_my_sql = True
        print('Conexiunea cu baza de date reusita!')
    except:
        print('Conectarea cu bazele de date esuata...Incercam reconectarea')
        time.sleep(1)
#numele canalelor:
topic_1wire = 'temperaturi/1wire'
topic_wifi_senzor1 = 'temperaturi/wifi/senzor1'
topic_wifi_senzor2 = 'temperaturi/wifi/senzor2'
topic_wifi = 'temperaturi/wifi/#'
#callbacks:
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        client.connected_flag = True
        print('M-am conectat.') #daca return code-ul este nul, atunci conexiunea este viabila
        try: #incercam sa ne abonam la canalele pentru senzorii wifi
            (result, mid) = client.subscribe(topic_wifi, qos)
            while result != 0: #daca rezultatul este nul atunci conexiunea este slaba si trebuie refacuta
                print('... ...')
                (result, mid) = client.subscribe(topic_wifi, qos)
            print('Am reusit abaonarea la canlul cu identificatorul de mesaj: ', mid)
        except: #daca primim o excpetie trebuie sa iesim din program intrucat sunt parametri incorecti
            print('Nu am putut sa ne abonam la canalul cu datele primite de la senzori...')
            exit(-3)
        try: #incercam sa ne abonam la canalul pentru senzorul 1-wire
            (result_1wire, mid_1wire) = client.subscribe(topic_1wire, qos)
            while result_1wire != 0:
                print('... ... ...')
                (result_1wire, mid_1wire) = client.subscribe(topic_1wire, qos)
            print('Am reusit abaonarea la canlul pentru senzorul 1-wire cu identificatorul de mesaj: ', mid)
        except:
            print('Nu am putut sa ne abonam la canalul cu datele primite de la senzorul 1wire...')
            exit(-3)
    else:
        client.bad_connection_flag = True
        print('Eroare la conexiune cu codul: ',rc) #altfel nu
def on_disconnect(client, userdata, rc):
    if rc == 0:
        print('Clientul s-a deconectat...Totul este bine.')
    else:
        print('Clientul s-a deconectat cu codul: ', rc,' ... Incercam reconectarea...')
        client.connected_flag = False
        if rc < 7:
            client.loop_stop()
            print('Clientul s-a deconectat cu codul: ',rc,' ... Este o eroare grava ...')
            exit(-4)
def on_subscribe(client, userdata, mid, granted_qos):
    print('Identificaoturl de mesaj emis : ',mid) #trebuie sa corespunda mid-urile
    pass
def on_message(client, userdata, message):
    payload = str(message.payload.decode("utf-8"))
    if message.topic == topic_wifi_senzor1:
        if esteNumar(payload):
            q1.put(payload)
        else:
            print('De la wifi1 avem: ',payload)
    elif message.topic == topic_wifi_senzor2:
        if esteNumar(payload):
            q2.put(payload)
        else:
            print('De la wifi2 avem: ',payload)
    elif message.topic == topic_1wire:
        if esteNumar(payload):
            q3.put(payload)
        else:
            print('De la 1-wire avem: ', payload)
    if message.retain == 1:
        print("Mesajul acesta a fost emis cat timp clientul era deconectat...")
def on_log(client, userdata, level, buff):
    #print(buff)
    pass

client = mqtt.Client(cliend_id,clean_session)
client.bad_connection_flag = False #flag pentru conexiune deficitara
client.connected_flag = False #flag pentru conexiune stabilita
client.on_connect = on_connect
client.on_disconnect = on_disconnect
client.on_subscribe = on_subscribe
client.on_message = on_message
client.on_log = on_log
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
while not client.bad_connection_flag:
    if client.connected_flag:
        print('q1 are dimensiunea: ',q1.qsize(),' si q2: ',q2.qsize())
        while not q1.empty() and not q2.empty() and not q3.empty():
            (t1,t2,t3) = (q1.get(),q2.get(),q3.get()) # indiferent de succesul operatiunilor, vom muta in permanenta elementele din cozi - sunt de timp real
            try:
                params = [buffer_size, nume_camera]
                cursorul_meu.callproc('adaugare',params) #presupunem ca inseram parametri corecti
                try:
                    cursorul_meu.execute('insert into temperaturi(nume_camera, temperatura_wifith1, temperatura_wifith2, temperatura_1wire) \
                    values(\'albastra\',%s, %s, %s)',(t1,t2,t3))
                except:
                    print('Insertie defectuaosa, deci sunt parametri gresiti...')
                    time.sleep(1)
                    break 
                db.commit()
            except Exception as e:
                print('Nu exista inca baza de date!!!')
                print('Mesajul de eorare: ', e)
                time.sleep(1)
                try:
                    db = conexiune.connect(
                        host = '101.232.174.243',
                        user = 'root',
                        passwd = 'prikoke',
                        database = 'bazaDeDate'
                    )
                    cursorul_meu = db.cursor()
                    print('Reconectare reusita!!! Daca in continuare nu sunt disponibile tabelele inseamna ca nu sunt create corect!!!')
                except:
                    print('Reconectarea la baza de date esuata...')
                    break
    else:
        print('Mai incercam reconectarea la serverul MQTT...')
    time.sleep(1) #perioada este diferita de cea pentru achizitia unei temepraturi
cursorul_meu.close()
client.loop_stop()
client.disconnect()