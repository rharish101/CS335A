package main

import "fmt"

func main() {
	n := 5
	var a [5]int
	var c int
	for (i := 0; i < n; i++) {
		scanln(&c)
		a[i] = c
	}

	start := 0
	end := n - 1
	key := 8

	for (start <= end) {
		m := start + (end-start)/2

		if (a[m] == key) {
			println("found")
		}

		if (a[m] < key) {
			start = m + 1
		} else {
			end = m - 1
		}
	}
}