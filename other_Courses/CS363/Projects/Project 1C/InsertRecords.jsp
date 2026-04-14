<%@ page language="java" contentType="text/html; charset=EUC-KR"
	pageEncoding="EUC-KR"%>
<%@ page import="java.io.*, java.util.*,java.sql.*"%>
<%@ page import="jakarta.servlet.http.*, jakarta.servlet.*"%>
<!DOCTYPE html>
<html>
<head>
<meta charset="EUC-KR">
<title>InsertRecords</title>
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
			st.addBatch("use project1;");
			st.addBatch("INSERT ignore INTO students(snum,ssn,name,gender,dob,c_addr,c_phone,p_addr,p_phone)\r\n"
					+ "	values\r\n"
					+ "		(1001,654651234,'Randy','M','2000-12-01','301 E Hall','5152700988','121 Main','7083066321'),\r\n"
					+ "		(1002,123097834,'Victor','M','2000-05-06','270 W Hall','5151234578','702 Walnut','7080366333'),\r\n"
					+ "		(1003,978012431,'John','M','1999-07-08','201 W Hall','5154132805','888 University','5152012011'),\r\n"
					+ "        (1004,746897816,'Seth','M','1998-12-30','199 N Hall','5158891504','21 Green','5154132907'),\r\n"
					+ "        (1005,186032894,'Nicole','F','2001-04-01','178 S Hall','5158891155','13 Gray','5157162071'),\r\n"
					+ "        (1006,534218752,'Becky','F','2001-05-16','12 N Hall','5157083698','189 Clark','2034367632'),\r\n"
					+ "        (1007,432609519,'Kevin','M','2000-08-12','75 E Hall','5157082497','89 National','7182340772');");

			st.addBatch("INSERT ignore INTO departments(code,name,phone,college)" + "	values"
					+ "	(401,'Computer Science', '5152982801', 'LAS')," + "	(402,'Mathematics', '5152982802', 'LAS'),"
					+ "	(403,'Chemical Engineering', '5152982803', 'Engineering'),"
					+ "	(404,'Landscape Architect', '5152982804', 'Design');");
			st.addBatch("INSERT ignore INTO degrees(name, level, department_code)" + "	values "
					+ "	('Computer Science', 'BS', 401)," + "	('Software Engineering', 'BS', 401),"
					+ "	('Computer Science', 'MS', 401)," + "	('Computer Science', 'PhD', 401),"
					+ "	('Applied Mathematics', 'MS', 402)," + "	('Chemical Engineering', 'BS', 403),"
					+ "	('Landscape Architect', 'BS', 404);");
			st.addBatch("INSERT ignore INTO major(snum, name, level)" + "values" + "(1001, 'Computer Science', 'BS'),"
					+ "	(1002, 'Software Engineering', 'BS')," + "	(1003, 'Chemical Engineering', 'BS'),"
					+ "	(1004, 'Landscape Architect', 'BS')," + "	(1005, 'Computer Science', 'MS'),"
					+ "	(1006, 'Applied Mathematics', 'MS')," + "	(1007, 'Computer Science', 'PhD');");
			st.addBatch("INSERT ignore INTO minor(snum, name, level)" + "	values"
					+ "	(1007, 'Applied Mathematics', 'MS')," + "	(1005, 'Applied Mathematics', 'MS'),"
					+ "	(1001, 'Software Engineering', 'BS');");
			st.addBatch("INSERT ignore INTO courses(number, name, description, credithours, level, department_code)\r\n"
					+ "	values\r\n"
					+ "		(113, 'Spreadsheet', 'Microsoft Excel and Access', 3, 'Undergraduate', 401),\r\n"
					+ "        (311, 'Algorithm', 'Design and Analysis', 3, 'Undergraduate', 401),\r\n"
					+ "        (531, 'Theory of Computation', 'Theorem and Porbability', 3 ,'Graduate', 401),\r\n"
					+ "        (363, 'Database', 'Design Principle', 3, 'Undergraduate', 401),\r\n"
					+ "        (412, 'Water Management', 'Water Management', 3, 'Undergraduate', 404),\r\n"
					+ "        (228, 'Special Topics', 'Intersting Topics about CE', 3, 'Undergraduate', 403),\r\n"
					+ "        (101, 'Calculus', 'Limit and Derivative', 4, 'Undergraduate', 402);");
			st.addBatch("INSERT ignore INTO register(snum, course_number, regtime, grade)" + "	values"
					+ "	(1001, 363, 'Fall2020', 3)," + "	(1002, 311, 'Fall2020', 4),"
					+ "	(1003, 228, 'Fall2020', 4)," + " (1004, 363, 'Spring2021', 3),"
					+ "	(1005, 531, 'Spring2021', 4)," + "	(1006, 363, 'Fall2020', 3),"
					+ "	(1007, 531, 'Spring2021', 4);");

			st.executeBatch();

			System.out.println("Data records are inserted");

		} catch (ClassNotFoundException | SQLException e) {
			// TODO Auto-generated catch block
			System.out.println("Error in insert data records: " + e.getMessage());
			e.printStackTrace();
		}
	}%>
	<%
	String but = request.getParameter("button1");
	out.println("Click \"Submit\" to insert data records.");

	if ("Submit".equals(but)) {
		createTable();
		String URL = "InsertRecordsResult.jsp";
		response.sendRedirect(URL);
	}
	%>

	<form method="post">
		<input type="submit" name="button1" value="Submit" />

	</form>
</body>
</html>