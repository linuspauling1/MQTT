CREATE DEFINER=`root`@`%` PROCEDURE `adaugare`(IN valoare_maxima int)
BEGIN
	declare var1 int;
    declare iterator int default 99;
    declare cursorul cursor for select max(indice) from temperaturi;
    set iterator = valoare_maxima - 1;
    open cursorul;
    fetch cursorul into var1;
    close cursorul;
	if var1 >= valoare_maxima then
		delete from temperaturi where indice >= valoare_maxima;
	end if; -- am sters elementele in plus
    eticheta: loop
		update temperaturi
		set indice = iterator + 1
		where indice = iterator;
		set iterator = iterator - 1;
		if iterator < 1 then
			leave eticheta;
		end if;
    end loop; -- am actualizat valorile indicilor
END
