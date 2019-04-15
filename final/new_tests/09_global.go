package main

var a int
var b [45]int

func main() {
	a = 10
	println(a)
	for (i := 0; i < 45; i++) {
		b[i] = i + 67
	}
	for (i := 0; i < 45; i++) {
		println(b[i])
	}
}