package main

func Factorial(n uint32)(result uint32) {
	if (n > 0) {
		var result uint32 = n * Factorial(n-1)
		return result
	}
	return 1
}

func main() {
    var num1, num2 uint32
    scanln(&num1, &num2)
    a := Factorial(num1)
    b := Factorial(num2)
    println(a, b)
}
