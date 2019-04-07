package main

func Factorial(n uint64)(result uint64) {
	if (n > 0) {
		var result uint64 = n * Factorial(n-1)
		return result
	}
	return 1
}

func main() {

}