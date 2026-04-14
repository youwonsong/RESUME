package project1b;

import java.sql.*;

public class ModifyRecords {
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

			st.addBatch("update students\r\n" + "	set name = 'Scott'\r\n" + "    where ssn = '746897816';");

			st.addBatch("update major M " + "	join students S on S.snum = M.snum"
					+ "	set M.name = 'Computer Science' , M.level = 'MS'" + "	where S.ssn = 746897816;");
			st.addBatch("set sql_safe_updates = 0;");
			st.addBatch("delete from register\r\n" + "	where regtime = 'Spring2021';\r\n");
			st.addBatch("set sql_safe_updates = 1;");

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
