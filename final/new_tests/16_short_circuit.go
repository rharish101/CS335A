package main

import "fmt"

func callMyFunc() bool {
	println("This should not print\n")
	return true
}

func main() {
	a := 0
	if (a >= 0 || callMyFunc()) {
		println("This should print in first line\n")
	}
	if (a > 0 && callMyFunc()) {
		println("This should not print in second line\n")
	} else {
		println("This should print in second line\n")
	}
}