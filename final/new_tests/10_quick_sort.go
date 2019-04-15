package main

import "fmt"

var A [100]int

func partition(p int, r int) int {
	x := A[p]
	i := p - 1
	j := r + 1

	for(;;) {
		j--
		kk := A[j]
		for (;kk < x;) {
			j--
			kk = A[j]
		}
		i++
		for (;A[i] > x;) {
			i++
		}
		if (i < j) {
			tmp := A[i]
			A[i] = A[j]
			A[j] = tmp
		} else {
			return j
		}
	}
	return -1
}
func qsort(p int, r int) {
	if (p < r) {
		q := partition(p, r)
		qsort(p, q)
		qsort(q+1, r)
	}
}

func main() {
	for (i := 0; i < 10; i++) {
		n := 0
		scanln(&n)
		A[i] = n
	}

	qsort(0, 9)

	for (i := 0; i < 10; i++) {
		println(A[i])
	}
}