package main

func FibonacciRecursion(n int) int {
    if( n <= 1 ){
        return n
    }
    return FibonacciRecursion(n-1) + FibonacciRecursion(n-2)
}

func main(){
	var n int
	scanln(&n)
	a := FibonacciRecursion(n)
	println(a)
}