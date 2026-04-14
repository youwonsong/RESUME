<%@ page language="java" contentType="text/html; charset=EUC-KR"
	pageEncoding="EUC-KR"%>

<!DOCTYPE html>
<html>
<head>
<meta charset="EUC-KR">
<title>QueryResult1</title>
</head>
<body>
	<sql:setDataSource var="myDS" driver="com.mysql.jdbc.Driver"
		url="jdbc:mysql://127.0.0.1:3306/?user=coms363" user="coms363"
		password="password" />

	<sql:query var="query" dataSource="${myDS}">
        select snum, ssn from students where name = 'Becky';
    </sql:query>

	<div align="center">
		<table border="1">
			<h1>This is the result of query 1</h1>
			<tr>
				<th>snum</th>
				<th>ssn</th>
			</tr>
			<c:forEach var="result" items="${query1.rows}">
				<tr>
					<td><c:out value="${result.snum}" /></td>
					<td><c:out value="${result.ssn}" /></td>
				</tr>
			</c:forEach>
		</table>
	</div>
</body>
</html>