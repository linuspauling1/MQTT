drop table if exists temperaturi;
drop table if exists camere;
create table camere (
	prag_inferior decimal(3,1) default 20.0,
    prag_superior decimal(3,1) default 25.0,
    perioada int default 500, -- se ofera in ms
    diferenta_wifi decimal(3,1) default 2.5,
    diferenta_total decimal(3,1) default 5.0,
    nume_camera varchar(20),
    primary key(nume_camera)
);
insert into camere(nume_camera) values('portocalie'); -- avem doar doua camere
insert into camere(nume_camera) values('albastra'); -- care vor ramane asa pe parcursul aplicatiei
create table temperaturi (
	temperatura_wifith1 decimal(3,1), -- temperaturile sunt oferite in grade Celsius
    temperatura_wifith2 decimal(3,1), -- valorile default sunt absurde tocmai pentru
    temperatura_1wire decimal(3,1), -- semnalarea de erori
    pondere_wifith1 int default 30, -- ponderile vor fi procente intregi
    pondere_wifith2 int default 30,
    pondere_1wire int default 40,
    temperatura_medie decimal(3,1), -- va fi calculata automat
    ora timestamp default 0, -- data si ora la care se face insertia
    nume_camera varchar(20) not null, -- are maxim 20 de caractere
    indice int default 1, -- de regula nu schimbam defaultul
    primary key(indice),
    foreign key(nume_camera) references camere(nume_camera)
);
-- trigger ora pentru insertie
create trigger trig_ora_insert before insert on temperaturi for each row set new.ora = now();
-- trigger ora pentru actualizare
-- create trigger trig_ora_update before update on temperaturi for each row set new.ora = now();
-- trigger temperatura medie pentru insertie
create trigger trig_medie_insert before insert on temperaturi
for each row set new.temperatura_medie = (new.temperatura_wifith1*new.pondere_wifith1 + new.temperatura_wifith2*new.pondere_wifith2 + new.temperatura_1wire*new.pondere_1wire)/100;
-- trigger temperatura medie pentru actualizare
create trigger trig_medie_update before update on temperaturi
for each row set new.temperatura_medie = (new.temperatura_wifith1*new.pondere_wifith1 + new.temperatura_wifith2*new.pondere_wifith2 + new.temperatura_1wire*new.pondere_1wire)/100;
-- testare:
-- call insertie_initiala();
-- call adaugare(99); -- o vom apela obligatoriu inainte de fiecare insert