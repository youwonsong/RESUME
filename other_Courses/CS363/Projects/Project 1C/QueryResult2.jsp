<%@ page language="java" contentType="text/html; charset=EUC-KR"
	pageEncoding="EUC-KR"%>
<!DOCTYPE html>
<html>
<head>
<meta charset="EUC-KR">
<title>QueryResult2</title>
</head>
<body>
	<sql:setDataSource var="myDS" driver="com.mysql.jdbc.Driver"
		url="jdbc:mysql://127.0.0.1:3306/?user=coms363" user="coms363"
		password="password" />

	<sql:query var="query" dataSource="${myDS}">
        select C.name, C.level from courses C inner join departments D 
	on c.department_code = D.code
	and D.name = 'Computer Science';
    </sql:query>

	<div align="center">
		<table border="1">
			<h1>This is the result of query 1</h1>
			<tr>
				<th>C.name</th>
				<th>C.level</th>
			</tr>
			<c:forEach var="result" items="${query1.rows}">
				<tr>
					<td><c:out value="${result.C.name}" /></td>
					<td><c:out value="${result.C.level}" /></td>
				</tr>
			</c:forEach>
		</table>
	</div>
</body>
</html>