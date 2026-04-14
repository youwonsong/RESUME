package varlang;
import java.io.IOException;

import varlang.Env;
import varlang.Value;
import varlang.AST.Program;

/**
 * This main class implements the Read-Eval-Print-Loop of the interpreter with
 * the help of Reader, Evaluator, and Printer classes. 
 * 
 * @author hridesh
 *
 */
public class Interpreter {
	public static void main(String[] args) {
		System.out.println("Type a program to evaluate and press the enter key," + 
							" e.g. (let ((a 3) (b 100) (c 84) (d 279) (e 277)) (+ (* a b) (/ c (- d e)))) \n" + 
							"Press Ctrl + C to exit.");
		Reader reader = new Reader();
		Evaluator eval = new Evaluator();
		Printer printer = new Printer();
		REPL: while (true) { // Read-Eval-Print-Loop (also known as REPL)
			Program p = null;
			int count = 0;
			try {
				p = reader.read();
				for(int i =0; i<p.toString().length(); i++){
					if(p.toString().charAt(i)=='a'){
						count++;
					}
					if(count>3){
						System.out.println("Error");
						break REPL;
					}
				}
				if(p._e == null) continue REPL;
				Value val = eval.valueOf(p);
				printer.print(val);
			} catch (Env.LookupException e) {
				printer.print(e);
			} catch (IOException e) {
				System.out.println("Error reading input:" + e.getMessage());
			} catch (NullPointerException e) {
				System.out.println("Error:" + e.getMessage());
			}
		}
	}
}
