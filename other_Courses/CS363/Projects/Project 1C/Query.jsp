<%@ page language="java" contentType="text/html; charset=EUC-KR"
	pageEncoding="EUC-KR"%>
<%@ page import="java.io.*, java.util.*,java.sql.*"%>
<%@ page import="jakarta.servlet.http.*, jakarta.servlet.*"%>
<!DOCTYPE html>
<html>
<head>
<meta charset="EUC-KR">
<title>Query</title>
</head>
<body>

	<%
	String but1 = request.getParameter("button1");

	if ("Q1".equals(but1)) {
		String redirect = "QueryResult1.jsp";
		response.sendRedirect(redirect);
	}

	String but2 = request.getParameter("button2");

	if ("Q2".equals(but2)) {
		String redirect = "QueryResult2.jsp";
		response.sendRedirect(redirect);
	}

	String but3 = request.getParameter("button3");

	if ("Q3".equals(but3)) {
		String redirect = "QueryResult3.jsp";
		response.sendRedirect(redirect);
	}
	%>

	<form method="post">
		Click "Q1" to see result of query1.<br> <input type="submit"
			name="button1" value="Q1" />
	</form>
	<form>
		Click "Q2" to see result of query2.<br> <input type="submit"
			name="button2" value="Q2" />
	</form>
	<form>
		Click "Q3" to see result of query3.<br> <input type="submit"
			name="button3" value="Q3" />
	</form>
</body>
</html>