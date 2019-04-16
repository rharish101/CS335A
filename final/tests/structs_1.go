package main

type mystruct struct {
	val int
}

type mystruct1 struct {
	val mystruct
}

func fact(i int) int {
	if (i == 0) {
		return 1
	}
	println(2)
	return i * fact(i-1)
}

func main() {
	var s mystruct1 = mystruct1{mystruct{2} }
	var t mystruct1 = mystruct1{mystruct{7} }
	s.val.val = 5
	println(fact(s.val.val), fact(t.val.val))
	// fact(2)
}
