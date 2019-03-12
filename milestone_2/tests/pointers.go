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
	**c = 1
	*b = 1

	var x [3]int
	x[1] = 3

	var y *int
	y = &x[1]

	/*a := 2
	b := &a

	c := 1.5
	d := &c

	b = d*/
}
