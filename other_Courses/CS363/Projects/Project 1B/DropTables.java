package project1b;

import java.sql.*;

public class DropTables {
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

		try {
			st = connect.createStatement();

			st.addBatch(
					"drop table if exists\r\n" + "	courses, degrees, departments, major, minor, register, students;");

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
