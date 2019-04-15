package main

import "fmt"

func callMyFunc() bool {
	//println("This should not print\n")
	println(0)
	return bool(1)
}

func main() {
	a := 0
	if (a >= 0 || callMyFunc()) {
		//println("This should print in first line\n")
		println(1)
	}
	if (a > 0 && callMyFunc()) {
		//println("This should not print in second line\n")
		println(2)
	} else {
		//println("This should print in second line\n")
		println(3)
	}
}