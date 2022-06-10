drop table if exists temperaturi;
drop table if exists camere;
drop table if exists utilizatori;
drop table if exists administrator;
create table administrator( -- tablea speciala
	numar_telefon varchar(10) default '0744604883' not null, -- ar trebui editat daca schimbam numarul de telefon
    nume_admin varchar(20) default 'admin' not null,
    parola_admin varchar(20) default 'admin' not null,
    nr_crt int default 1 primary key check(nr_crt = 1) -- ne asiguram ca intrarea este unica
);
insert into administrator() values();
create table utilizatori (
	numar_telefon varchar(10), -- de regula au 10 caractere numerele de telefon, maxim
    nume_utilizator varchar(20) default 'user' not null, -- numele utilizatorului
    parola_utilitzor varchar(20) default 'user' not null, -- parola utilizatorului
    primary key(numar_telefon)
);
-- insertie de proba
insert into utilizatori values('0744604883', 'agrise', 'mure');
create table camere (
    nume_camera varchar(20),
	prag_inferior decimal(3,1) default 20.0,
    prag_superior decimal(3,1) default 30.0,
    perioada int default 2000, -- se ofera in ms, ar fi bine sa fie minim 2s
    diferenta decimal(3,1) default 10.0,
    numar_telefon varchar(10),
    primary key(nume_camera),
    foreign key(numar_telefon) references utilizatori(numar_telefon) on update cascade
);
-- trigger pentru prag_inferior la update si insert
DELIMITER $$
CREATE TRIGGER prag_inferior_update BEFORE UPDATE ON camere FOR EACH ROW
BEGIN
	if old.prag_superior <= new.prag_inferior then -- noul prag inferior nu trebuie sa fie mai mare decat vechiul prag inferior
		set new.prag_inferior = old.prag_inferior;
	end if;
END$$    
DELIMITER ;
DELIMITER $$
CREATE TRIGGER prag_inferior_insert BEFORE insert ON camere FOR EACH ROW
BEGIN
	if new.prag_superior <= new.prag_inferior then -- noul prag inferior nu trebuie sa fie mai mare decat pragul inferior
		set new.prag_inferior = new.prag_superior - new.diferenta; -- consideram situatia extrema
	end if;
END$$    
DELIMITER ;
-- trigger pentru prag_superior la update si insert
DELIMITER $$
CREATE TRIGGER prag_superior_update BEFORE UPDATE ON camere FOR EACH ROW
BEGIN
	if old.prag_inferior >= new.prag_superior then -- pragul superior nu trebuie sa fie mai mic decat vechiul prag inferior
		set new.prag_superior = old.prag_superior;
	end if;
END$$    
DELIMITER ;
DELIMITER $$
CREATE TRIGGER prag_superior_insert BEFORE insert ON camere FOR EACH ROW
BEGIN
	if new.prag_superior <= new.prag_inferior then -- pragl superior nu trebuie sa fie mai mic decat pragul inferior
		set new.prag_superior = new.prag_inferior + new.diferenta; -- consideram situatia extrema
	end if;
END$$    
DELIMITER ;
-- noua tabela:
insert into camere(nume_camera, numar_telefon) values('portocalie','0744604883'); -- avem doar doua camere
insert into camere(nume_camera, numar_telefon) values('albastra','0744604883'); -- care vor ramane asa pe parcursul aplicatiei
create table temperaturi (
	temperatura_wifith1 decimal(3,1), -- temperaturile sunt oferite in grade Celsius
    temperatura_wifith2 decimal(3,1), -- valorile default sunt absurde tocmai pentru
    temperatura_1wire decimal(3,1), -- semnalarea de erori
    temperatura_medie decimal(3,1), -- va fi calculata automat
    diferenta decimal(3,1), -- va fi calculata automat
    ora timestamp default 0, -- data si ora la care se face insertia
    nume_camera varchar(20) not null, -- are maxim 20 de caractere
    indice int default 1, -- de regula nu schimbam defaultul
    primary key(indice, nume_camera), -- cheie primara compozit
    foreign key(nume_camera) references camere(nume_camera) on update cascade
);
-- trigger ora pentru insertie
create trigger trig_ora_insert before insert on temperaturi for each row set new.ora = now();
-- trigger ora pentru actualizare
-- create trigger trig_ora_update before update on temperaturi for each row set new.ora = now();
-- trigger temperatura medie pentru insertie
create trigger trig_medie_insert before insert on temperaturi
for each row set new.temperatura_medie = (new.temperatura_wifith1+new.temperatura_wifith2+new.temperatura_1wire)/3;
-- trigger temperatura medie pentru actualizare
-- create trigger trig_medie_update before update on temperaturi
-- for each row set new.temperatura_medie = (new.temperatura_wifith1+new.temperatura_wifith2+new.temperatura_1wire)/3;
DELIMITER $$
CREATE TRIGGER trigger_medie BEFORE UPDATE ON temperaturi FOR EACH ROW
BEGIN
	if abs(old.temperatura_wifith1 - old.temperatura_wifith2) > abs(old.temperatura_wifith1 - old.temperatura_1wire) then
		if abs(old.temperatura_wifith1 - old.temperatura_1wire) > abs(old.temperatura_wifith2 - old.temperatura_1wire) then
			set new.temperatura_medie = (old.temperatura_wifith2 + old.temperatura_1wire)/2;
		else
			set new.temperatura_medie = (old.temperatura_wifith1 + old.temperatura_1wire)/2;
		end if;
	else
		if abs(old.temperatura_wifith1 - old.temperatura_wifith2) > abs(old.temperatura_wifith2 - old.temperatura_1wire) then
			set new.temperatura_medie = (old.temperatura_wifith2 + old.temperatura_1wire)/2;
		else
			set new.temperatura_medie = (old.temperatura_wifith1 + old.temperatura_wifith2)/2;
		end if;
	end if;
END$$    
DELIMITER ;

DELIMITER $$
CREATE TRIGGER trigger_medie_insertie BEFORE insert ON temperaturi FOR EACH ROW
BEGIN
	if abs(new.temperatura_wifith1 - new.temperatura_wifith2) >= abs(new.temperatura_wifith1 - new.temperatura_1wire) then
		if abs(new.temperatura_wifith1 - new.temperatura_1wire) >= abs(new.temperatura_wifith2 - new.temperatura_1wire) then
			set new.temperatura_medie = (new.temperatura_wifith2 + new.temperatura_1wire)/2;
		else
			set new.temperatura_medie = (new.temperatura_wifith1 + new.temperatura_1wire)/2;
		end if;
	else
		if abs(new.temperatura_wifith1 - new.temperatura_wifith2) >= abs(new.temperatura_wifith2 - new.temperatura_1wire) then
			set new.temperatura_medie = (new.temperatura_wifith2 + new.temperatura_1wire)/2;
		else
			set new.temperatura_medie = (new.temperatura_wifith1 + new.temperatura_wifith2)/2;
		end if;
	end if;
END$$    
DELIMITER ;

DELIMITER $$
CREATE TRIGGER trigger_diferenta BEFORE UPDATE ON temperaturi FOR EACH ROW
BEGIN
	if(abs(new.temperatura_medie - new.temperatura_wifith1) > abs(new.temperatura_medie - new.temperatura_wifith2)) then
		if(abs(new.temperatura_medie - new.temperatura_wifith1) > abs(new.temperatura_medie - new.temperatura_1wire)) then
			set new.diferenta = new.temperatura_medie - new.temperatura_wifith1;
        else
			set new.diferenta = new.temperatura_medie - new.temperatura_1wire;
        end if;
    else
		if(abs(new.temperatura_medie - new.temperatura_wifith2) > abs(new.temperatura_medie - new.temperatura_1wire)) then
			set new.diferenta = new.temperatura_medie - new.temperatura_wifith2;
        else
			set new.diferenta = new.temperatura_medie - new.temperatura_1wire;
        end if;
    end if;
END$$    
DELIMITER ;

DELIMITER $$
CREATE TRIGGER trigger_diferenta_insertie BEFORE insert ON temperaturi FOR EACH ROW
BEGIN
	if(abs(new.temperatura_medie - new.temperatura_wifith1) > abs(new.temperatura_medie - new.temperatura_wifith2)) then
		if(abs(new.temperatura_medie - new.temperatura_wifith1) > abs(new.temperatura_medie - new.temperatura_1wire)) then
			set new.diferenta = new.temperatura_wifith1 - new.temperatura_medie;
        else
			set new.diferenta = new.temperatura_1wire - new.temperatura_medie;
        end if;
    else
		if(abs(new.temperatura_medie - new.temperatura_wifith2) > abs(new.temperatura_medie - new.temperatura_1wire)) then
			set new.diferenta = new.temperatura_wifith2 - new.temperatura_medie;
        else
			set new.diferenta = new.temperatura_1wire - new.temperatura_medie;
        end if;
    end if;
END$$    
DELIMITER ;