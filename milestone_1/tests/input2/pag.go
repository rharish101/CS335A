package main

import "fmt"

func goo(c, d, e int_t) int {
	fmt.Println(c + d)
	fmt.Println(e)
	fmt.Println(d)
	return
}

func foo(a, b int_t) int {
	fmt.Println(a)
	fmt.Println(b)
	goo(1, 2, 3)
	return
}

func main() {
	var i, j int_t = 3, 4
	foo(i, j)
	return
}
