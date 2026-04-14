package project1b;

import java.sql.*;

public class CreateTables {

	private static Connection connect = null;

	public static void main(String[] args) throws SQLException {

		try {
			String userName = "coms363";
			String password = "password";
			String dbServer = "jdbc:mysql://localhost:3306/";

			connect = DriverManager.getConnection(dbServer, userName, password);
		} catch (Exception e) {
			System.out.println(e);
		}

		Statement st = null;

		try {
			st = connect.createStatement();
			st.addBatch("drop database if exists project1;\r\n");
			st.addBatch("create database if not exists project1;\r\n");
			st.addBatch("use project1;\r\n");
			st.addBatch("CREATE TABLE IF NOT EXISTS students (\r\n" + "    snum int,\r\n" + "    ssn int,\r\n"
					+ "    name varchar(10),\r\n" + "    gender varchar(1),\r\n" + "    dob datetime,\r\n"
					+ "    c_addr varchar(20),\r\n" + "    c_phone varchar(10),\r\n" + "    p_addr varchar(20),\r\n"
					+ "    p_phone varchar(10),\r\n" + "	primary key(ssn),\r\n" + "    unique(snum)\r\n" + ");");
			st.addBatch("CREATE TABLE IF NOT EXISTS departments(\r\n" + "	code int,\r\n" + "    name varchar(50),\r\n"
					+ "    phone varchar(10),\r\n" + "    college varchar(20),\r\n" + "	primary key(code),\r\n"
					+ "    unique(name)\r\n" + ");");
			st.addBatch("CREATE TABLE IF NOT EXISTS degrees(\r\n" + "	name varchar(50),\r\n"
					+ "    level varchar(5),\r\n" + "    department_code int,\r\n" + "	primary key(name, level),\r\n"
					+ "    foreign key(department_code) references departments(code)\r\n" + ");");
			st.addBatch("CREATE TABLE IF NOT EXISTS courses(\r\n" + "	number int,\r\n" + "    name varchar(50),\r\n"
					+ "    description varchar(50),\r\n" + "    credithours int,\r\n" + "    level varchar(20),\r\n"
					+ "    department_code int,\r\n" + "    primary key(number),\r\n" + "    unique(name),\r\n"
					+ "    foreign key(department_code) references departments(code)\r\n" + ");");
			st.addBatch("CREATE TABLE IF NOT EXISTS register(\r\n" + "	snum int,\r\n" + "    course_number int,\r\n"
					+ "    regtime varchar(20),\r\n" + "    grade int,\r\n" + "    primary key(snum,course_number),\r\n"
					+ "    foreign key(snum) references students(snum),\r\n"
					+ "    foreign key(course_number) references courses(number)\r\n" + ");");
			st.addBatch("CREATE TABLE IF NOT EXISTS major(\r\n" + "	snum int,\r\n" + "    name varchar(50),\r\n"
					+ "    level varchar(5),	\r\n" + "    primary key(snum, name, level),\r\n"
					+ "    foreign key(snum) references students(snum),\r\n"
					+ "    foreign key(name,level) references degrees(name,level)\r\n" + ");");
			st.addBatch("CREATE TABLE IF NOT EXISTS minor(\r\n" + "	snum int,\r\n" + "    name varchar(50),\r\n"
					+ "    level varchar(5),\r\n" + "    primary key(snum, name, level),\r\n"
					+ "    foreign key(snum) references students(snum),\r\n"
					+ "    foreign key(name,level) references degrees(name,level)\r\n" + ");");

		} catch (SQLException e) {
			e.printStackTrace();
		}

		try {
			st.executeBatch();
		} catch (SQLException e) {
			e.printStackTrace();
		} finally {
			try {
				if (st != null) {
					st.close();
				}
				if (connect != null) {
					connect.close();
				}
			} catch (Exception e) {
				e.printStackTrace();
			}
		}
	}
}
