<%@ page language="java" contentType="text/html; charset=EUC-KR"
	pageEncoding="EUC-KR"%>
<%@ page import="java.io.*, java.util.*,java.sql.*"%>
<%@ page import="jakarta.servlet.http.*, jakarta.servlet.*"%>
<!DOCTYPE html>
<html>
<head>
<meta charset="EUC-KR">
<title>ModifyRecords</title>
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
			st.addBatch("update students\r\n" + "	set name = 'Scott'\r\n" + "    where ssn = '746897816';");

			st.executeBatch();

			System.out.println("Data records are modified");

		} catch (ClassNotFoundException | SQLException e) {
			// TODO Auto-generated catch block
			System.out.println("Error in modify records: " + e.getMessage());
			e.printStackTrace();
		}
	}%>
	<%
	String but = request.getParameter("button1");
	out.println("Click \"Submit\" to modify records.");

	if ("Submit".equals(but)) {
		createTable();
		String redirect = "ModifyRecordsResult.jsp";
		response.sendRedirect(redirect);
	}
	%>

	<form method="post">
		<input type="submit" name="button1" value="Submit" />

	</form>
</body>
</html>