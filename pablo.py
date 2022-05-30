import paho.mqtt.client as mqtt #importam biblioteca pentru clientul mqtt
import time
import mysql.connector

client_id = 'rpi' #numele clientului care sade aici, pe rpi
port_insecure = 1883 #portul nesecurizat pentru mqtt
host = '101.232.174.243' #ip server
qos = 2 #folosim calitatea maxima astfel incat sa nu avem probleme cu deconectarea
clean_session = False #vom stoca informatiile netrimise
retain = True #vom stoca ultimul mesaj

mydb = mysql.connector.connect( #ne conectam la baza de date
    host = host,
    user = 'root',
    passwd = 'prikoke',
    database = 'bazaDeDate'
)
my_cursor=mydb.cursor() #generam o instanta pentru un cursor

topic_perioada = 'nodemcu/perioada'
topic_temperatura_medie = 'nodemcu/medie'
topic_prag_inferior = 'nodemcu/prag/inferior'
topic_prag_superior = 'nodemcu/prag/superior'
topic_diferenta = 'nodemcu/diferenta'

perioada=1.0 #valorile curente
temperatura_medie=11.1 #sunt irelevante intrucat vor fi citite din baza de date
prag_inferior=11 #insa trebuie sa difere de perioadele anterioare intiale pentru
prag_superior=11 #declansarea transmiterii informatiilor
diferenta=1
ante_perioada=0 #valorile anterioare
ante_temperatura_medie=0
ante_prag_inferior=0
ante_prag_superior=0
ante_diferenta=0

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        client.connected_flag = True #s-a conectat clientul daca are codul returnat nul callback-ul on_connect
        print('Conexiune reusita')
    else:
        client.bad_connection_flag = True #setam fanionul ca sa putem iesi din script
        print('Conexiunea a esuat cu codul: ', rc)
def on_disconnect(client, userdata, rc):
    print('Clientul s-a deconectat cu codul: ', rc)
    if rc < 7:
        client.connected_flag = False
        client.loop_stop()
        print('Este o eroare grava...')
        exit(-4)
def on_publish(client, userdata, result):
    print('Mesajul a fost trimis cu codul ', result)

client = mqtt.Client(client_id, clean_session)
client.bad_connection_flag = False #setam steagurile pentru client
client.connected_flag = False
client.on_connect = on_connect #adaugam callback-ul
client.on_disconnect = on_disconnect
client.on_publish = on_publish
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
client.loop_stop() #oprim firul buclei intrucat o vom apela periodic
while client.connected_flag or client.bad_connection_flag:
    try:
        my_cursor.execute('select perioada from camere where nume_camera = \'albastra\'')#achizitie perioada
        try:
            perioada = my_cursor.fetchall()[0][0]
        except:
            print('Nu exista inca date din tabela camerelor!!!')
        if(perioada is None):
            print('Informatiile despre camere sunt absente!!!')
        else:
            perioada = int(perioada)
        my_cursor.execute('select prag_inferior from camere where nume_camera = \'albastra\'')#achizitie prag inferior
        try:
            prag_inferior = my_cursor.fetchall()[0][0]
        except:
            print('Nu exista inca date din tabela camerelor - perioada!!!')
        if(prag_inferior is None):
            print('Informatiile despre camere sunt absente - perioada!!!')
        else:
            prag_inferior = float(prag_inferior)
        my_cursor.execute('select prag_superior from camere where nume_camera = \'albastra\'')#achizitie prag superior
        try:
            prag_superior = my_cursor.fetchall()[0][0]
        except:
            print('Nu exista inca date din tabela camerelor - prag superior!!!')
        if(prag_superior is None):
            print('Informatiile despre camere sunt absente - prag superior!!!')
        else:
            prag_superior = float(prag_superior)
        my_cursor.execute('select diferenta from camere where nume_camera = \'albastra\'')#achizitie diferenta
        try:
            diferenta = my_cursor.fetchall()[0][0]
        except:
            print('Nu exista inca date din tabela camerelor - diferenta temperaturi termistori !!!')
        if(diferenta is None):
            print('Informatiile despre camere sunt absente - diferenta temperaturi terminstori !!!')
        else:
            diferenta = float(diferenta)
        my_cursor.execute('select temperatura_medie from temperaturi where nume_camera = \'albastra\' and indice = 1') #achizitie temperatura medie
        try:
            temperatura_medie = my_cursor.fetchall()[0][0]
        except:
            print('Nu exista inca date - temperatura medie !!!')
        if(temperatura_medie is None):
            print('Informatia este absenta - temperatura medie !!!')
        else:
            temperatura_medie = float(temperatura_medie)
        mydb.commit()
    except:
        print('Nu exista inca baza de date!!!')
        time.sleep(1)
        try:
            mydb = mysql.connector.connect(
                host = '101.232.174.243',
                user = 'root',
                passwd = 'prikoke',
                database = 'bazaDeDate'
            )
            my_cursor = mydb.cursor()
        except:
            print('Reconectare esuata...')
    if ante_perioada != perioada:
        client.publish(topic_perioada, perioada, qos, retain)
        ante_perioada = perioada
        print('Noua perioada: ',perioada)
    if ante_prag_inferior != prag_inferior:
        client.publish(topic_prag_inferior, prag_inferior, qos, retain)
        ante_prag_inferior = prag_inferior
        print('Noul prag inferior: ',prag_inferior)
    if ante_prag_superior != prag_superior:
        client.publish(topic_prag_superior, prag_superior, qos, retain)
        ante_prag_superior = prag_superior
        print('Noul prag superior: ',prag_superior)
    if ante_diferenta != diferenta:
        client.publish(topic_diferenta, diferenta, qos, retain)
        ante_diferenta = diferenta
        print('Noua diferenta: ',diferenta)
    if ante_temperatura_medie != temperatura_medie:
        client.publish(topic_temperatura_medie, temperatura_medie, qos, retain)
        ante_temperatura_medie = temperatura_medie
        print('Noua temperatura medie: ',temperatura_medie)
    client.loop() #apelam bucla pentru fiecare ciclare
    time.sleep(perioada/1000) #perioada este aceeasi ca pentru achizitia temperaturii
my_cursor.close() #nu mai folosim cursorul
client.disconnect() #ne deconectam