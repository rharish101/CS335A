package main

import "math"

func main() {
	var num float64
	scanln(&num)
	println(num, math.Sin(num), math.Cos(num))
}
