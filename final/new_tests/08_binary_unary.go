package main


func main() {
	a := 89
	b := -17
	c := a + b
	d := -c
	e := a - (-c) + (-(-b))
	println(a, b, c, d, e)
}