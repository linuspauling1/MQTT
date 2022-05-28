CREATE PROCEDURE `insertie_initiala` ()
BEGIN
	declare iterator int default 0;
    declare maxim int default 100;
    eticheta: LOOP
    insert into temperaturi(indice) values(iterator);
    set iterator = iterator + 1;
    IF iterator < maxim THEN
        LEAVE eticheta;
    END IF;
END LOOP;
END
