package main

import "fmt"

func main() {
	/* local variable definition */
	var a int = 10

	/* for loop execution */
	for (a := 10; a < 20; a += 1) {
		fmt.Printf("value of a: %d\n", a)
		a++
		if (a > 15) {
			/* terminate the loop using break statement */
			break
		}
	}
}
