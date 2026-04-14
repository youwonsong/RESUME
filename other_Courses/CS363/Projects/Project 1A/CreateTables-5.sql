use project1;



CREATE TABLE IF NOT EXISTS students (
    snum int,
    ssn int,
    name varchar(10),
    gender varchar(1),
    dob datetime,
    c_addr varchar(20),
    c_phone varchar(10),
    p_addr varchar(20),
    p_phone varchar(10),
	primary key(ssn),
    unique(snum)
);

CREATE TABLE IF NOT EXISTS departments(
	code int,
    name varchar(50),
    phone varchar(10),
    college varchar(20),
	primary key(code),
    unique(name)
);

CREATE TABLE IF NOT EXISTS degrees(
	name varchar(50),
    level varchar(5),
    department_code int,
	primary key(name, level),
    foreign key(department_code) references departments(code)
);

CREATE TABLE IF NOT EXISTS courses(
	number int,
    name varchar(50),
    description varchar(50),
    credithours int,
    level varchar(20),
    department_code int,
    primary key(number),
    unique(name),
    foreign key(department_code) references departments(code)
);

CREATE TABLE IF NOT EXISTS register(
	snum int,
    course_number int,
    regtime varchar(20),
    grade int,
    primary key(snum,course_number),
    foreign key(snum) references students(snum),
    foreign key(course_number) references courses(number)
);

CREATE TABLE IF NOT EXISTS major(
	snum int,
    name varchar(50),
    level varchar(5),
    primary key(snum, name, level),
    foreign key(snum) references students(snum),
    foreign key(name,level) references degrees(name,level)
);

CREATE TABLE IF NOT EXISTS minor(
	snum int,
    name varchar(50),
    level varchar(5),
    primary key(snum, name, level),
    foreign key(snum) references students(snum),
    foreign key(name,level) references degrees(name,level)
);