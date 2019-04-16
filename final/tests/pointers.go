package main

import (
	"fmt"
)

func main() {
	a := 2
	b := &a
	c := &b
	d := *b
	e := **c
	println(e)
	**c = 1
	*b = 1 

	z := 4 + **c
	println(z)
	var x [3]int
	x[1] = 3

	var y *int
	y = &x[1]

	var w int = 3
	*(&w) = 5
	println(w)

	// a := 2
	// b := &a

	// c := 1
	// d := &c

	// b = d
}
