package main

func Factorial(n uint32)(result uint32) {
	if (n > 0) {
		var result uint32 = n * Factorial(n-1)
		return result
	}
	return 1
}

func main() {
    a := Factorial(3)
}
