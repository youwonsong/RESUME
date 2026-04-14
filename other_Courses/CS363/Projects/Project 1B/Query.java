package project1b;

import java.sql.*;

public class Query {
	private static Connection connect = null;

	public static void main(String[] args) {
		try {
			String userName = "coms363";
			String password = "password";
			String dbServer = "jdbc:mysql://localhost:3306/project1";

			connect = DriverManager.getConnection(dbServer, userName, password);

		} catch (Exception e) {
			System.out.println(e);
		}

		Statement st = null;

		ResultSet result = null;
		String sqlQ = "";
		String outputStr = "";

		try {
			st = connect.createStatement();
			sqlQ = "select snum, ssn from students where name = 'Becky';";
			result = st.executeQuery(sqlQ);
			outputStr = "#1\n";

			while (result.next()) {
				outputStr += "Student#: " + result.getInt("snum") + "\n";
				outputStr += "SSN: " + result.getInt("ssn") + "\n";
			}

			System.out.println(outputStr + "\n");

			sqlQ = "select M.name,M.level from major M\r\n" + "	inner join students S \r\n" + "	on M.snum = S.snum \r\n"
					+ "	and S.ssn = '123097834';";
			result = st.executeQuery(sqlQ);
			outputStr = "#2\n";

			while (result.next()) {
				outputStr += "Major: " + result.getString("name") + "\n";
				outputStr += "Level: " + result.getString("level") + "\n";
			}

			System.out.println(outputStr + "\n");

			sqlQ = "select C.name from courses C\r\n" + "	inner join departments D \r\n"
					+ "	on c.department_code = D.code\r\n" + "	and D.name = 'Computer Science';";
			result = st.executeQuery(sqlQ);
			outputStr = "#3\n";
			while (result.next()) {
				outputStr += "Course Subject: " + result.getString("name") + "\n";
			}

			System.out.println(outputStr + "\n");

			sqlQ = "select G.name, G.level from degrees G\r\n" + "	inner join departments D\r\n"
					+ "    on g.department_code = d.code\r\n" + "	and D.name = 'Computer Science';";
			result = st.executeQuery(sqlQ);
			outputStr = "#4\n";
			while (result.next()) {
				outputStr += "Major: " + result.getString("name") + "\n";
			}

			System.out.println(outputStr + "\n");

			sqlQ = "select S.name from students S\r\n" + "	inner join minor N\r\n" + "    on S.snum = N.snum;";
			result = st.executeQuery(sqlQ);
			outputStr = "#5\n";

			while (result.next()) {
				outputStr += "Student Name: " + result.getString("name") + "\n";
			}

			System.out.println(outputStr + "\n");

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
