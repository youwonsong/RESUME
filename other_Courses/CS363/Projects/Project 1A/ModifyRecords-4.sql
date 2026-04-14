/*1*/
update students
	set name = 'Scott'
    where ssn = '746897816';
    
/*2*/    
update major M  join students S on S.snum = M.snum
	set M.name = 'Computer Science' , M.level = 'MS'
    where S.ssn = 746897816;
    
/*3*/
set sql_safe_updates = 0;    
delete from register
	where regtime = 'Spring2021';
set sql_safe_updates = 1;