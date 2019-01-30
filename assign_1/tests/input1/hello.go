package main

// Yo
/* Hello "world" program
   In Go*/

import "fmt"

func main() {
	fmt.Println("help \"me\"")
	fmt.Println(`hello /*world*/
	Yo buddy
	`)
	fmt.Println('\n')
	fmt.Println(.2e0 / (2 + 3i))
	fmt.Println(0x5 &^ 0x1)
}
