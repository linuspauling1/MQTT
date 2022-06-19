import paho.mqtt.client as mqtt #importam biblioteca pentru clientul mqtt
import time
import mysql.connector

client_id = 'rpi' #numele clientului care sade aici, pe rpi
port_insecure = 1883 #portul nesecurizat pentru mqtt
host = '101.232.172.13' #ip server
qos = 2 #folosim calitatea maxima astfel incat sa nu avem probleme cu deconectarea
clean_session = False #vom stoca informatiile netrimise
retain = True #vom stoca ultimul mesaj
my_sql_conexiune = False #flag pentru testarea conexiunii cu mariaDB
while not my_sql_conexiune:
    try:
        mydb = mysql.connector.connect( #ne conectam la baza de date
            host = host,
            user = 'root',
            passwd = 'prikoke',
            database = 'bazaDeDate'
        )
        my_cursor=mydb.cursor() #generam o instanta pentru un cursor
        my_sql_conexiune = True
    except:
        print('Conectarea la serverul MySQL esuata...Incercam sa ne reconectam...')
        time.sleep(1)
topic_perioada = 'nodemcu1/perioada'
topic_prag_inferior = 'nodemcu1/prag/inferior'
topic_prag_superior = 'nodemcu1/prag/superior'
topic_diferenta = 'nodemcu1/diferenta'

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
    if rc == 0:
        print('Clientul s-a deconectat... Totul este bine.')
    else:
        print('Clientul s-a deconectat cu codul ',rc,' incercam sa ne reonectam...')
        client.connected_flag = False
        if rc < 7:
            client.loop_stop()
            print('Clientul s-a deconectat cu codul ',rc,' ... Este o eroare grava ...')
            exit(-3)
        else:
            print('Clientul s-a deconectat cu codul: ', rc,' ... Incercam reconectarea...')
def on_publish(client, userdata, result):
    print('Mesajul a fost trimis cu codul ', result)
def on_log(client, userdata, level, buff):
    #print(buff)
    pass

client = mqtt.Client(client_id, clean_session)
client.bad_connection_flag = False #setam steagurile pentru client
client.connected_flag = False
client.on_connect = on_connect #adaugam callback-ul
client.on_disconnect = on_disconnect
client.on_publish = on_publish
client.on_log = on_log
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
        try:
            mydb.commit()
            my_cursor.execute('select perioada from camere where nume_camera = \'albastra\'')#achizitie perioada
            try:
                perioada = my_cursor.fetchall()[0][0]
                if(perioada is None):
                    print('Informatiile despre camere sunt absente!!!')
                else:
                    perioada = int(perioada)
                    if ante_perioada != perioada:
                        client.publish(topic_perioada, perioada, qos, retain)
                        ante_perioada = perioada
                        print('Noua perioada: ',perioada)
            except:
                print('Nu exista inca date din tabela camerelor!!!')
            my_cursor.execute('select prag_inferior from camere where nume_camera = \'albastra\'')#achizitie prag inferior
            try:
                prag_inferior = my_cursor.fetchall()[0][0]
                if(prag_inferior is None):
                    print('Informatiile despre camere sunt absente - perioada!!!')
                else:
                    prag_inferior = float(prag_inferior)
                    if ante_prag_inferior != prag_inferior:
                        client.publish(topic_prag_inferior, prag_inferior, qos, retain)
                        ante_prag_inferior = prag_inferior
                        print('Noul prag inferior: ',prag_inferior)
            except:
                print('Nu exista inca date din tabela camerelor - perioada!!!')
            my_cursor.execute('select prag_superior from camere where nume_camera = \'albastra\'')#achizitie prag superior
            try:
                prag_superior = my_cursor.fetchall()[0][0]
                if(prag_superior is None):
                    print('Informatiile despre camere sunt absente - prag superior!!!')
                else:
                    prag_superior = float(prag_superior)
                    if ante_prag_superior != prag_superior:
                        client.publish(topic_prag_superior, prag_superior, qos, retain)
                        ante_prag_superior = prag_superior
                        print('Noul prag superior: ',prag_superior)
            except:
                print('Nu exista inca date din tabela camerelor - prag superior!!!')
            my_cursor.execute('select diferenta from camere where nume_camera = \'albastra\'')#achizitie diferenta
            try:
                diferenta = my_cursor.fetchall()[0][0]
                if(diferenta is None):
                    print('Informatiile despre camere sunt absente - diferenta temperaturi terminstori !!!')
                else:
                    diferenta = float(diferenta)
                    if ante_diferenta != diferenta:
                        client.publish(topic_diferenta, diferenta, qos, retain)
                        ante_diferenta = diferenta
                        print('Noua diferenta: ',diferenta)
            except:
                print('Nu exista inca date din tabela camerelor - diferenta temperaturi termistori !!!')
            mydb.commit()
        except Exception as e:
            print('Nu este disponibila baza de date sau tabelele sunt alterate!!!')
            print('Mesajul de eroare este ', e)
            time.sleep(1)
            try:
                mydb = mysql.connector.connect(
                    host = host,
                    user = 'root',
                    passwd = 'prikoke',
                    database = 'bazaDeDate'
                )
                my_cursor = mydb.cursor()
                print('Reconectare reusita!!! Daca nu sunt in continuare accesibile tabelele, atunci acestea nu au fost create corect!!!')
            except:
                print('Reconectare esuata la serverul MySQL...')
    else:
        print('Mai incercam conectarea la serverul MQTT...')
    time.sleep(1) #perioada NU este aceeasi ca pentru achizitia temperaturii
client.loop_stop() #oprim bucla
my_cursor.close() #nu mai folosim cursorul
client.disconnect() #ne deconectam
