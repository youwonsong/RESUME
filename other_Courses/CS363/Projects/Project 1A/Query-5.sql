/*1*/
select snum, ssn from students where name = 'Becky';

/*2*/
select M.name,M.level from major M inner join students S 
	on M.snum = S.snum 
	and S.ssn = '123097834';

/*3*/
select C.name from courses C inner join departments D 
	on c.department_code = D.code
	and D.name = 'Computer Science';

/*4*/
select G.name, G.level from degrees G inner join departments D
    on g.department_code = d.code
	and D.name = 'Computer Science';
    
/*5*/
select S.name from students S inner join minor N
    on S.snum = N.snum;
    
/*6*/
select COUNT(*) AS count from students S inner join minor N
    on S.snum = N.snum;
    
/*7*/
select S.name, S.snum from students S inner join register R inner join courses C
    on S.snum = R.snum
    and R.course_number = C.number
    and C.name = 'Algorithm';
    
/*8*/
select name,snum from students
	where dob = (select MIN(dob) from students);
    
/*9*/
select name,snum from students
	where dob = (select MAX(dob) from students);
    
/*10*/
select name,snum,ssn from students where name LIKE '%n%';

/*11*/
select name,snum,ssn from students where name NOT LIKE '%n%';

/*12*/
select C.number, C.name, count(R.course_number) AS registree from courses C inner join register R
    on C.number = R.course_number
    group by R.course_number; 

/*13*/
select S.name from students S inner join register R
    on S.snum = R.snum
    and R.regtime = 'Fall2020';
    
/*14*/
select C.number, C.name from courses C inner join departments D
    on C.department_code = D.code
    and D.name = 'Computer Science';
    
/*15*/
select C.number, C.name from courses C inner join departments D
    on C.department_code = D.code
    and (D.name = 'Computer Science' or D.name = 'Landscape Architect');