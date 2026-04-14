<%@ page language="java" contentType="text/html; charset=EUC-KR"
	pageEncoding="EUC-KR"%>
<%@ page import="java.io.*, java.util.*,java.sql.*"%>
<%@ page import="jakarta.servlet.http.*, jakarta.servlet.*"%>
<!DOCTYPE html>
<html>
<head>
<meta charset="EUC-KR">
<title>CreateTables</title>
</head>
<body>

	<%!public void createTable() {
		String connectionURL = "jdbc:mysql://127.0.0.1:3306/?user=coms363";
		Connection connection = null;

		Statement st = null;

		try {
			Class.forName("com.mysql.jdbc.Driver");
			connection = DriverManager.getConnection(connectionURL, "coms363", "password");

			st = connection.createStatement();
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

			st.executeBatch();

			System.out.println("Tables are created");

		} catch (ClassNotFoundException | SQLException e) {
			// TODO Auto-generated catch block
			System.out.println("Error in create table: " + e.getMessage());
			e.printStackTrace();
		}
	}%>
	<%
	String but = request.getParameter("button1");
	out.println("Click \"Submit\" to create tables.");

	if ("Submit".equals(but)) {
		createTable();
		String redirect = "CreateTablesResult.jsp";
		response.sendRedirect(redirect);
	}
	%>

	<form method="post">
		<input type="submit" name="button1" value="Submit" />

	</form>
</body>
</html>