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

	var w int = 3
	*(&w) = 5
	println(w)
}
