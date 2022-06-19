import time
import serial
import mysql.connector

def trimite_mesajul(textMesaj,nr_telefon):
	global seriala
	ctrlZ = chr(26) #caracter pentru terminarea mesajului
	nr_ro = nr_telefon #numarul pentru romania
	trimis = False
	while not trimis:
		try:
			seriala.write('at+cmgf=1\n') #pentru a putea transmite mesaje
			trimiteMesaj = 'at+cmgs="' + nr_ro + '"\n' + textMesaj + ctrlZ
			seriala.write(trimiteMesaj.encode()) #vom trimite un string UTF-8
			seriala.flushInput() #trebuie curatat ecranul
			seriala.readline() #trebuie citita comanda
			seriala.flushInput() #si ulterior curatata si aceasta
			text = seriala.readline() #citim instructiunea de succes sau de eroare
			print(unicode(text))
			if 'ERROR\r\n' in text:
				seriala.write('at+cpin="0000"\n')
			else:
				trimis = True
				break #nu vom mai astepta 5 secunde
		except Exception as e:
			print('Probabil ca ceva nu mai merge bine cu seriala...Reconectati dispozitivul si dupa reporniti aplicatia...')
			print(e)
		finally:
			time.sleep(5) #asteptam 5 secunde pentru reconectare
def conectare_seriala_GSM():
    global seriala
    try: 
		seriala = serial.Serial(            
        	port='/dev/serial0', #alias pentru ttyS0, miniUART, la porturile GPIO14-15
        	baudrate = 9600, #poate fi schimbata
        	parity=serial.PARITY_NONE, #fara bit de paritate
        	stopbits=serial.STOPBITS_ONE, #un singur bit de stop, nu doi
        	bytesize=serial.EIGHTBITS, #un octet de date, nu 5 biti, nu 9
        	timeout=5 #asteptam maxim 5 secunde pentru raspuns
    	)
    except Exception as e:
		print('Seriala UART indisponibila!!!!')
		print(e)
		exit(-1)
    try:
        seriala.write('at+cpin?\n')
        text = seriala.readlines()
        for item in text:
		    if 'SIM' in item:
			    seriala.write('at+cpin="0000"\n') #introducem PIN-ul, chiar daca produce o eroare cand este deja introdus
			    print('Nu era introdus SIM-ul')
			    break
    except Exception as e:
        print('Probabil ca ceva nu mai merge bine cu seriala...Reconectati dispopzitivul si dupa reporniti aplicatia...')
        print(e)
        exit(-1)
#partea "activa" a codului:
conectare_seriala_GSM()
#citirea bazelor de date:
my_sql_conexiune = False
host = '101.232.174.243'
while not my_sql_conexiune:
    try:
        baza_de_date = mysql.connector.connect( #ne conectam la baza de date
            host = host,
            user = 'root',
            passwd = 'prikoke',
            database = 'bazaDeDate'
        )
        cursorul_meu = baza_de_date.cursor() #generam o instanta pentru un cursor
        my_sql_conexiune = True
    except:
        print('Conectarea la serverul MySQL esuata...Incercam sa ne reconectam...')
        time.sleep(1)
ora_a = '0'
ora_p = '0'
ora_anterioara_a = '0' #ora este fictiva
ora_anterioara_p = '0' #este necesar ca mesageria sa fie activata
while True:
	try:
		#pentru camera albastra:
		try:
			cursorul_meu.execute('select prag_inferior, prag_superior, diferenta, numar_telefon from camere where nume_camera = \'albastra\'')
			prag_inferior_a, prag_superior_a, diferenta_a, numar_telefon_a = cursorul_meu.fetchall()[0]
			cursorul_meu.execute('select temperatura_medie, diferenta, ora from temperaturi where nume_camera = \'albastra\' limit 1')
			temperatura_medie_a, diferenta_maxima_a, ora_a = cursorul_meu.fetchall()[0]
		except:
			print('Nu avem populata baza de date a camerei albastre.')
		#pentru camera portocalie:
		try:
			cursorul_meu.execute('select prag_inferior, prag_superior, diferenta, numar_telefon from camere where nume_camera = \'portocalie\'')
			prag_inferior_p, prag_superior_p, diferenta_p, numar_telefon_p = cursorul_meu.fetchall()[0]
			cursorul_meu.execute('select temperatura_medie, diferenta, ora from temperaturi where nume_camera = \'portocalie\' limit 1')
			temperatura_medie_p, diferenta_maxima_p, ora_p = cursorul_meu.fetchall()[0]
		except:
			print('Nu avem populata baza de date a camerei portocalii.')
		#pentru administrator:
		try:
				cursorul_meu.execute('select numar_telefon from administrator')
				numar_telefon_admin, = cursorul_meu.fetchall()[0]
		except:
			print('Nu avem populata baza de date a administratorului.')
		if ora_a != ora_anterioara_a:
			ora_anterioara_a = ora_a
			if temperatura_medie_a < prag_inferior_a:
				mesaj = 'Temperatura este prea mica in camera albastra!'
				trimite_mesajul(mesaj,numar_telefon_a)
			elif temperatura_medie_a > prag_superior_a:
				mesaj = 'Temperatura este prea mare in camera albastra!'
				trimite_mesajul(mesaj,numar_telefon_a)
			if abs(diferenta_maxima_a) > diferenta_a:
				mesaj = 'Diferenta valorilor citie de senzori in camera albastra este inadminisbili de mare!'
				trimite_mesajul(mesaj,numar_telefon_admin)
		if ora_p != ora_anterioara_p:
			ora_anterioara_p = ora_p
			if temperatura_medie_p < prag_inferior_p:
				mesaj = 'Temperatura este prea mica in camera portocalie!'
				trimite_mesajul(mesaj,numar_telefon_p)
			elif temperatura_medie_p > prag_superior_p:
				mesaj = 'Temperatura este prea mare in camera portocalie!'
				trimite_mesajul(mesaj,numar_telefon_p)
			if abs(diferenta_maxima_p) > diferenta_p:
				mesaj = 'Diferenta valorilor citie de senzori in camera portocalie este inadminisbili de mare!'
				trimite_mesajul(mesaj,numar_telefon_admin)
		baza_de_date.commit()
	except Exception as e:
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
	#intarziere:
	time.sleep(30) #alegem perioada ca fiind de numatate de  minut