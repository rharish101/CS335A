package main

import "fmt"

func fibo_iter(n int) {
	a := 0
	b := 1
	for (i := 0; i < n; i++) {
		println( a)
		a,b = b,a+b
	}
}

func main() {
	a := 0
	scanln(&a)
	fibo_iter(a)
}