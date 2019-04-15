package main


type mystruct struct {
	val int
}

func fact(i int) int {
	if(i == 0) {
		return 1
	}
	return i * fact(i-1)
}

func main() {
	var x [2][3]int
	x[0][0] = 5
	println(fact(x[0][0]))
}